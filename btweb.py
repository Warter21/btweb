#!/usr/bin/env python3
from flask import Flask, render_template, redirect, jsonify, request
import subprocess
import re

app = Flask(__name__)

def bt(cmd):
    """Run bluetoothctl in batch mode."""
    try:
        out = subprocess.check_output(
            ["bluetoothctl", "--"] + cmd.split(),
            stderr=subprocess.STDOUT
        )
        return out.decode(errors="ignore")
    except subprocess.CalledProcessError as e:
        return e.output.decode(errors="ignore")

def get_device_info(mac):
    out = bt(f"info {mac}")
    info = {
        "connected": "Connected: yes" in out,
        "paired": "Paired: yes" in out,
        "trusted": "Trusted: yes" in out,
        "rssi": None,
        "device_type": "other",
        "a2dp": False,
        "battery": None,
    }

    # RSSI
    m = re.search(r"RSSI:\s*(-?\d+)", out)
    if m:
        info["rssi"] = int(m.group(1))

    # Device type
    if "Icon: audio-headset" in out or "Icon: audio-card" in out:
        info["device_type"] = "headset"
    elif "Icon: audio-speakers" in out:
        info["device_type"] = "speaker"
    elif "Icon: phone" in out:
        info["device_type"] = "phone"

    # A2DP
    if "UUID: Audio Sink" in out or "a2dp" in out.lower():
        info["a2dp"] = True

    # Battery from PulseAudio
    info["battery"] = get_battery_from_pulseaudio(mac)

    return info

def list_devices():
    out = bt("devices")
    devices = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "Device":
            mac = parts[1]
            name = " ".join(parts[2:])
            devices.append({"mac": mac, "name": name})
    return devices

def is_scanning():
    out = bt("show")
    return "Discovering: yes" in out

def mac_to_sink_name(mac):
    """bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink"""
    base = mac.replace(":", "_")
    return f"bluez_sink.{base}.a2dp_sink"

def get_sink_volume(mac):
    """Return volume (0-100) for the BT sink if found, else None."""
    sink_name = mac_to_sink_name(mac)
    try:
        out = subprocess.check_output(
            ["pactl", "list", "sinks"],
            stderr=subprocess.STDOUT
        ).decode(errors="ignore")
    except subprocess.CalledProcessError:
        return None

    blocks = out.split("Sink #")
    for b in blocks:
        if sink_name in b:
            m = re.search(r"Volume:.*?(\d+)%", b)
            if m:
                return int(m.group(1))
    return None

def set_sink_volume(mac, volume):
    sink_name = mac_to_sink_name(mac)
    try:
        subprocess.check_call(
            ["pactl", "set-sink-volume", sink_name, f"{volume}%"],
            stderr=subprocess.STDOUT
        )
        return True
    except subprocess.CalledProcessError:
        return False

def get_battery_from_pulseaudio(mac):
    try:
        out = subprocess.check_output(
            ["pactl", "list", "cards"],
            stderr=subprocess.STDOUT
        ).decode(errors="ignore")
    except Exception:
        return None

    blocks = out.split("Card #")
    for b in blocks:
        # Match by device.string = "MAC"
        if f'device.string = "{mac}"'.lower() in b.lower():

            # bluetooth.battery = "70%"
            m = re.search(r'bluetooth\.battery\s*=\s*"?(\d+)%', b, re.I)
            if m:
                return int(m.group(1))

            # battery.level = 70
            m = re.search(r"battery\.level\s*=\s*(\d+)", b, re.I)
            if m:
                return int(m.group(1))

            # Battery Level: 70%
            m = re.search(r"Battery Level:\s*(\d+)%", b, re.I)
            if m:
                return int(m.group(1))

    return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/devices")
def api_devices():
    devices = list_devices()
    enriched = []
    for d in devices:
        info = get_device_info(d["mac"])
        vol = get_sink_volume(d["mac"]) if info["connected"] else None
        enriched.append({
            "mac": d["mac"],
            "name": d["name"],
            "connected": info["connected"],
            "paired": info["paired"],
            "trusted": info["trusted"],
            "rssi": info["rssi"],
            "device_type": info["device_type"],
            "a2dp": info["a2dp"],
            "volume": vol,
            "battery": info["battery"],
        })
    return jsonify(enriched)

@app.route("/api/scan_status")
def api_scan_status():
    return jsonify({"scanning": is_scanning()})

@app.route("/api/set_volume/<mac>", methods=["POST"])
def api_set_volume(mac):
    data = request.get_json(silent=True) or {}
    vol = data.get("volume")
    try:
        vol_int = max(0, min(100, int(vol)))
    except (TypeError, ValueError):
        return jsonify({"ok": False}), 400

    ok = set_sink_volume(mac, vol_int)
    return jsonify({"ok": ok})

@app.route("/connect/<mac>")
def connect(mac):
    bt(f"connect {mac}")
    return redirect("/")

@app.route("/disconnect/<mac>")
def disconnect(mac):
    bt(f"disconnect {mac}")
    return redirect("/")

@app.route("/pair/<mac>")
def pair(mac):
    bt(f"pair {mac}")
    return redirect("/")

@app.route("/remove/<mac>")
def remove(mac):
    bt(f"remove {mac}")
    return redirect("/")

@app.route("/trust/<mac>")
def trust(mac):
    bt(f"trust {mac}")
    return redirect("/")

@app.route("/untrust/<mac>")
def untrust(mac):
    bt(f"untrust {mac}")
    return redirect("/")

@app.route("/scan/on")
def scan_on():
    subprocess.Popen([
        "timeout", "20",
        "bluetoothctl", "scan", "on"
    ])
    return redirect("/")

@app.route("/api/debug/battery/<mac>")
def api_debug_battery(mac):
    value = get_battery_from_pulseaudio(mac)
    return {"mac": mac, "battery": value}

@app.route("/restart/squeezelite")
def restart_squeezelite():
    subprocess.call(["systemctl", "--user", "restart", "squeezelite"])
    return redirect("/")

@app.route("/restart/pulseaudio")
def restart_pulseaudio():
    subprocess.call(["systemctl", "--user", "restart", "pulseaudio"])
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1234)

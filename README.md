# Bluetooth Web UI

A lightweight, modern, browser‑based interface for managing Bluetooth audio devices on Linux.
This project provides a clean web dashboard with real‑time updates, device controls, audio volume management, and service utilities — all without requiring a desktop environment.

Designed for headless systems such as embedded Linux boards, home servers, media players, and DIY audio setups.

---

## ✨ Features

### 🔵 Bluetooth Device Management
- Scan for nearby devices (20 second timed scan)
- Connect / Disconnect
- Pair / Remove
- Trust / Untrust
- Live RSSI (signal strength)
- Battery information
- Device type detection (speaker, headset, phone, etc.)
- A2DP profile detection

### 🔊 Audio Controls
- Real‑time volume slider for Bluetooth A2DP sinks (PulseAudio)
- Automatic detection of active sinks

### ⚡ AJAX Interface
- Device list updates every 5 seconds (no full page reload)
- Scan status updates every second
- Smooth UI interactions without blocking

### 🌙 Dark Mode
- Toggle between light and dark themes
- Preference stored in browser localStorage

### 🛠 Service Utilities
- Restart Squeezelite
- Restart PulseAudio

---

## 🧩 Requirements

- Linux system with:
  - `bluez`
  - `bluetoothctl`
  - `python3`
  - `python3-flask`
  - `pactl` (PulseAudio) — optional but recommended
- A running Bluetooth adapter (`hci0`)
- Optional: Squeezelite as a user service

---

## 📦 Installation

1. Clone the repository.
2. Install dependencies: sudo apt install python3 python3-flask pulseaudio-utils bluez
3. Start the server: python3 btweb.py
4. Then open your browser: http://<your-device-ip>:1234

---

## 🖥 How It Works

Backend (Python + Flask)
- Uses bluetoothctl -- <command> for stable, non-interactive control
- Provides JSON API endpoints:
  - /api/devices
  - /api/scan_status
  - /api/set_volume/<mac>
- Runs timed scans using: timeout 20 bluetoothctl scan on
- Reads PulseAudio sink volume and adjusts it via pactl

Frontend (HTML + JS)
- Fetches device list every 5 seconds
- Fetches scan status every second
- Updates UI dynamically without reloading
- Provides:
  - Connect/Disconnect buttons
  - Pair/Remove
  - Trust/Untrust
  - Volume slider
  - Device icons
  - Dark mode toggle

---

## 📡 API Endpoints

<img width="930" height="802" alt="image" src="https://github.com/user-attachments/assets/dddc5267-b350-419f-92dd-c1f8b72cab9f" />

---

## 📝 License

MIT License (or whichever you prefer)

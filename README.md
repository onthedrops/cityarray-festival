# CITYARRAY Festival Edition

**Portable Event Signage with Raspberry Pi**

A complete festival communication system featuring an operator dashboard and intelligent sign clients that display multilingual emergency alerts, event information, and crowd guidance.

![Status](https://img.shields.io/badge/status-active%20development-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10+-blue)

## ✨ Features

- 🖥️ **Real-time Dashboard** - Monitor and control your entire sign fleet
- 🌍 **Multilingual TTS** - 10 languages with natural voice synthesis
- 📡 **Cellular Failover** - Signs stay connected even when WiFi fails
- 🤖 **Local AI** - Ollama-powered responses without cloud dependency
- 🎨 **Priority Colors** - Red/Amber/Green visual hierarchy
- 📝 **Template Library** - 39 pre-built multilingual messages
- 🔌 **Offline Mode** - Signs operate autonomously when disconnected

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         OPERATOR                                  │
│                            │                                      │
│                            ▼                                      │
│    ┌─────────────────────────────────────────────────────────┐   │
│    │                    DASHBOARD                             │   │
│    │    ┌──────────┬──────────┬──────────┬──────────┐        │   │
│    │    │ Overview │  Signs   │ Messages │ Templates │        │   │
│    │    └──────────┴──────────┴──────────┴──────────┘        │   │
│    │              FastAPI + HTMX + WebSocket                  │   │
│    └─────────────────────────────────────────────────────────┘   │
│                            │                                      │
│              WebSocket (real-time sync)                          │
│                            │                                      │
│    ┌───────────────────────┼───────────────────────┐             │
│    │                       │                       │             │
│    ▼                       ▼                       ▼             │
│ ┌──────┐               ┌──────┐               ┌──────┐          │
│ │ Pi 5 │               │ Pi 5 │               │ Pi 5 │          │
│ │Sign 1│               │Sign 2│               │Sign 3│          │
│ └──┬───┘               └──┬───┘               └──┬───┘          │
│    │                      │                      │               │
│ ┌──┴───┐               ┌──┴───┐               ┌──┴───┐          │
│ │LED   │               │LED   │               │LED   │          │
│ │Panel │               │Panel │               │Panel │          │
│ └──────┘               └──────┘               └──────┘          │
└──────────────────────────────────────────────────────────────────┘
```

## 📦 Repository Structure

```
cityarray-festival/
├── dashboard/              # Operator web dashboard
│   ├── app.py              # FastAPI application
│   ├── models.py           # SQLAlchemy models
│   ├── templates/          # Jinja2 HTML templates
│   ├── static/             # CSS, JS assets
│   └── requirements.txt
├── sign-client/            # Raspberry Pi sign software
│   └── sign_client_v2.py   # Client with cellular failover
├── backend/                # Shared backend utilities
├── docs/                   # Documentation
├── seed_templates.py       # Template seeding script
└── templates_data.json     # 39 multilingual templates
```

## 🚀 Quick Start

### Dashboard Setup (Mac/Linux)

```bash
# Clone the repo
git clone https://github.com/onthedrops/cityarray-festival.git
cd cityarray-festival/dashboard

# Install dependencies
pip3 install -r requirements.txt

# Seed templates
python3 seed_templates.py

# Run dashboard
python3 app.py
```

Open http://localhost:8000

### Sign Client Setup (Raspberry Pi 5)

```bash
# On the Pi
mkdir -p ~/cityarray/sign-client
cd ~/cityarray/sign-client

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install websockets aiohttp requests

# Copy sign_client_v2.py from repo
# Edit configuration (dashboard IP, sign name, zone)

# Run
python sign_client_v2.py
```

## 🖥️ Dashboard Pages

| Route | Purpose |
|-------|---------|
| `/` | Dashboard overview with stats and recent activity |
| `/signs` | Sign fleet management with health monitoring |
| `/messages` | Message history with delivery status |
| `/templates` | Template library (39 pre-built) |
| `/submissions` | Community submission moderation queue |
| `/simulator` | Virtual sign testing (no hardware needed) |

## 🛠️ Hardware Setup

### Per-Sign Components

| Component | Model | Purpose |
|-----------|-------|---------|
| Computer | Raspberry Pi 5 (4GB) | Main controller |
| Display | Waveshare 64x32 RGB LED | Visual output |
| Display Driver | Adafruit Matrix Portal S3 | WiFi LED control |
| Camera | Raspberry Pi AI Camera | Crowd detection |
| Audio | USB Speaker/Mic | TTS announcements |
| AI Accelerator | AI HAT+ 16 TOPS (Hailo-8L) | Local inference |
| Network | Cellular HAT (optional) | Failover connectivity |
| Power | 5V 4A supply (LED panel) | Display power |

### Wiring Diagram

```
                    ┌─────────────────┐
                    │  Raspberry Pi 5 │
                    │                 │
        USB-C ──────┤ Power           │
        Ethernet ───┤ Network         │
        USB ────────┤ Speaker/Mic     │
        CSI ────────┤ AI Camera       │
        GPIO ───────┤ AI HAT+         │
                    └─────────────────┘
                            │
                       WiFi │ HTTP
                            ▼
                    ┌─────────────────┐
                    │ Matrix Portal   │──── 5V Power
                    │      S3         │      Supply
                    └────────┬────────┘
                             │ HUB75
                             ▼
                    ┌─────────────────┐
                    │  64x32 RGB LED  │
                    │     Matrix      │
                    └─────────────────┘
```

## 🌍 Supported Languages

| Language | Engine | Voice Model |
|----------|--------|-------------|
| English | Piper | en_US-lessac-medium |
| Spanish | Piper | es_ES-davefx-medium |
| Chinese | Piper | zh_CN-huayan-medium |
| Vietnamese | Piper | vi_VN-vivos-x_low |
| French | Piper | fr_FR-siwis-medium |
| Arabic | Piper | ar_JO-kareem-medium |
| Portuguese | Piper | pt_BR-faber-medium |
| Korean | Edge-TTS | ko-KR-SunHiNeural |
| Japanese | Edge-TTS | ja-JP-NanamiNeural |
| Hindi | Edge-TTS | hi-IN-SwaraNeural |

## 📡 Network Modes

### Normal Mode
```
Sign ◄──WebSocket──► Dashboard ◄──► Operator
         (WiFi)
```

### Cellular Failover
```
Sign ◄──WebSocket──► Dashboard ◄──► Operator
        (4G/LTE)
```

### Offline Mode
```
Sign operates autonomously with:
├── Cached templates
├── Local emergency commands
├── Message queue (syncs when reconnected)
└── Voice agent (Ollama)
```

**Offline Commands:**
- `evacuate` - Show evacuation message
- `shelter` - Shelter in place
- `medical` - Medical emergency
- `weather` - Severe weather alert
- `clear` - Clear display
- `reconnect` - Attempt reconnection

## 🎨 Message Priority System

| Priority | Color | Use Case |
|----------|-------|----------|
| 90-100 | 🔴 Red | Evacuation, life safety |
| 70-89 | 🟠 Amber | Weather, medical, caution |
| 0-69 | 🟢 Green | Information, schedules |

## 📋 Pre-built Templates

The system includes 39 multilingual templates across categories:

- **Emergency**: Evacuation, shelter, medical
- **Weather**: Severe weather, lightning, heat
- **Crowd**: Capacity, alternate routes
- **Event**: Schedule changes, delays
- **Safety**: Lost child, suspicious activity
- **Facilities**: Restrooms, water, first aid

## 🧪 Testing Without Hardware

Use the built-in simulator:

1. Start dashboard: `python3 app.py`
2. Go to http://localhost:8000/simulator
3. Create virtual signs
4. Send messages from dashboard
5. Watch virtual signs respond

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [cityarray-sdk](https://github.com/onthedrops/cityarray-sdk) - Core SDK and documentation
- [Piper TTS](https://github.com/rhasspy/piper) - Local text-to-speech
- [Ollama](https://ollama.ai) - Local LLM inference

## 📬 Contact

- **GitHub**: [@onthedrops](https://github.com/onthedrops)

---

Built with ❤️ for safer festivals and events.

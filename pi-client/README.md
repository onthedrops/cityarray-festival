# CITYARRAY Pi Client

Scripts for Raspberry Pi 5 to control LED sign.

## Setup on Pi
```bash
cd ~/cityarray
python3 -m venv sign-client/venv
source sign-client/venv/bin/activate
pip install flask requests pytz websockets
```

## Dependencies (install separately)
- Ollama with llama3.2:3b
- Piper TTS
- Whisper.cpp (optional, for voice)

## Files
- `sign_client.py` - Connects dashboard to physical sign (bilingual)
- `sign_formatter.py` - Translation dictionary + formatting
- `cityarray_system.py` - Full system with Flask API
- `cityarray_proactive.py` - Standalone slide cycling
- `cityarray_console.py` - Terminal message input

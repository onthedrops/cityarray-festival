# CITYARRAY Sign Client

Runs on Raspberry Pi to connect to the dashboard.

## Features
- Cellular failover
- Offline mode with cached templates
- Local emergency operation

## Setup on Pi
```bash
mkdir -p ~/cityarray/sign-client
cd ~/cityarray/sign-client
python3 -m venv venv
source venv/bin/activate
pip install websockets aiohttp requests
python sign_client_v2.py
```

## Configuration

Edit `sign_client_v2.py` and update:
- `dashboard_host` - Your dashboard IP
- `sign_name` - Name for this sign
- `sign_zone` - Zone assignment

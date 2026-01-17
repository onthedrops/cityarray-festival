# CITYARRAY Festival Edition - Backend API

FastAPI backend with SQLite database and WebSocket support for real-time updates.

## Quick Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your settings

# Run the server
python app.py
# Or with auto-reload:
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Architecture

```
backend/
├── app.py              # FastAPI application, routes, WebSocket handlers
├── models.py           # SQLAlchemy database models
├── schemas.py          # Pydantic validation schemas
├── database.py         # Database connection and initialization
├── websocket_manager.py # Real-time WebSocket management
├── requirements.txt    # Python dependencies
└── .env.example        # Environment variables template
```

## WebSocket Endpoints

### Dashboard Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/dashboard');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Update:', data.type, data);
};

// Request all signs
ws.send(JSON.stringify({ type: 'get_all_signs' }));
```

### Sign Connection
```python
import websockets
import json

async def connect_sign(sign_id):
    uri = f"ws://localhost:8000/ws/sign/{sign_id}"
    async with websockets.connect(uri) as ws:
        # Send heartbeat
        await ws.send(json.dumps({
            "type": "heartbeat",
            "data": {
                "battery": 85,
                "signal_strength": -65,
                "crowd_density": "medium",
                "crowd_count": 42
            }
        }))
        
        # Listen for messages
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "override":
                # Handle override message
                pass
```

## Message Types

### Server → Dashboard
| Type | Description |
|------|-------------|
| `sign_update` | Sign status changed |
| `sign_connected` | New sign connected |
| `sign_disconnected` | Sign disconnected |
| `sign_offline` | Sign marked offline (timeout) |
| `new_submission` | Attendee submission received |
| `submission_approved` | Submission approved |
| `override_activated` | Override sent |
| `override_cancelled` | Override cancelled |
| `message_sent` | New message queued |
| `message_ack` | Sign acknowledged message |

### Server → Sign
| Type | Description |
|------|-------------|
| `new_message` | Display this message |
| `override` | Immediate override message |
| `override_cancelled` | Resume normal operation |
| `ping` | Connection check |
| `request_status` | Send status immediately |

### Sign → Server
| Type | Description |
|------|-------------|
| `heartbeat` | Periodic status update |
| `metrics` | Crowd/impression data |
| `ack` | Message acknowledged |

## Database

SQLite by default (file: `cityarray.db`). To switch to PostgreSQL:

```python
# In database.py, change:
DATABASE_URL = "postgresql://user:password@localhost/cityarray"
```

## Default Templates

On first run, the system creates 17 default message templates:
- Emergency (evacuation, shelter, medical)
- Weather (current, lightning, heat)
- Schedule (now playing, starting soon)
- Traffic/Parking
- Wayfinding (restrooms, first aid)
- Crowd alerts
- Attendee (lost, found, meetup)
- Sponsor

## Environment Variables

```bash
# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./cityarray.db

# Twilio (for SMS/voice)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567

# Weather API
OPENWEATHER_API_KEY=your_api_key

# Security (production)
SECRET_KEY=your_secret_key
```

## Testing

```bash
# Run tests
pytest

# Test WebSocket connection
python -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8000/ws/dashboard') as ws:
        print(await ws.recv())

asyncio.run(test())
"
```

## Production Deployment

For production:
1. Switch to PostgreSQL
2. Use proper authentication (JWT)
3. Set up HTTPS/WSS
4. Use gunicorn with uvicorn workers
5. Set up Redis for session storage

```bash
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

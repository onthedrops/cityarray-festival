# CITYARRAY Festival Dashboard

HTMX + Jinja2 operator dashboard for the Festival Edition signage system.

## Quick Start

```bash
cd festival-dashboard
pip install -r requirements.txt
python app.py
```

Open http://localhost:8000 in your browser.

## Features

### Dashboard (`/`)
- Real-time sign fleet status
- Quick actions (send override, send message)
- Recent messages list
- System stats (online/offline signs, pending submissions)

### Signs (`/signs`)
- Sign fleet table with live metrics
- Battery, signal, crowd count, density
- Send message to individual signs

### Messages (`/messages`)
- Message history
- Create new messages from templates
- Target specific signs or all

### Templates (`/templates`)
- Pre-built message templates (17 default)
- Categories: emergency, wayfinding, crowd, weather, etc.
- Create/edit custom templates

### Submissions (`/submissions`)
- Attendee message moderation queue
- Approve/reject with reasons
- Filter by status

### Simulator (`/simulator`) 🧪
- Create simulated signs without hardware
- Adjust metrics (battery, crowd density)
- Quick-create festival/concert/sports fleets
- See messages received in real-time

## Architecture

```
┌─────────────────────────────────────────────┐
│              Browser (Dashboard)            │
│  HTMX + WebSocket (/ws/dashboard)           │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│           FastAPI Server (app.py)           │
│  ├── Dashboard Routes (Jinja2)              │
│  ├── API Endpoints (/api/*)                 │
│  └── WebSocket Manager                      │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│            SQLite Database                   │
│  Signs, Templates, Messages, Submissions    │
└─────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Sign Clients (or Simulators)        │
│  WebSocket (/ws/sign/{id})                  │
└─────────────────────────────────────────────┘
```

## Real-Time Updates

The dashboard uses HTMX's WebSocket extension to receive live updates:

- Sign status changes (online/offline)
- Sign metrics (battery, crowd)
- New messages sent
- Override activations
- New submissions

## Files

```
festival-dashboard/
├── app.py              # Main FastAPI application
├── database.py         # SQLite/SQLAlchemy config
├── models.py           # ORM models
├── schemas.py          # Pydantic schemas
├── websocket_manager.py # WebSocket handling
├── requirements.txt
└── templates/
    ├── base.html       # Base layout (HTMX, CSS, WebSocket)
    ├── dashboard.html  # Main dashboard
    ├── signs.html      # Sign fleet management
    ├── messages.html   # Message history
    ├── templates.html  # Template management
    ├── submissions.html # Moderation queue
    └── simulator.html  # Sign simulator
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/signs` | List all signs |
| POST | `/api/signs` | Register new sign |
| GET | `/api/templates` | List templates |
| POST | `/api/templates` | Create template |
| POST | `/api/messages` | Send message |
| POST | `/api/override` | Send override |
| GET | `/api/submissions` | List submissions |
| POST | `/api/submissions/{id}/approve` | Approve |
| POST | `/api/submissions/{id}/reject` | Reject |
| GET | `/health` | Health check |
| GET | `/api/status` | System status |

## Testing Without Hardware

1. Open http://localhost:8000/simulator
2. Click "Create Festival Fleet (5 signs)"
3. Watch signs connect in real-time
4. Go to Dashboard to see fleet status
5. Send a message - watch it appear on simulators
6. Send an override - all simulators turn red

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Frontend:** HTMX + Jinja2 (no React, no Node.js)
- **Real-time:** WebSockets (native HTMX extension)
- **Styling:** Custom CSS (~300 lines, no framework)

# CITYARRAY Festival Edition — System Architecture

**Version:** 1.0  
**Date:** January 2026  
**Status:** Sprint Planning

---

## System Overview

CITYARRAY Festival Edition is a portable, AI-powered event signage system that provides real-time information, emergency communications, and community engagement for festivals, concerts, and large gatherings.

### Core Capabilities

| Category | Features |
|----------|----------|
| **AI Vision** | YOLOv8 crowd detection on Hailo-8L, density estimation |
| **Data Feeds** | Traffic/parking, weather (current + alerts), event schedule |
| **Attendee Input** | SMS via Twilio, QR → web form, moderation queue |
| **Display Control** | Template scheduler, instant override, zone-based messaging |
| **Audio** | TTS announcements in 5 languages, crowd noise estimation |
| **Monitoring** | Map view, sign status, live display preview |
| **Operator Alerts** | Twilio SMS/voice for system issues + emergencies |
| **Analytics** | Impressions, crowd density history, message audit log |

### Hardware per Sign Unit

- Raspberry Pi 5 (8GB)
- Hailo-8L M.2 (13 TOPS)
- AI Camera
- MEMS Microphone (crowd noise)
- Speaker + Class D Amplifier
- Display (E-paper 13.3" or LED 24")
- LiFePO4 Battery (500Wh, 8-16hr runtime)
- 4G LTE Modem (Twilio SIM)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLOUD / BACKEND                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │   Twilio     │  │  Weather     │  │  Traffic     │               │
│  │  SMS/Voice   │  │    API       │  │    API       │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                 │                        │
│         ▼                 ▼                 ▼                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    FESTIVAL BACKEND                          │    │
│  │                  (Flask / FastAPI)                           │    │
│  │                                                              │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │    │
│  │  │ Message │ │Scheduler│ │ Sign    │ │Analytics│            │    │
│  │  │ Queue   │ │ Engine  │ │ Manager │ │ Engine  │            │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘            │    │
│  │                                                              │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │    │
│  │  │Moderat- │ │  User   │ │  Event  │ │  Alert  │            │    │
│  │  │  ion    │ │  Roles  │ │ Config  │ │ Service │            │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘            │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                     DATABASE                                 │    │
│  │            (PostgreSQL / SQLite for MVP)                     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │      4G LTE / WiFi    │
                    ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Sign 1    │ │   Sign 2    │ │   Sign N    │
│  (Zone A)   │ │  (Zone B)   │ │  (Zone C)   │
├─────────────┤ ├─────────────┤ ├─────────────┤
│ Pi 5        │ │ Pi 5        │ │ Pi 5        │
│ Hailo-8L    │ │ Hailo-8L    │ │ Hailo-8L    │
│ Camera      │ │ Camera      │ │ Camera      │
│ Mic/Speaker │ │ Mic/Speaker │ │ Mic/Speaker │
│ Display     │ │ Display     │ │ Display     │
│ demo_full.py│ │ demo_full.py│ │ demo_full.py│
└─────────────┘ └─────────────┘ └─────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  OPERATOR        │  │  ATTENDEE        │  │  ATTENDEE        │   │
│  │  DASHBOARD       │  │  WEB FORM        │  │  SMS             │   │
│  │  (Web UI)        │  │  (via QR code)   │  │  (via Twilio)    │   │
│  │                  │  │                  │  │                  │   │
│  │ - Map view       │  │ - Lost & Found   │  │ "LOST blue       │   │
│  │ - Sign status    │  │ - Meetup request │  │  backpack near   │   │
│  │ - Scheduler      │  │ - Report issue   │  │  Stage A"        │   │
│  │ - Override       │  │ - Feedback       │  │                  │   │
│  │ - Moderation     │  │                  │  │  → 555-EVENT     │   │
│  │ - Analytics      │  │                  │  │                  │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. Data Feeds

### 1.1 Weather Integration

**Source:** OpenWeatherMap API or National Weather Service API (free)

**Data Collected:**
- Current conditions (temp, humidity, wind, description)
- Severe weather alerts (lightning, heat advisory, storms)
- Forecast (hourly for event duration)

**Auto-Triggers:**
| Condition | Action |
|-----------|--------|
| Lightning within 10 miles | Auto-display: "SEEK SHELTER - Lightning detected" |
| Heat index > 105°F | Auto-display: "HEAT ADVISORY - Hydration stations at..." |
| Rain imminent | Auto-display: "Rain expected in 30 min" |
| Severe thunderstorm warning | Emergency override all signs |

**Display Format:**
```
┌─────────────────────────────┐
│ ☀️ 78°F  Partly Cloudy      │
│ Wind: 8 mph SW              │
│ Sunset: 7:45 PM             │
└─────────────────────────────┘
```

### 1.2 Traffic/Parking Integration

**Source:** Manual input or Google Maps API / Waze API

**Data Tracked:**
- Parking lot status: Open / Filling / Full
- Road conditions: Clear / Slow / Congested / Closed
- Suggested routes

**Display Format:**
```
┌─────────────────────────────┐
│ PARKING STATUS              │
│ Lot A: FULL                 │
│ Lot B: OPEN (45% capacity)  │
│ Lot C: FILLING              │
│                             │
│ Exit via Gate 3 recommended │
└─────────────────────────────┘
```

### 1.3 Event Schedule Integration

**Source:** CSV upload or API from ticketing platform

**Features:**
- Import artist/act schedule with stage assignments
- Auto-display "Next up" countdowns
- Set time reminders

**Display Format:**
```
┌─────────────────────────────┐
│ MAIN STAGE                  │
│ NOW: The Headliners         │
│ NEXT: DJ Opener (8:30 PM)   │
│                             │
│ STAGE B in 15 minutes:      │
│ Local Band                  │
└─────────────────────────────┘
```

---

## 2. Attendee Input System

### 2.1 SMS Input (Twilio)

**Twilio Number:** Dedicated short code or 10-digit number per event

**Message Format:**
```
Text to: 555-EVENT (555-383-68)

LOST [description]     → Lost & found submission
FOUND [description]    → Found item report
MEETUP [location]      → Meetup request
REPORT [issue]         → Report problem
HELP                   → Get menu of options
```

**Processing Flow:**
```
Attendee SMS → Twilio → Backend Webhook → Moderation Queue → Approved → Display
```

**Auto-Response:**
```
"Thanks! Your message is pending review. 
If approved, it will display on signs near [zone].
Reply STOP to opt out."
```

### 2.2 QR Code → Web Form

**QR Code on Each Sign:**
- Links to: `https://event.cityarray.com/submit?sign=A1`
- Pre-fills zone based on sign location

**Web Form Categories:**
| Category | Fields |
|----------|--------|
| Lost Item | Description, last seen location, contact method |
| Found Item | Description, current location, contact method |
| Meetup Request | Group name, meeting point, time |
| Report Issue | Issue type, location, description, photo upload (optional) |
| Feedback | Message, rating (optional) |

### 2.3 Moderation Queue

**Moderation UI Features:**
- View pending submissions (newest first)
- One-click approve / reject / edit
- Auto-reject filters (profanity, spam patterns)
- Assign to zone for display
- Set display duration
- Preview before publish

**Moderation Roles:**
| Role | Can Approve |
|------|-------------|
| Event Manager | All categories |
| Zone Lead | Their zone only |
| Staff | Lost & found only |

---

## 3. Display Control

### 3.1 Template System

**Template Categories:**

| Category | Examples |
|----------|----------|
| Emergency | Evacuation, shelter-in-place, medical emergency, security alert |
| Weather | Current conditions, severe weather, heat advisory |
| Traffic/Parking | Lot status, road conditions, exit guidance |
| Schedule | Set times, countdowns, delays, cancellations |
| Wayfinding | Restrooms, first aid, water stations, ATMs |
| Lost & Found | Attendee submissions (moderated) |
| Sponsor | Rotating sponsor messages |
| Custom | Free-form operator messages |

**Template Variables:**
```
{{ event_name }}
{{ current_time }}
{{ weather_temp }}
{{ weather_condition }}
{{ lot_a_status }}
{{ next_artist }}
{{ next_stage }}
{{ countdown_timer }}
{{ zone_name }}
```

**Example Template:**
```
Template: "schedule_next_up"
Content:
┌─────────────────────────────┐
│ {{ stage_name }}            │
│ NOW: {{ current_artist }}   │
│ NEXT: {{ next_artist }}     │
│       {{ next_time }}       │
│                             │
│ {{ weather_temp }}°F {{ weather_icon }} │
└─────────────────────────────┘
```

### 3.2 Scheduler

**Scheduler Features:**
- Drag-and-drop timeline per zone
- Recurring patterns (e.g., sponsor every 10 min)
- Priority levels (Emergency > Weather > Schedule > Sponsor)
- Blackout periods (no sponsors during headliner)
- Duration per message

**Schedule Entry:**
```json
{
  "template": "sponsor_acme",
  "zones": ["A", "B", "C"],
  "start_time": "18:00",
  "end_time": "23:00",
  "frequency_minutes": 10,
  "duration_seconds": 30,
  "priority": 1,
  "enabled": true
}
```

### 3.3 Override System

**Override Modes:**

| Mode | Behavior |
|------|----------|
| Insert | Display override message, then resume schedule |
| Replace | Display override message, pause schedule until cleared |
| Emergency | All signs immediately, audio announcement, operator alert |

**Override Flow:**
1. Operator selects zone(s) or "All Signs"
2. Selects template or types custom message
3. Selects mode (Insert / Replace / Emergency)
4. Confirms → Immediate push to signs
5. Signs acknowledge receipt
6. Dashboard shows override active

---

## 4. Monitoring Dashboard

### 4.1 Map View

**Features:**
- Upload venue map image (PNG/JPG)
- Drag-and-drop sign placement on map
- Click sign icon → see status popup
- Color coding:
  - 🟢 Green: Online, healthy
  - 🟡 Yellow: Warning (low battery, weak signal)
  - 🔴 Red: Offline or error
  - 🔵 Blue: Override active

**Sign Popup:**
```
┌─────────────────────────────┐
│ Sign A1 - Main Entrance     │
│ Status: 🟢 Online           │
│ Battery: 78%                │
│ Signal: -65 dBm (Good)      │
│ Crowd: MEDIUM (47 people)   │
│ Displaying: schedule_next   │
│ Last update: 12 sec ago     │
│                             │
│ [Preview] [Override] [Logs] │
└─────────────────────────────┘
```

### 4.2 Sign Status Table

| Sign ID | Zone | Status | Battery | Signal | Crowd | Displaying | Last Seen |
|---------|------|--------|---------|--------|-------|------------|-----------|
| A1 | Main Gate | 🟢 Online | 78% | Good | Medium | schedule_next | 12s ago |
| A2 | Main Gate | 🟢 Online | 82% | Good | Low | weather | 8s ago |
| B1 | Stage B | 🟡 Warning | 23% | Fair | High | crowd_alert | 15s ago |
| C1 | Food Court | 🔴 Offline | -- | -- | -- | -- | 5 min ago |

### 4.3 Live Display Preview

- Thumbnail of what each sign is currently showing
- Click to enlarge
- Auto-refresh every 10 seconds
- Historical view (what was shown when)

---

## 5. Operator Alerts (Twilio)

### 5.1 Alert Types

| Alert | Channel | Recipients |
|-------|---------|------------|
| Sign offline | SMS | Zone Lead, Event Manager |
| Battery < 20% | SMS | Zone Lead |
| Battery < 10% | SMS + Voice Call | Event Manager |
| Crowd density critical | SMS | Zone Lead, Security |
| Connectivity lost | SMS | Zone Lead |
| Emergency override activated | SMS + Voice | All operators |
| Weather alert triggered | SMS | Event Manager |
| Attendee message flagged | SMS | Moderator on duty |

### 5.2 Alert Configuration

```json
{
  "alert_type": "battery_low",
  "threshold": 20,
  "channels": ["sms"],
  "recipients": ["zone_lead"],
  "cooldown_minutes": 30,
  "message": "Sign {{ sign_id }} battery at {{ battery }}%. Needs attention."
}
```

### 5.3 Voice Call Script

For critical alerts (battery critical, sign offline cluster, emergency):

```
"This is CITYARRAY Alert System. 
Sign {{ sign_id }} at {{ zone_name }} is {{ status }}.
Battery level is {{ battery }} percent.
Press 1 to acknowledge. Press 2 to escalate."
```

---

## 6. Analytics

### 6.1 Metrics Tracked

| Metric | Description |
|--------|-------------|
| Impressions | Estimated viewers per message (camera-based) |
| Crowd density | People count per zone over time |
| Message display time | How long each message was shown |
| System uptime | Per sign and overall |
| Attendee submissions | Count by category |
| Moderation stats | Approved / rejected / avg response time |

### 6.2 Reports

**Real-time Dashboard:**
- Current crowd by zone
- Messages displayed in last hour
- System health overview

**Post-Event Report:**
- Total impressions by message type
- Peak crowd times and locations
- Sponsor message performance (impressions, CPM)
- Incident log (emergencies, overrides)
- Attendee engagement (submissions, categories)

### 6.3 Audit Log

Every action logged:
```json
{
  "timestamp": "2026-01-15T18:45:32Z",
  "user": "jane@eventco.com",
  "role": "Event Manager",
  "action": "override_sent",
  "target": ["A1", "A2", "B1"],
  "message": "Stage A delayed 15 minutes",
  "mode": "insert"
}
```

---

## 7. User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **Admin** | All access, user management, billing, multi-event |
| **Event Manager** | Full event control, all zones, all features |
| **Zone Lead** | Override/schedule for assigned zones, view all, moderation |
| **Staff** | View-only dashboard, approve lost & found only |
| **Sponsor** | View sponsor analytics only |

**Role Hierarchy for Override:**
```
Admin > Event Manager > Zone Lead > Staff

Higher role can override lower role's actions.
Zone Lead override in Zone A does not affect Zone B.
Event Manager override affects all zones.
```

---

## 8. Multi-Event Profiles

### Event Configuration

Save/load complete event setup:

```json
{
  "event_name": "Summer Music Festival 2026",
  "venue_map": "uploads/summer_fest_map.png",
  "signs": [
    {"id": "A1", "name": "Main Gate", "zone": "A", "x": 150, "y": 200},
    {"id": "A2", "name": "Main Gate South", "zone": "A", "x": 150, "y": 250}
  ],
  "zones": [
    {"id": "A", "name": "Main Gate", "color": "#FF5733"},
    {"id": "B", "name": "Stage Area", "color": "#33FF57"}
  ],
  "schedule_templates": [...],
  "alert_config": [...],
  "twilio_number": "+15551234567",
  "weather_location": "33.9425,-118.4081",
  "created_at": "2026-01-10T10:00:00Z"
}
```

**Reuse for Similar Events:**
- "Copy from previous event"
- Adjust sign positions for new venue
- Keep templates and schedules

---

## 9. Technical Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL (production) / SQLite (MVP/testing)
- **Task Queue:** Celery + Redis (for scheduled tasks, alerts)
- **Real-time:** WebSockets (sign status, live preview)

### Frontend (Operator Dashboard)
- **Framework:** React + TypeScript
- **UI Library:** Tailwind CSS + shadcn/ui
- **Maps:** Leaflet.js or custom image mapping
- **Charts:** Recharts

### Attendee Web Form
- **Framework:** Simple HTML/CSS/JS or React
- **Mobile-first responsive design

### Sign Software (on Pi 5)
- **Base:** Existing demo_full.py
- **Additions:** 
  - Backend sync client
  - Local message queue (offline mode)
  - Status reporter
  - Remote command handler

### External Services
- **Twilio:** SMS, Voice, phone numbers
- **Weather:** OpenWeatherMap or NWS API
- **Traffic:** Manual input or Google Maps API

---

## 10. Database Schema (Simplified)

```sql
-- Events
CREATE TABLE events (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    venue_map_url TEXT,
    weather_location VARCHAR(100),
    twilio_number VARCHAR(20),
    config JSONB,
    created_at TIMESTAMP
);

-- Signs
CREATE TABLE signs (
    id VARCHAR(10) PRIMARY KEY,
    event_id UUID REFERENCES events(id),
    name VARCHAR(100),
    zone_id VARCHAR(10),
    position_x INT,
    position_y INT,
    status VARCHAR(20),
    battery INT,
    signal_strength INT,
    last_seen TIMESTAMP,
    current_message_id UUID
);

-- Zones
CREATE TABLE zones (
    id VARCHAR(10),
    event_id UUID REFERENCES events(id),
    name VARCHAR(100),
    color VARCHAR(7),
    PRIMARY KEY (id, event_id)
);

-- Message Templates
CREATE TABLE templates (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id),
    category VARCHAR(50),
    name VARCHAR(100),
    content TEXT,
    variables JSONB,
    audio_enabled BOOLEAN,
    languages JSONB
);

-- Scheduled Messages
CREATE TABLE schedule (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id),
    template_id UUID REFERENCES templates(id),
    zones JSONB,
    start_time TIME,
    end_time TIME,
    frequency_minutes INT,
    duration_seconds INT,
    priority INT,
    enabled BOOLEAN
);

-- Attendee Submissions
CREATE TABLE submissions (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id),
    category VARCHAR(50),
    content TEXT,
    contact_method VARCHAR(100),
    source VARCHAR(10), -- 'sms' or 'web'
    zone_id VARCHAR(10),
    status VARCHAR(20), -- 'pending', 'approved', 'rejected'
    moderated_by UUID,
    moderated_at TIMESTAMP,
    displayed_at TIMESTAMP,
    created_at TIMESTAMP
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    name VARCHAR(100),
    role VARCHAR(50),
    zones JSONB, -- for zone-restricted roles
    phone VARCHAR(20),
    created_at TIMESTAMP
);

-- Audit Log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100),
    target JSONB,
    details JSONB,
    created_at TIMESTAMP
);

-- Analytics
CREATE TABLE impressions (
    id UUID PRIMARY KEY,
    sign_id VARCHAR(10),
    message_id UUID,
    estimated_viewers INT,
    crowd_density VARCHAR(20),
    timestamp TIMESTAMP
);
```

---

## 11. API Endpoints (Overview)

### Event Management
```
POST   /api/events                    Create event
GET    /api/events/{id}               Get event details
PUT    /api/events/{id}               Update event
POST   /api/events/{id}/map           Upload venue map
```

### Signs
```
GET    /api/events/{id}/signs         List all signs
GET    /api/signs/{sign_id}           Get sign status
POST   /api/signs/{sign_id}/override  Send override message
GET    /api/signs/{sign_id}/preview   Get current display image
```

### Templates & Scheduling
```
GET    /api/events/{id}/templates     List templates
POST   /api/events/{id}/templates     Create template
GET    /api/events/{id}/schedule      Get schedule
POST   /api/events/{id}/schedule      Add scheduled item
DELETE /api/events/{id}/schedule/{id} Remove scheduled item
```

### Moderation
```
GET    /api/events/{id}/submissions?status=pending    Get pending
POST   /api/submissions/{id}/approve                  Approve
POST   /api/submissions/{id}/reject                   Reject
```

### Twilio Webhooks
```
POST   /api/twilio/sms/incoming       Handle incoming SMS
POST   /api/twilio/voice/incoming     Handle incoming voice
POST   /api/twilio/status             Delivery status callback
```

### Sign Communication (from Pi)
```
POST   /api/signs/{id}/heartbeat      Report status
GET    /api/signs/{id}/messages       Get pending messages
POST   /api/signs/{id}/ack            Acknowledge message received
POST   /api/signs/{id}/metrics        Report crowd/impressions
```

---

## 12. Sprint Prioritization

### Sprint 1: Core Infrastructure (Week 1-2)
| Task | Priority | Effort |
|------|----------|--------|
| Backend skeleton (FastAPI + DB) | P0 | 3 days |
| Sign sync protocol (heartbeat, messages) | P0 | 2 days |
| Basic dashboard UI (sign status table) | P0 | 2 days |
| Template system (CRUD) | P0 | 1 day |
| Manual override capability | P0 | 1 day |

### Sprint 2: Scheduler & Monitoring (Week 3)
| Task | Priority | Effort |
|------|----------|--------|
| Scheduler engine | P0 | 2 days |
| Map view with sign placement | P1 | 2 days |
| Live display preview | P1 | 1 day |
| Offline queue (sign-side) | P1 | 2 days |

### Sprint 3: Twilio & Attendee Input (Week 4)
| Task | Priority | Effort |
|------|----------|--------|
| Twilio SMS inbound webhook | P0 | 1 day |
| Twilio SMS outbound alerts | P0 | 1 day |
| Twilio voice alerts | P1 | 1 day |
| Attendee web form + QR | P1 | 2 days |
| Moderation queue UI | P1 | 2 days |

### Sprint 4: Data Feeds & Polish (Week 5)
| Task | Priority | Effort |
|------|----------|--------|
| Weather integration | P1 | 1 day |
| Traffic/parking manual input | P2 | 0.5 day |
| Event schedule import | P1 | 1 day |
| User roles & permissions | P1 | 2 days |
| Analytics dashboard | P2 | 2 days |

### Sprint 5: Testing & Demo Prep (Week 6)
| Task | Priority | Effort |
|------|----------|--------|
| Multi-sign field test | P0 | 2 days |
| Pilot event dry run | P0 | 2 days |
| Documentation & training | P1 | 1 day |

---

## 13. Open Questions

1. **Hosting:** Self-hosted (your server) or cloud (AWS/GCP/Vercel)?
2. **Domain:** What URL for attendee forms? (e.g., cityarray.events)
3. **Twilio account:** Do you have one, or need to set up?
4. **First pilot event:** Any specific event in mind for testing?

---

*Document created January 2026*
*CITYARRAY Festival Edition System Architecture v1.0*

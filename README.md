
## Dashboard (New!)

HTMX-based operator dashboard for sign fleet management.
```bash
cd dashboard
pip3 install -r requirements.txt
python3 app.py
```

Open http://localhost:8000

### Features
- Real-time sign monitoring via WebSocket
- Message broadcasting to all or specific signs
- Emergency override system
- Template library (11 pre-built)
- Submission moderation
- **Sign Simulator** - test without hardware at `/simulator`

### Pages
| Route | Purpose |
|-------|---------|
| `/` | Dashboard overview |
| `/signs` | Sign fleet table |
| `/messages` | Message history |
| `/templates` | Template library |
| `/submissions` | Moderation queue |
| `/simulator` | Create virtual signs |

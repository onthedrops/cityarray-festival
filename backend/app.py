"""
CITYARRAY Festival Edition - Backend API
FastAPI + SQLite + WebSocket for real-time updates
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import json

from database import init_db, get_db
from models import Sign, Event, Template, Message, Submission
from schemas import (
    SignCreate, SignUpdate, SignStatus, SignHeartbeat,
    EventCreate, EventUpdate,
    TemplateCreate, TemplateUpdate,
    MessageCreate, MessageUpdate,
    SubmissionCreate, SubmissionUpdate,
    OverrideRequest
)
from websocket_manager import ConnectionManager

# WebSocket manager for real-time broadcasts
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    print("✅ Database initialized")
    yield
    print("👋 Shutting down")

app = FastAPI(
    title="CITYARRAY Festival API",
    description="Backend API for Festival Edition signage system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - allow dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# WEBSOCKET - Real-time updates
# =============================================================================

@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for operator dashboards.
    Receives real-time updates about sign status, messages, etc.
    """
    await manager.connect(websocket, client_type="dashboard")
    try:
        while True:
            # Keep connection alive, listen for dashboard commands
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle dashboard commands (e.g., request full status)
            if message.get("type") == "get_all_signs":
                db = next(get_db())
                signs = db.query(Sign).all()
                await websocket.send_json({
                    "type": "all_signs",
                    "data": [sign.to_dict() for sign in signs]
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws/sign/{sign_id}")
async def sign_websocket(websocket: WebSocket, sign_id: str):
    """
    WebSocket endpoint for individual signs.
    Signs connect here to receive messages and send status updates.
    """
    await manager.connect(websocket, client_type="sign", client_id=sign_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "heartbeat":
                # Process heartbeat from sign
                await process_sign_heartbeat(sign_id, message.get("data", {}))
                
            elif message.get("type") == "metrics":
                # Process crowd/impression metrics
                await process_sign_metrics(sign_id, message.get("data", {}))
                
            elif message.get("type") == "ack":
                # Sign acknowledged message receipt
                await process_message_ack(sign_id, message.get("message_id"))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Broadcast sign disconnected to dashboards
        await manager.broadcast_to_dashboards({
            "type": "sign_disconnected",
            "sign_id": sign_id,
            "timestamp": datetime.utcnow().isoformat()
        })

async def process_sign_heartbeat(sign_id: str, data: dict):
    """Process heartbeat from sign and broadcast to dashboards"""
    db = next(get_db())
    sign = db.query(Sign).filter(Sign.id == sign_id).first()
    
    if sign:
        sign.status = "online"
        sign.battery = data.get("battery", sign.battery)
        sign.signal_strength = data.get("signal_strength", sign.signal_strength)
        sign.crowd_density = data.get("crowd_density", sign.crowd_density)
        sign.crowd_count = data.get("crowd_count", sign.crowd_count)
        sign.ambient_noise_db = data.get("ambient_noise_db", sign.ambient_noise_db)
        sign.current_message_id = data.get("current_message_id", sign.current_message_id)
        sign.last_seen = datetime.utcnow()
        db.commit()
        
        # Broadcast update to all dashboards
        await manager.broadcast_to_dashboards({
            "type": "sign_update",
            "data": sign.to_dict()
        })

async def process_sign_metrics(sign_id: str, data: dict):
    """Process crowd/impression metrics from sign"""
    # Store metrics for analytics
    # TODO: Add to impressions table
    await manager.broadcast_to_dashboards({
        "type": "sign_metrics",
        "sign_id": sign_id,
        "data": data
    })

async def process_message_ack(sign_id: str, message_id: str):
    """Process message acknowledgment from sign"""
    await manager.broadcast_to_dashboards({
        "type": "message_ack",
        "sign_id": sign_id,
        "message_id": message_id,
        "timestamp": datetime.utcnow().isoformat()
    })

# =============================================================================
# EVENTS
# =============================================================================

@app.post("/api/events", tags=["Events"])
async def create_event(event: EventCreate, db=Depends(get_db)):
    """Create a new event"""
    db_event = Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event.to_dict()

@app.get("/api/events", tags=["Events"])
async def list_events(db=Depends(get_db)):
    """List all events"""
    events = db.query(Event).all()
    return [e.to_dict() for e in events]

@app.get("/api/events/{event_id}", tags=["Events"])
async def get_event(event_id: str, db=Depends(get_db)):
    """Get event details"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.to_dict()

# =============================================================================
# SIGNS
# =============================================================================

@app.post("/api/signs", tags=["Signs"])
async def register_sign(sign: SignCreate, db=Depends(get_db)):
    """Register a new sign"""
    db_sign = Sign(**sign.model_dump())
    db.add(db_sign)
    db.commit()
    db.refresh(db_sign)
    
    await manager.broadcast_to_dashboards({
        "type": "sign_registered",
        "data": db_sign.to_dict()
    })
    return db_sign.to_dict()

@app.get("/api/signs", tags=["Signs"])
async def list_signs(event_id: str = None, db=Depends(get_db)):
    """List all signs, optionally filtered by event"""
    query = db.query(Sign)
    if event_id:
        query = query.filter(Sign.event_id == event_id)
    signs = query.all()
    return [s.to_dict() for s in signs]

@app.get("/api/signs/{sign_id}", tags=["Signs"])
async def get_sign(sign_id: str, db=Depends(get_db)):
    """Get sign details"""
    sign = db.query(Sign).filter(Sign.id == sign_id).first()
    if not sign:
        raise HTTPException(status_code=404, detail="Sign not found")
    return sign.to_dict()

@app.post("/api/signs/{sign_id}/heartbeat", tags=["Signs"])
async def sign_heartbeat(sign_id: str, heartbeat: SignHeartbeat, db=Depends(get_db)):
    """
    HTTP fallback for sign heartbeat (when WebSocket unavailable).
    Prefer WebSocket for real-time updates.
    """
    sign = db.query(Sign).filter(Sign.id == sign_id).first()
    if not sign:
        raise HTTPException(status_code=404, detail="Sign not found")
    
    sign.status = "online"
    sign.battery = heartbeat.battery
    sign.signal_strength = heartbeat.signal_strength
    sign.crowd_density = heartbeat.crowd_density
    sign.crowd_count = heartbeat.crowd_count
    sign.ambient_noise_db = heartbeat.ambient_noise_db
    sign.last_seen = datetime.utcnow()
    db.commit()
    
    await manager.broadcast_to_dashboards({
        "type": "sign_update",
        "data": sign.to_dict()
    })
    
    # Return any pending messages for this sign
    pending_messages = db.query(Message).filter(
        Message.target_signs.contains(sign_id),
        Message.status == "pending"
    ).all()
    
    return {
        "status": "ok",
        "pending_messages": [m.to_dict() for m in pending_messages]
    }

# =============================================================================
# TEMPLATES
# =============================================================================

@app.post("/api/templates", tags=["Templates"])
async def create_template(template: TemplateCreate, db=Depends(get_db)):
    """Create a new message template"""
    db_template = Template(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template.to_dict()

@app.get("/api/templates", tags=["Templates"])
async def list_templates(event_id: str = None, category: str = None, db=Depends(get_db)):
    """List templates, optionally filtered"""
    query = db.query(Template)
    if event_id:
        query = query.filter(Template.event_id == event_id)
    if category:
        query = query.filter(Template.category == category)
    templates = query.all()
    return [t.to_dict() for t in templates]

@app.get("/api/templates/{template_id}", tags=["Templates"])
async def get_template(template_id: str, db=Depends(get_db)):
    """Get template details"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()

# =============================================================================
# MESSAGES & OVERRIDE
# =============================================================================

@app.post("/api/messages", tags=["Messages"])
async def send_message(message: MessageCreate, db=Depends(get_db)):
    """Send a message to signs"""
    db_message = Message(**message.model_dump())
    db_message.status = "pending"
    db_message.created_at = datetime.utcnow()
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Send to target signs via WebSocket
    for sign_id in message.target_signs:
        await manager.send_to_sign(sign_id, {
            "type": "new_message",
            "data": db_message.to_dict()
        })
    
    # Notify dashboards
    await manager.broadcast_to_dashboards({
        "type": "message_sent",
        "data": db_message.to_dict()
    })
    
    return db_message.to_dict()

@app.post("/api/override", tags=["Messages"])
async def send_override(override: OverrideRequest, db=Depends(get_db)):
    """
    Send an override message to signs.
    Higher priority, interrupts scheduled content.
    """
    # Create override message
    db_message = Message(
        event_id=override.event_id,
        template_id=override.template_id,
        content=override.content,
        target_signs=override.target_signs if override.target_signs else ["all"],
        priority=override.priority,
        override_mode=override.mode,
        audio_enabled=override.audio_enabled,
        audio_languages=override.audio_languages,
        status="active",
        created_at=datetime.utcnow(),
        created_by=override.created_by
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Determine target signs
    if "all" in db_message.target_signs:
        signs = db.query(Sign).filter(Sign.event_id == override.event_id).all()
        target_sign_ids = [s.id for s in signs]
    else:
        target_sign_ids = db_message.target_signs
    
    # Send to all target signs
    override_payload = {
        "type": "override",
        "data": db_message.to_dict()
    }
    
    for sign_id in target_sign_ids:
        await manager.send_to_sign(sign_id, override_payload)
    
    # Broadcast to dashboards
    await manager.broadcast_to_dashboards({
        "type": "override_activated",
        "data": db_message.to_dict(),
        "target_signs": target_sign_ids
    })
    
    return {
        "status": "override_sent",
        "message": db_message.to_dict(),
        "target_signs": target_sign_ids
    }

@app.delete("/api/override/{message_id}", tags=["Messages"])
async def cancel_override(message_id: str, db=Depends(get_db)):
    """Cancel an active override"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Override not found")
    
    message.status = "cancelled"
    db.commit()
    
    # Notify signs to resume normal operation
    cancel_payload = {
        "type": "override_cancelled",
        "message_id": message_id
    }
    
    if "all" in message.target_signs:
        await manager.broadcast_to_signs(cancel_payload)
    else:
        for sign_id in message.target_signs:
            await manager.send_to_sign(sign_id, cancel_payload)
    
    # Notify dashboards
    await manager.broadcast_to_dashboards({
        "type": "override_cancelled",
        "message_id": message_id
    })
    
    return {"status": "override_cancelled"}

# =============================================================================
# SUBMISSIONS (Attendee messages)
# =============================================================================

@app.post("/api/submissions", tags=["Submissions"])
async def create_submission(submission: SubmissionCreate, db=Depends(get_db)):
    """Create a new attendee submission (from SMS or web form)"""
    db_submission = Submission(**submission.model_dump())
    db_submission.status = "pending"
    db_submission.created_at = datetime.utcnow()
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # Notify dashboards of new submission needing moderation
    await manager.broadcast_to_dashboards({
        "type": "new_submission",
        "data": db_submission.to_dict()
    })
    
    return db_submission.to_dict()

@app.get("/api/submissions", tags=["Submissions"])
async def list_submissions(
    event_id: str = None,
    status: str = None,
    category: str = None,
    db=Depends(get_db)
):
    """List submissions with optional filters"""
    query = db.query(Submission)
    if event_id:
        query = query.filter(Submission.event_id == event_id)
    if status:
        query = query.filter(Submission.status == status)
    if category:
        query = query.filter(Submission.category == category)
    
    submissions = query.order_by(Submission.created_at.desc()).all()
    return [s.to_dict() for s in submissions]

@app.post("/api/submissions/{submission_id}/approve", tags=["Submissions"])
async def approve_submission(
    submission_id: str,
    target_zones: list[str] = None,
    duration_seconds: int = 60,
    db=Depends(get_db)
):
    """Approve a submission for display"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    submission.status = "approved"
    submission.moderated_at = datetime.utcnow()
    db.commit()
    
    # Create message from approved submission
    # TODO: Determine target signs from zones
    
    await manager.broadcast_to_dashboards({
        "type": "submission_approved",
        "data": submission.to_dict()
    })
    
    return submission.to_dict()

@app.post("/api/submissions/{submission_id}/reject", tags=["Submissions"])
async def reject_submission(submission_id: str, reason: str = None, db=Depends(get_db)):
    """Reject a submission"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    submission.status = "rejected"
    submission.moderated_at = datetime.utcnow()
    submission.rejection_reason = reason
    db.commit()
    
    await manager.broadcast_to_dashboards({
        "type": "submission_rejected",
        "data": submission.to_dict()
    })
    
    return submission.to_dict()

# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "connected_dashboards": manager.dashboard_count,
        "connected_signs": manager.sign_count
    }

@app.get("/api/status", tags=["System"])
async def system_status(db=Depends(get_db)):
    """Get overall system status"""
    total_signs = db.query(Sign).count()
    online_signs = db.query(Sign).filter(Sign.status == "online").count()
    pending_submissions = db.query(Submission).filter(Submission.status == "pending").count()
    
    return {
        "signs": {
            "total": total_signs,
            "online": online_signs,
            "offline": total_signs - online_signs
        },
        "submissions": {
            "pending": pending_submissions
        },
        "connections": {
            "dashboards": manager.dashboard_count,
            "signs": manager.sign_count
        },
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

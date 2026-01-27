"""
CITYARRAY Festival Edition - Complete Application
API + Dashboard (HTMX/Jinja2)
"""

import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if os.path.exists(backend_path):
    sys.path.insert(0, os.path.abspath(backend_path))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from datetime import datetime
import json

# Import from backend
from database import init_db, get_db
from models import Sign, Event, Template, Message, Submission, Zone
from schemas import (
    SignCreate, SignUpdate, SignStatus, SignHeartbeat,
    EventCreate, EventUpdate,
    TemplateCreate, TemplateUpdate,
    MessageCreate, MessageUpdate,
    SubmissionCreate, SubmissionUpdate,
    OverrideRequest
)
from websocket_manager import ConnectionManager

# WebSocket manager
manager = ConnectionManager()

# Templates
templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    print("✅ Database initialized")
    yield
    print("👋 Shutting down")


app = FastAPI(
    title="CITYARRAY Festival Edition",
    description="Festival signage system with operator dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (if any)
# app.mount("/static", StaticFiles(directory="static"), name="static")


# =============================================================================
# DASHBOARD ROUTES (HTMX + Jinja2)
# =============================================================================

def get_system_stats(db):
    """Get system statistics for dashboard"""
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
        }
    }


@app.get("/")
async def dashboard(request: Request, db=Depends(get_db)):
    """Main dashboard view"""
    signs = db.query(Sign).all()
    zones = db.query(Zone).all()
    messages = db.query(Message).order_by(Message.created_at.desc()).limit(10).all()
    tpls = db.query(Template).all()
    stats = get_system_stats(db)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "signs": [s.to_dict() for s in signs],
        "zones": [z.to_dict() for z in zones],
        "messages": [m.to_dict() for m in messages],
        "templates": [t.to_dict() for t in tpls],
        "stats": stats
    })


@app.get("/signs")
async def signs_page(request: Request, db=Depends(get_db)):
    """Signs management page"""
    signs = db.query(Sign).all()
    zones = db.query(Zone).all()
    stats = get_system_stats(db)
    
    return templates.TemplateResponse("signs.html", {
        "request": request,
        "active_page": "signs",
        "signs": [s.to_dict() for s in signs],
        "zones": [z.to_dict() for z in zones],
        "stats": stats
    })


@app.get("/messages")
async def messages_page(request: Request, db=Depends(get_db)):
    """Messages history page"""
    messages = db.query(Message).order_by(Message.created_at.desc()).all()
    signs = db.query(Sign).all()
    zones = db.query(Zone).all()
    tpls = db.query(Template).all()
    stats = get_system_stats(db)
    
    return templates.TemplateResponse("messages.html", {
        "request": request,
        "active_page": "messages",
        "messages": [m.to_dict() for m in messages],
        "signs": [s.to_dict() for s in signs],
        "zones": [z.to_dict() for z in zones],
        "templates": [t.to_dict() for t in tpls],
        "stats": stats
    })


@app.get("/templates")
async def templates_page(request: Request, db=Depends(get_db)):
    """Templates management page"""
    tpls = db.query(Template).all()
    stats = get_system_stats(db)
    
    return templates.TemplateResponse("templates.html", {
        "request": request,
        "active_page": "templates",
        "templates": [t.to_dict() for t in tpls],
        "stats": stats
    })


@app.get("/submissions")
async def submissions_page(request: Request, status: str = None, db=Depends(get_db)):
    """Submissions moderation page"""
    query = db.query(Submission)
    if status:
        query = query.filter(Submission.status == status)
    submissions = query.order_by(Submission.created_at.desc()).all()
    stats = get_system_stats(db)
    
    return templates.TemplateResponse("submissions.html", {
        "request": request,
        "active_page": "submissions",
        "submissions": [s.to_dict() for s in submissions],
        "filter_status": status,
        "stats": stats
    })


@app.get("/simulator")
async def simulator_page(request: Request, db=Depends(get_db)):
    """Sign simulator page"""
    stats = get_system_stats(db)
    
    return templates.TemplateResponse("simulator.html", {
        "request": request,
        "active_page": "simulator",
        "stats": stats
    })


# =============================================================================
# WEBSOCKET ENDPOINTS
# =============================================================================

@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket for operator dashboards"""
    await manager.connect(websocket, client_type="dashboard")
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
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
    """WebSocket for individual signs"""
    await manager.connect(websocket, client_type="sign", client_id=sign_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "heartbeat":
                await process_sign_heartbeat(sign_id, message.get("data", {}))
            elif message.get("type") == "metrics":
                await process_sign_metrics(sign_id, message.get("data", {}))
            elif message.get("type") == "ack":
                await process_message_ack(sign_id, message.get("message_id"))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast_to_dashboards({
            "type": "sign_disconnected",
            "sign_id": sign_id,
            "timestamp": datetime.utcnow().isoformat()
        })


async def process_sign_heartbeat(sign_id: str, data: dict):
    """Process heartbeat from sign"""
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
        
        await manager.broadcast_to_dashboards({
            "type": "sign_update",
            "data": sign.to_dict()
        })


async def process_sign_metrics(sign_id: str, data: dict):
    """Process metrics from sign"""
    await manager.broadcast_to_dashboards({
        "type": "sign_metrics",
        "sign_id": sign_id,
        "data": data
    })


async def process_message_ack(sign_id: str, message_id: str):
    """Process message acknowledgment"""
    await manager.broadcast_to_dashboards({
        "type": "message_ack",
        "sign_id": sign_id,
        "message_id": message_id,
        "timestamp": datetime.utcnow().isoformat()
    })


# =============================================================================
# API ENDPOINTS
# =============================================================================

# --- Signs ---
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
    """List all signs"""
    query = db.query(Sign)
    if event_id:
        query = query.filter(Sign.event_id == event_id)
    return [s.to_dict() for s in query.all()]


@app.get("/api/signs/{sign_id}", tags=["Signs"])
async def get_sign(sign_id: str, db=Depends(get_db)):
    """Get sign details"""
    sign = db.query(Sign).filter(Sign.id == sign_id).first()
    if not sign:
        raise HTTPException(status_code=404, detail="Sign not found")
    return sign.to_dict()


@app.put("/api/signs/{sign_id}", tags=["Signs"])
async def update_sign(sign_id: str, sign: SignUpdate, db=Depends(get_db)):
    """Update a sign"""
    db_sign = db.query(Sign).filter(Sign.id == sign_id).first()
    if not db_sign:
        raise HTTPException(status_code=404, detail="Sign not found")
    
    for key, value in sign.model_dump(exclude_unset=True).items():
        setattr(db_sign, key, value)
    db.commit()
    db.refresh(db_sign)
    
    await manager.broadcast_to_dashboards({
        "type": "sign_updated",
        "data": db_sign.to_dict()
    })
    return db_sign.to_dict()


# --- Zones ---
@app.post("/api/zones", tags=["Zones"])
async def create_zone(name: str, code: str = None, color: str = "#3B82F6", description: str = None, db=Depends(get_db)):
    """Create a new zone"""
    zone = Zone(name=name, code=code or name[:3].upper(), color=color, description=description)
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone.to_dict()


@app.get("/api/zones", tags=["Zones"])
async def list_zones(db=Depends(get_db)):
    """List all zones"""
    return [z.to_dict() for z in db.query(Zone).all()]


@app.put("/api/zones/{zone_id}", tags=["Zones"])
async def update_zone(zone_id: str, name: str = None, code: str = None, color: str = None, description: str = None, db=Depends(get_db)):
    """Update a zone"""
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    if name: zone.name = name
    if code: zone.code = code
    if color: zone.color = color
    if description: zone.description = description
    db.commit()
    db.refresh(zone)
    return zone.to_dict()


@app.delete("/api/zones/{zone_id}", tags=["Zones"])
async def delete_zone(zone_id: str, db=Depends(get_db)):
    """Delete a zone"""
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    db.delete(zone)
    db.commit()
    return {"deleted": zone_id}


# --- Templates ---
@app.post("/api/templates", tags=["Templates"])
async def create_template(template: TemplateCreate, db=Depends(get_db)):
    """Create a new template"""
    db_template = Template(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template.to_dict()


@app.get("/api/templates", tags=["Templates"])
async def list_templates(db=Depends(get_db)):
    """List all templates"""
    return [t.to_dict() for t in db.query(Template).all()]


@app.get("/api/templates/{template_id}", tags=["Templates"])
async def get_template(template_id: str, db=Depends(get_db)):
    """Get template details"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()


@app.put("/api/templates/{template_id}", tags=["Templates"])
async def update_template(template_id: str, template: TemplateUpdate, db=Depends(get_db)):
    """Update a template"""
    db_template = db.query(Template).filter(Template.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for key, value in template.model_dump(exclude_unset=True).items():
        setattr(db_template, key, value)
    db.commit()
    return db_template.to_dict()


# --- Messages ---
@app.post("/api/messages", tags=["Messages"])
async def send_message(message: MessageCreate, db=Depends(get_db)):
    """Send a message to signs"""
    db_message = Message(**message.model_dump())
    db_message.status = "pending"
    db_message.created_at = datetime.utcnow()
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Send to target signs
    for sign_id in message.target_signs:
        await manager.send_to_sign(sign_id, {
            "type": "new_message",
            "data": db_message.to_dict()
        })
    
    await manager.broadcast_to_dashboards({
        "type": "message_sent",
        "data": db_message.to_dict()
    })
    
    return db_message.to_dict()


@app.get("/api/messages", tags=["Messages"])
async def list_messages(db=Depends(get_db)):
    """List all messages"""
    return [m.to_dict() for m in db.query(Message).order_by(Message.created_at.desc()).all()]


@app.post("/api/messages/{message_id}/clear", tags=["Messages"])
async def clear_message(message_id: str, db=Depends(get_db)):
    """Clear an active message"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.status = "cleared"
    db.commit()
    
    # Notify signs to clear the message
    await manager.broadcast_to_signs({
        "type": "clear_message",
        "data": {"message_id": message_id}
    })
    
    await manager.broadcast_to_dashboards({
        "type": "message_cleared",
        "data": message.to_dict()
    })
    
    return {"status": "cleared", "message_id": message_id}


@app.post("/api/override", tags=["Messages"])
async def send_override(override: OverrideRequest, db=Depends(get_db)):
    """Send an override message"""
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
    
    # Get target signs
    if "all" in db_message.target_signs:
        signs = db.query(Sign).all()
        target_sign_ids = [s.id for s in signs]
    else:
        target_sign_ids = db_message.target_signs
    
    # Send to signs
    for sign_id in target_sign_ids:
        await manager.send_to_sign(sign_id, {
            "type": "override",
            "data": db_message.to_dict()
        })
    
    await manager.broadcast_to_dashboards({
        "type": "override_activated",
        "data": db_message.to_dict(),
        "target_signs": target_sign_ids
    })
    
    return {"status": "override_sent", "message": db_message.to_dict()}


# --- Submissions ---
@app.post("/api/submissions", tags=["Submissions"])
async def create_submission(submission: SubmissionCreate, db=Depends(get_db)):
    """Create a new submission"""
    db_submission = Submission(**submission.model_dump())
    db_submission.status = "pending"
    db_submission.created_at = datetime.utcnow()
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    await manager.broadcast_to_dashboards({
        "type": "new_submission",
        "data": db_submission.to_dict()
    })
    
    return db_submission.to_dict()


@app.get("/api/submissions", tags=["Submissions"])
async def list_submissions(status: str = None, db=Depends(get_db)):
    """List submissions"""
    query = db.query(Submission)
    if status:
        query = query.filter(Submission.status == status)
    return [s.to_dict() for s in query.order_by(Submission.created_at.desc()).all()]


@app.post("/api/submissions/{submission_id}/approve", tags=["Submissions"])
async def approve_submission(submission_id: str, db=Depends(get_db)):
    """Approve a submission"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    submission.status = "approved"
    submission.moderated_at = datetime.utcnow()
    db.commit()
    
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


# --- System ---
@app.get("/health", tags=["System"])
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "connected_dashboards": manager.dashboard_count,
        "connected_signs": manager.sign_count
    }


@app.get("/api/status", tags=["System"])
async def system_status(db=Depends(get_db)):
    """System status"""
    return {
        **get_system_stats(db),
        "connections": {
            "dashboards": manager.dashboard_count,
            "signs": manager.sign_count
        },
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

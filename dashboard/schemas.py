"""
CITYARRAY Festival Edition - Pydantic Schemas
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SignCreate(BaseModel):
    name: str
    event_id: Optional[str] = None
    zone: Optional[str] = None
    location: Optional[str] = None
    display_type: str = "led"
    status: str = "offline"

class SignUpdate(BaseModel):
    name: Optional[str] = None
    zone: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None

class SignStatus(BaseModel):
    status: str
    battery: Optional[int] = None
    signal_strength: Optional[int] = None

class SignHeartbeat(BaseModel):
    battery: Optional[int] = None
    signal_strength: Optional[int] = None
    crowd_density: Optional[float] = None
    crowd_count: Optional[int] = None
    ambient_noise_db: Optional[float] = None
    current_message_id: Optional[str] = None

class EventCreate(BaseModel):
    name: str
    venue: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class EventUpdate(BaseModel):
    name: Optional[str] = None
    venue: Optional[str] = None
    status: Optional[str] = None

class TemplateCreate(BaseModel):
    name: str
    category: Optional[str] = None
    content: Optional[str] = None
    audio_enabled: bool = False
    priority: int = 50

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    audio_enabled: Optional[bool] = None
    priority: Optional[int] = None

class MessageCreate(BaseModel):
    event_id: Optional[str] = None
    template_id: Optional[str] = None
    content: str
    target_signs: List[str] = ["all"]
    priority: str = "normal"
    audio_enabled: bool = False
    audio_languages: Optional[List[str]] = None

class MessageUpdate(BaseModel):
    status: Optional[str] = None

class SubmissionCreate(BaseModel):
    event_id: Optional[str] = None
    content: str
    sender_name: Optional[str] = None
    sender_phone: Optional[str] = None
    category: str = "message"

class SubmissionUpdate(BaseModel):
    status: Optional[str] = None
    rejection_reason: Optional[str] = None

class OverrideRequest(BaseModel):
    event_id: Optional[str] = None
    template_id: Optional[str] = None
    content: str
    target_signs: Optional[List[str]] = None
    priority: str = "high"
    mode: str = "interrupt"
    audio_enabled: bool = True
    audio_languages: List[str] = ["en", "es"]
    created_by: Optional[str] = None

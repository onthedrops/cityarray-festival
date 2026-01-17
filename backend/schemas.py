"""
CITYARRAY Festival Edition - Pydantic Schemas
Request/Response validation models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# =============================================================================
# EVENT SCHEMAS
# =============================================================================

class EventCreate(BaseModel):
    name: str
    description: Optional[str] = None
    venue_name: Optional[str] = None
    venue_map_url: Optional[str] = None
    weather_lat: Optional[float] = None
    weather_lon: Optional[float] = None
    twilio_number: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    timezone: str = "America/Los_Angeles"
    config: dict = {}


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    venue_name: Optional[str] = None
    venue_map_url: Optional[str] = None
    weather_lat: Optional[float] = None
    weather_lon: Optional[float] = None
    twilio_number: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    timezone: Optional[str] = None
    config: Optional[dict] = None


# =============================================================================
# SIGN SCHEMAS
# =============================================================================

class SignCreate(BaseModel):
    name: str
    event_id: Optional[str] = None
    hardware_id: Optional[str] = None
    zone_id: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    display_type: str = "led"
    has_camera: bool = True
    has_speaker: bool = True
    has_microphone: bool = True
    config: dict = {}


class SignUpdate(BaseModel):
    name: Optional[str] = None
    zone_id: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    config: Optional[dict] = None


class SignStatus(BaseModel):
    status: str
    battery: Optional[int] = None
    signal_strength: Optional[int] = None
    crowd_density: Optional[str] = None
    crowd_count: Optional[int] = None
    current_message_id: Optional[str] = None


class SignHeartbeat(BaseModel):
    """Heartbeat data from sign to server"""
    battery: Optional[int] = Field(None, ge=0, le=100)
    signal_strength: Optional[int] = None
    crowd_density: Optional[str] = None
    crowd_count: Optional[int] = Field(None, ge=0)
    ambient_noise_db: Optional[float] = None
    current_message_id: Optional[str] = None
    current_template: Optional[str] = None
    uptime_seconds: Optional[int] = None
    errors: Optional[List[str]] = []


# =============================================================================
# TEMPLATE SCHEMAS
# =============================================================================

class TemplateCreate(BaseModel):
    event_id: Optional[str] = None
    name: str
    category: str
    title: Optional[str] = None
    body: Optional[str] = None
    footer: Optional[str] = None
    background_color: str = "#FFFFFF"
    text_color: str = "#000000"
    icon: Optional[str] = None
    audio_enabled: bool = False
    audio_message: Optional[str] = None
    audio_languages: List[str] = ["en"]
    priority: int = 10
    variables: List[str] = []


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    footer: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    icon: Optional[str] = None
    audio_enabled: Optional[bool] = None
    audio_message: Optional[str] = None
    audio_languages: Optional[List[str]] = None
    priority: Optional[int] = None
    variables: Optional[List[str]] = None


# =============================================================================
# MESSAGE SCHEMAS
# =============================================================================

class MessageCreate(BaseModel):
    event_id: str
    template_id: Optional[str] = None
    content: Optional[str] = None
    target_signs: List[str] = ["all"]
    target_zones: List[str] = []
    priority: int = 10
    audio_enabled: bool = False
    audio_languages: List[str] = ["en"]
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    duration_seconds: int = 30
    created_by: Optional[str] = None


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    target_signs: Optional[List[str]] = None
    target_zones: Optional[List[str]] = None
    status: Optional[str] = None


class OverrideRequest(BaseModel):
    """Request to send an override message"""
    event_id: str
    template_id: Optional[str] = None
    content: Optional[str] = None
    target_signs: Optional[List[str]] = None  # None = all signs
    target_zones: Optional[List[str]] = None
    priority: int = Field(80, ge=1, le=100)
    mode: str = Field("insert", pattern="^(insert|replace|emergency)$")
    audio_enabled: bool = True
    audio_languages: List[str] = ["en", "es"]
    duration_seconds: Optional[int] = None  # None = until cancelled
    created_by: Optional[str] = None


# =============================================================================
# SCHEDULE SCHEMAS
# =============================================================================

class ScheduleCreate(BaseModel):
    event_id: str
    template_id: str
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    frequency_minutes: int = 0  # 0 = once
    duration_seconds: int = 30
    target_zones: List[str] = ["all"]
    priority: int = 10
    enabled: bool = True
    active_days: Optional[List[str]] = None


class ScheduleUpdate(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    frequency_minutes: Optional[int] = None
    duration_seconds: Optional[int] = None
    target_zones: Optional[List[str]] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None


# =============================================================================
# SUBMISSION SCHEMAS
# =============================================================================

class SubmissionCreate(BaseModel):
    """Attendee submission (from SMS or web form)"""
    event_id: str
    category: str  # lost_item, found_item, meetup, report, feedback
    content: str
    phone: Optional[str] = None
    contact_method: Optional[str] = None
    source: str = "web"  # sms, web
    source_sign_id: Optional[str] = None
    zone_id: Optional[str] = None


class SubmissionUpdate(BaseModel):
    status: Optional[str] = None
    target_zones: Optional[List[str]] = None
    display_duration_seconds: Optional[int] = None


# =============================================================================
# USER SCHEMAS
# =============================================================================

class UserCreate(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None
    role: str = "staff"
    assigned_zones: Optional[List[str]] = None
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    assigned_zones: Optional[List[str]] = None
    alert_sms: Optional[bool] = None
    alert_voice: Optional[bool] = None
    alert_email: Optional[bool] = None


# =============================================================================
# TWILIO SCHEMAS
# =============================================================================

class TwilioSMSWebhook(BaseModel):
    """Incoming SMS webhook from Twilio"""
    From: str = Field(alias="From")
    To: str = Field(alias="To")
    Body: str = Field(alias="Body")
    MessageSid: str = Field(alias="MessageSid")
    AccountSid: Optional[str] = None
    NumMedia: Optional[int] = 0

    class Config:
        populate_by_name = True


class TwilioVoiceWebhook(BaseModel):
    """Incoming voice webhook from Twilio"""
    From: str = Field(alias="From")
    To: str = Field(alias="To")
    CallSid: str = Field(alias="CallSid")
    CallStatus: str = Field(alias="CallStatus")
    Digits: Optional[str] = None

    class Config:
        populate_by_name = True


# =============================================================================
# ANALYTICS SCHEMAS
# =============================================================================

class ImpressionCreate(BaseModel):
    sign_id: str
    message_id: str
    estimated_viewers: int
    crowd_density: Optional[str] = None
    dwell_time_seconds: Optional[int] = None


class AnalyticsQuery(BaseModel):
    event_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    group_by: Optional[str] = None  # hour, day, zone, category

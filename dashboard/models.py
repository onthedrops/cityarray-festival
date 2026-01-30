"""
CITYARRAY Festival Edition - Database Models
SQLAlchemy ORM models for SQLite (easily swappable to PostgreSQL)
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())


class Event(Base):
    """Event/Festival configuration"""
    __tablename__ = "events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    venue_name = Column(String(255))
    venue_map_url = Column(Text)  # URL or base64 of venue map image
    
    # Location for weather API
    weather_lat = Column(Float)
    weather_lon = Column(Float)
    
    # Twilio configuration
    twilio_number = Column(String(20))
    
    # Event timing
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    timezone = Column(String(50), default="America/Los_Angeles")
    
    # Configuration JSON (flexible settings)
    config = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    signs = relationship("Sign", back_populates="event")
    templates = relationship("Template", back_populates="event")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "venue_name": self.venue_name,
            "venue_map_url": self.venue_map_url,
            "weather_lat": self.weather_lat,
            "weather_lon": self.weather_lon,
            "twilio_number": self.twilio_number,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "timezone": self.timezone,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Zone(Base):
    """Zones within an event venue"""
    __tablename__ = "zones"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("events.id"), nullable=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10))  # Short code like "A", "B", "MAIN"
    color = Column(String(7))  # Hex color for map display
    description = Column(Text)
    
    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "name": self.name,
            "code": self.code,
            "color": self.color,
            "description": self.description
        }


class Sign(Base):
    """Individual sign units"""
    __tablename__ = "signs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("events.id"))
    
    # Identification
    name = Column(String(100), nullable=False)
    hardware_id = Column(String(100))  # Pi serial number or unique ID
    zone_id = Column(String(36))
    
    # Position on venue map
    position_x = Column(Integer)
    position_y = Column(Integer)
    
    # Current status
    status = Column(String(20), default="offline")  # online, offline, warning, error
    battery = Column(Integer)  # Percentage 0-100
    signal_strength = Column(Integer)  # dBm or percentage
    
    # Crowd detection data
    crowd_density = Column(String(20))  # low, medium, high, critical
    crowd_count = Column(Integer)
    ambient_noise_db = Column(Float)
    
    # Current display
    current_message_id = Column(String(36))
    current_template = Column(String(100))
    
    # Timestamps
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Hardware info
    display_type = Column(String(50))  # e-paper, led
    has_camera = Column(Boolean, default=True)
    has_speaker = Column(Boolean, default=True)
    has_microphone = Column(Boolean, default=True)
    
    # Configuration
    config = Column(JSON, default=dict)
    
    # Relationships
    event = relationship("Event", back_populates="signs")
    
    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "name": self.name,
            "hardware_id": self.hardware_id,
            "zone_id": self.zone_id,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "status": self.status,
            "battery": self.battery,
            "signal_strength": self.signal_strength,
            "crowd_density": self.crowd_density,
            "crowd_count": self.crowd_count,
            "ambient_noise_db": self.ambient_noise_db,
            "current_message_id": self.current_message_id,
            "current_template": self.current_template,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "display_type": self.display_type,
            "has_camera": self.has_camera,
            "has_speaker": self.has_speaker,
            "has_microphone": self.has_microphone,
            "config": self.config
        }


class Template(Base):
    """Message templates"""
    __tablename__ = "templates"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("events.id"))
    
    # Template identification
    name = Column(String(100), nullable=False)
    category = Column(String(50))  # emergency, weather, schedule, wayfinding, sponsor, attendee
    
    # Content
    title = Column(String(255))
    body = Column(Text)
    footer = Column(String(255))
    
    # Display settings
    background_color = Column(String(7), default="#FFFFFF")
    text_color = Column(String(7), default="#000000")
    icon = Column(String(50))  # Emoji or icon name
    
    # Audio settings
    audio_enabled = Column(Boolean, default=False)
    audio_message = Column(Text)
    audio_languages = Column(JSON, default=["en"])  # List of language codes
    
    # Priority (higher = more important, overrides lower)
    priority = Column(Integer, default=10)
    
    # Variables that can be substituted
    variables = Column(JSON, default=list)  # ["weather_temp", "next_artist", etc.]
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="templates")
    
    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "name": self.name,
            "category": self.category,
            "title": self.title,
            "body": self.body,
            "footer": self.footer,
            "background_color": self.background_color,
            "text_color": self.text_color,
            "icon": self.icon,
            "audio_enabled": self.audio_enabled,
            "audio_message": self.audio_message,
            "audio_languages": self.audio_languages,
            "priority": self.priority,
            "variables": self.variables,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Message(Base):
    """Messages sent to signs"""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("events.id"))
    template_id = Column(String(36), ForeignKey("templates.id"))
    
    # Content (can override template)
    content = Column(Text)
    rendered_content = Column(Text)  # After variable substitution
    
    # Targeting
    target_signs = Column(JSON, default=["all"])  # List of sign IDs or ["all"]
    target_zones = Column(JSON, default=list)  # List of zone IDs
    
    # Priority and override
    priority = Column(Integer, default=10)
    override_mode = Column(String(20))  # insert, replace, emergency
    persistence_mode = Column(String(20), default="timed")  # timed, until_cleared, emergency_lock
    
    # Audio
    audio_enabled = Column(Boolean, default=False)
    audio_languages = Column(JSON, default=["en"])
    
    # Status
    status = Column(String(20), default="pending")  # pending, active, displayed, cancelled, expired
    
    # Scheduling
    scheduled_at = Column(DateTime)
    expires_at = Column(DateTime)
    duration_seconds = Column(Integer, default=30)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))  # User ID or "system"
    displayed_at = Column(DateTime)
    
    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "template_id": self.template_id,
            "content": self.content,
            "rendered_content": self.rendered_content,
            "target_signs": self.target_signs,
            "target_zones": self.target_zones,
            "priority": self.priority,
            "override_mode": self.override_mode,
            "persistence_mode": self.persistence_mode,
            "audio_enabled": self.audio_enabled,
            "audio_languages": self.audio_languages,
            "status": self.status,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by
        }


class Schedule(Base):
    """Scheduled message entries"""
    __tablename__ = "schedules"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("events.id"))
    template_id = Column(String(36), ForeignKey("templates.id"))
    
    # Timing
    start_time = Column(String(5))  # HH:MM format
    end_time = Column(String(5))
    frequency_minutes = Column(Integer)  # How often to show (0 = once)
    duration_seconds = Column(Integer, default=30)
    
    # Targeting
    target_zones = Column(JSON, default=["all"])
    
    # Priority
    priority = Column(Integer, default=10)
    
    # Status
    enabled = Column(Boolean, default=True)
    
    # Days active (for multi-day events)
    active_days = Column(JSON)  # List of dates or ["all"]
    
    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "template_id": self.template_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "frequency_minutes": self.frequency_minutes,
            "duration_seconds": self.duration_seconds,
            "target_zones": self.target_zones,
            "priority": self.priority,
            "enabled": self.enabled,
            "active_days": self.active_days
        }


class Submission(Base):
    """Attendee submissions (lost & found, meetups, etc.)"""
    __tablename__ = "submissions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("events.id"))
    
    # Category
    category = Column(String(50))  # lost_item, found_item, meetup, report, feedback
    
    # Content
    content = Column(Text, nullable=False)
    
    # Contact info
    phone = Column(String(20))
    contact_method = Column(String(50))  # sms, email, none
    
    # Source
    source = Column(String(10))  # sms, web
    source_sign_id = Column(String(36))  # If submitted via QR on a sign
    zone_id = Column(String(36))  # Submitted from or about this zone
    
    # Status
    status = Column(String(20), default="pending")  # pending, approved, rejected, displayed, expired
    
    # Moderation
    moderated_by = Column(String(100))
    moderated_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Display tracking
    displayed_at = Column(DateTime)
    display_duration_seconds = Column(Integer)
    target_zones = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Auto-expire after X hours
    
    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "category": self.category,
            "content": self.content,
            "phone": self.phone[-4:] if self.phone else None,  # Only last 4 digits for privacy
            "source": self.source,
            "zone_id": self.zone_id,
            "status": self.status,
            "moderated_at": self.moderated_at.isoformat() if self.moderated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class User(Base):
    """System users (operators, managers)"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(100))
    phone = Column(String(20))
    
    # Role and permissions
    role = Column(String(50))  # admin, event_manager, zone_lead, staff, sponsor
    assigned_zones = Column(JSON)  # For zone-restricted roles
    
    # Authentication (simplified - use proper auth in production)
    password_hash = Column(String(255))
    
    # Notification preferences
    alert_sms = Column(Boolean, default=True)
    alert_voice = Column(Boolean, default=False)
    alert_email = Column(Boolean, default=True)
    
    # Status
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "assigned_zones": self.assigned_zones,
            "active": self.active
        }


class AuditLog(Base):
    """Audit trail for all actions"""
    __tablename__ = "audit_log"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36))
    user_id = Column(String(36))
    
    # Action details
    action = Column(String(100), nullable=False)  # override_sent, message_approved, etc.
    target_type = Column(String(50))  # sign, message, submission, etc.
    target_id = Column(String(36))
    
    # Details
    details = Column(JSON)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Impression(Base):
    """Analytics: message impressions"""
    __tablename__ = "impressions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    sign_id = Column(String(36), ForeignKey("signs.id"))
    message_id = Column(String(36), ForeignKey("messages.id"))
    
    # Metrics
    estimated_viewers = Column(Integer)
    crowd_density = Column(String(20))
    dwell_time_seconds = Column(Integer)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "sign_id": self.sign_id,
            "message_id": self.message_id,
            "estimated_viewers": self.estimated_viewers,
            "crowd_density": self.crowd_density,
            "dwell_time_seconds": self.dwell_time_seconds,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

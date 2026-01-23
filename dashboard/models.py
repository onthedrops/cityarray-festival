"""
CITYARRAY Festival Edition - Database Models
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Sign(Base):
    __tablename__ = "signs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    event_id = Column(String, nullable=True)
    zone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    display_type = Column(String, default="led")
    status = Column(String, default="offline")
    battery = Column(Integer, nullable=True)
    signal_strength = Column(Integer, nullable=True)
    crowd_density = Column(Float, nullable=True)
    crowd_count = Column(Integer, nullable=True)
    ambient_noise_db = Column(Float, nullable=True)
    current_message_id = Column(String, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "event_id": self.event_id,
            "zone": self.zone, "location": self.location, "display_type": self.display_type,
            "status": self.status, "battery": self.battery, "signal_strength": self.signal_strength,
            "crowd_density": self.crowd_density, "crowd_count": self.crowd_count,
            "ambient_noise_db": self.ambient_noise_db, "current_message_id": self.current_message_id,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Event(Base):
    __tablename__ = "events"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    venue = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String, default="setup")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "venue": self.venue,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status, "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    title = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    footer = Column(String, nullable=True)
    background_color = Column(String, default="#000000")
    text_color = Column(String, default="#FFFFFF")
    icon = Column(String, nullable=True)
    audio_enabled = Column(Boolean, default=False)
    audio_message = Column(Text, nullable=True)
    audio_languages = Column(JSON, default=["en"])
    priority = Column(Integer, default=50)
    variables = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "category": self.category,
            "content": self.content or self.body or "", "title": self.title, "body": self.body,
            "footer": self.footer, "background_color": self.background_color,
            "text_color": self.text_color, "icon": self.icon, "audio_enabled": self.audio_enabled,
            "audio_message": self.audio_message, "audio_languages": self.audio_languages,
            "priority": self.priority, "variables": self.variables,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    event_id = Column(String, nullable=True)
    template_id = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    target_signs = Column(JSON, default=["all"])
    priority = Column(String, default="normal")
    override_mode = Column(String, nullable=True)
    audio_enabled = Column(Boolean, default=False)
    audio_languages = Column(JSON, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id, "event_id": self.event_id, "template_id": self.template_id,
            "content": self.content, "target_signs": self.target_signs, "priority": self.priority,
            "override_mode": self.override_mode, "audio_enabled": self.audio_enabled,
            "audio_languages": self.audio_languages, "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by
        }

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    event_id = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    sender_name = Column(String, nullable=True)
    sender_phone = Column(String, nullable=True)
    category = Column(String, default="message")
    status = Column(String, default="pending")
    rejection_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    moderated_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id, "event_id": self.event_id, "content": self.content,
            "sender_name": self.sender_name, "sender_phone": self.sender_phone,
            "category": self.category, "status": self.status, "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "moderated_at": self.moderated_at.isoformat() if self.moderated_at else None
        }

"""
CITYARRAY Festival Edition - Database Configuration
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cityarray.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized: {DATABASE_URL}")
    from models import Template
    db = SessionLocal()
    if db.query(Template).count() == 0:
        create_default_templates(db)
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_default_templates(db: Session):
    from models import Template
    templates = [
        Template(name="Emergency Evacuation", category="emergency", content="🚨 EVACUATE NOW - Leave the area immediately", audio_enabled=True, priority=100),
        Template(name="Shelter in Place", category="emergency", content="⚠️ SHELTER IN PLACE - Stay where you are", audio_enabled=True, priority=100),
        Template(name="Medical Emergency", category="emergency", content="🏥 MEDICAL ALERT - Keep pathways clear", audio_enabled=True, priority=95),
        Template(name="Lightning Warning", category="weather", content="⛈️ LIGHTNING - Seek shelter immediately", audio_enabled=True, priority=90),
        Template(name="Heat Advisory", category="weather", content="🌡️ HEAT ADVISORY - Stay hydrated!", audio_enabled=True, priority=70),
        Template(name="Crowd Alert", category="crowd", content="👥 AREA CROWDED - Please use alternate routes", audio_enabled=True, priority=60),
        Template(name="Now Playing", category="schedule", content="🎵 NOW PLAYING - Check schedule for details", audio_enabled=False, priority=30),
        Template(name="Restrooms", category="wayfinding", content="🚻 RESTROOMS - Follow directional signs", audio_enabled=False, priority=15),
        Template(name="First Aid", category="wayfinding", content="🏥 FIRST AID - Medical tent nearby", audio_enabled=False, priority=20),
        Template(name="Lost Item", category="attendee", content="🔍 LOST ITEM - Check Lost & Found tent", audio_enabled=False, priority=10),
        Template(name="Welcome", category="general", content="👋 WELCOME - Enjoy the event!", audio_enabled=False, priority=5),
    ]
    for t in templates:
        db.add(t)
    db.commit()
    print(f"✅ Created {len(templates)} default templates")

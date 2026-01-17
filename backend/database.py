"""
CITYARRAY Festival Edition - Database Configuration
SQLite connection with SQLAlchemy (easily swappable to PostgreSQL)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base
import os

# Database URL - SQLite for MVP, PostgreSQL for production
# To switch to PostgreSQL, just change this line:
# DATABASE_URL = "postgresql://user:password@localhost/cityarray"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cityarray.db")

# SQLite-specific settings
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized: {DATABASE_URL}")
    
    # Create default templates if none exist
    from models import Template
    db = SessionLocal()
    if db.query(Template).count() == 0:
        create_default_templates(db)
    db.close()


def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_default_templates(db: Session):
    """Create default message templates"""
    from models import Template
    
    default_templates = [
        # Emergency templates
        Template(
            name="Emergency Evacuation",
            category="emergency",
            title="🚨 EVACUATE NOW",
            body="Leave the area immediately. Follow staff instructions.",
            footer="Salga del área inmediatamente.",
            background_color="#FF0000",
            text_color="#FFFFFF",
            icon="🚨",
            audio_enabled=True,
            audio_message="Attention. Please evacuate the area immediately. Follow staff instructions to the nearest exit.",
            audio_languages=["en", "es", "zh", "vi", "ko"],
            priority=100
        ),
        Template(
            name="Shelter in Place",
            category="emergency",
            title="⚠️ SHELTER IN PLACE",
            body="Stay where you are. Do not leave the area.",
            footer="Quédese donde está.",
            background_color="#FF6600",
            text_color="#FFFFFF",
            icon="⚠️",
            audio_enabled=True,
            audio_message="Attention. Please shelter in place. Stay where you are until further notice.",
            audio_languages=["en", "es"],
            priority=100
        ),
        Template(
            name="Medical Emergency",
            category="emergency",
            title="🏥 MEDICAL ALERT",
            body="Medical emergency in progress. Keep pathways clear.",
            footer="Emergencia médica. Mantenga los pasillos libres.",
            background_color="#FF0000",
            text_color="#FFFFFF",
            icon="🏥",
            audio_enabled=True,
            audio_message="Medical emergency. Please keep pathways clear for emergency responders.",
            audio_languages=["en", "es"],
            priority=95
        ),
        
        # Weather templates
        Template(
            name="Weather Current",
            category="weather",
            title="Weather",
            body="{{weather_temp}}°F - {{weather_condition}}",
            footer="UV Index: {{weather_uv}}",
            background_color="#87CEEB",
            text_color="#000000",
            icon="☀️",
            audio_enabled=False,
            priority=20,
            variables=["weather_temp", "weather_condition", "weather_uv"]
        ),
        Template(
            name="Lightning Warning",
            category="weather",
            title="⛈️ LIGHTNING ALERT",
            body="Lightning detected nearby. Seek shelter immediately.",
            footer="Relámpago detectado. Busque refugio.",
            background_color="#4B0082",
            text_color="#FFFFFF",
            icon="⛈️",
            audio_enabled=True,
            audio_message="Weather alert. Lightning has been detected in the area. Please seek shelter immediately.",
            audio_languages=["en", "es"],
            priority=90
        ),
        Template(
            name="Heat Advisory",
            category="weather",
            title="🌡️ HEAT ADVISORY",
            body="High temperatures. Stay hydrated!",
            footer="Hydration stations: {{hydration_locations}}",
            background_color="#FF4500",
            text_color="#FFFFFF",
            icon="🌡️",
            audio_enabled=True,
            audio_message="Heat advisory in effect. Please stay hydrated. Water stations are available throughout the venue.",
            audio_languages=["en", "es"],
            priority=70,
            variables=["hydration_locations"]
        ),
        
        # Schedule templates
        Template(
            name="Now Playing",
            category="schedule",
            title="🎵 {{stage_name}}",
            body="NOW: {{current_artist}}\nNEXT: {{next_artist}} ({{next_time}})",
            footer="",
            background_color="#1E1E1E",
            text_color="#FFFFFF",
            icon="🎵",
            audio_enabled=False,
            priority=30,
            variables=["stage_name", "current_artist", "next_artist", "next_time"]
        ),
        Template(
            name="Starting Soon",
            category="schedule",
            title="⏰ STARTING SOON",
            body="{{artist_name}} at {{stage_name}}",
            footer="Starting in {{countdown}}",
            background_color="#FFD700",
            text_color="#000000",
            icon="⏰",
            audio_enabled=True,
            audio_message="{{artist_name}} starting soon at {{stage_name}}.",
            audio_languages=["en"],
            priority=40,
            variables=["artist_name", "stage_name", "countdown"]
        ),
        
        # Traffic/Parking templates
        Template(
            name="Parking Status",
            category="traffic",
            title="🚗 PARKING",
            body="{{lot_status}}",
            footer="{{parking_recommendation}}",
            background_color="#2E8B57",
            text_color="#FFFFFF",
            icon="🚗",
            audio_enabled=False,
            priority=25,
            variables=["lot_status", "parking_recommendation"]
        ),
        Template(
            name="Exit Guidance",
            category="traffic",
            title="🚗 EXIT INFO",
            body="Recommended exit: {{recommended_exit}}",
            footer="Current wait: {{wait_time}}",
            background_color="#2E8B57",
            text_color="#FFFFFF",
            icon="🚗",
            audio_enabled=False,
            priority=35,
            variables=["recommended_exit", "wait_time"]
        ),
        
        # Wayfinding templates
        Template(
            name="Restrooms",
            category="wayfinding",
            title="🚻 RESTROOMS",
            body="Nearest restrooms: {{direction}}",
            footer="",
            background_color="#4169E1",
            text_color="#FFFFFF",
            icon="🚻",
            audio_enabled=False,
            priority=15
        ),
        Template(
            name="First Aid",
            category="wayfinding",
            title="🏥 FIRST AID",
            body="Medical tent: {{direction}}",
            footer="For emergencies, alert any staff member",
            background_color="#FF0000",
            text_color="#FFFFFF",
            icon="🏥",
            audio_enabled=False,
            priority=20
        ),
        
        # Crowd management templates
        Template(
            name="Crowd Alert",
            category="crowd",
            title="👥 CROWD NOTICE",
            body="This area is crowded. {{alternative_area}} has more space.",
            footer="",
            background_color="#FF8C00",
            text_color="#FFFFFF",
            icon="👥",
            audio_enabled=True,
            audio_message="This area is experiencing high crowd density. {{alternative_area}} currently has more space available.",
            audio_languages=["en", "es"],
            priority=60,
            variables=["alternative_area"]
        ),
        
        # Lost & Found templates
        Template(
            name="Lost Item",
            category="attendee",
            title="🔍 LOST",
            body="{{item_description}}",
            footer="Text FOUND to {{event_number}} if you've seen this",
            background_color="#800080",
            text_color="#FFFFFF",
            icon="🔍",
            audio_enabled=False,
            priority=10,
            variables=["item_description", "event_number"]
        ),
        Template(
            name="Found Item",
            category="attendee",
            title="📦 FOUND",
            body="{{item_description}}",
            footer="Claim at Lost & Found tent",
            background_color="#008080",
            text_color="#FFFFFF",
            icon="📦",
            audio_enabled=False,
            priority=10,
            variables=["item_description"]
        ),
        Template(
            name="Meetup",
            category="attendee",
            title="👋 MEETUP",
            body="{{meetup_message}}",
            footer="",
            background_color="#9370DB",
            text_color="#FFFFFF",
            icon="👋",
            audio_enabled=False,
            priority=5,
            variables=["meetup_message"]
        ),
        
        # Sponsor template
        Template(
            name="Sponsor Message",
            category="sponsor",
            title="{{sponsor_name}}",
            body="{{sponsor_message}}",
            footer="",
            background_color="#FFFFFF",
            text_color="#000000",
            icon="",
            audio_enabled=False,
            priority=5,
            variables=["sponsor_name", "sponsor_message"]
        ),
    ]
    
    for template in default_templates:
        db.add(template)
    
    db.commit()
    print(f"✅ Created {len(default_templates)} default templates")

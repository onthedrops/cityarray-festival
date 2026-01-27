#!/usr/bin/env python3
"""
CITYARRAY Festival Edition - Template Seeder
Loads comprehensive multilingual templates from JSON into database
"""

import json
import os
from pathlib import Path
from database import SessionLocal, engine
from models import Base, Template

# Priority color mapping
CATEGORY_COLORS = {
    "emergency": ("#FF0000", "#FFFFFF"),  # Red bg, white text
    "weather": ("#4B0082", "#FFFFFF"),     # Indigo bg, white text
    "crowd": ("#FF8C00", "#FFFFFF"),       # Dark orange bg, white text
    "schedule": ("#1E1E1E", "#FFFFFF"),    # Dark bg, white text
    "wayfinding": ("#4169E1", "#FFFFFF"),  # Royal blue bg, white text
    "sponsor": ("#FFFFFF", "#000000"),     # White bg, black text
    "attendee": ("#9370DB", "#FFFFFF"),    # Purple bg, white text
    "general": ("#2E8B57", "#FFFFFF"),     # Sea green bg, white text
}

def load_templates_from_json(json_path: str = None) -> list:
    """Load templates from JSON file"""
    if json_path is None:
        json_path = Path(__file__).parent / "templates_data.json"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('templates', [])

def seed_templates(clear_existing: bool = True):
    """Seed templates into database"""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        if clear_existing:
            # Clear existing templates
            deleted = db.query(Template).delete()
            print(f"🗑️  Cleared {deleted} existing templates")
            db.commit()
        
        # Load templates from JSON
        templates_data = load_templates_from_json()
        print(f"📄 Loaded {len(templates_data)} templates from JSON")
        
        # Insert templates
        created = 0
        for tpl_data in templates_data:
            # Get colors for category
            bg_color, text_color = CATEGORY_COLORS.get(
                tpl_data['category'], 
                ("#FFFFFF", "#000000")
            )
            
            # English content goes in body
            content = tpl_data['content']
            english_body = content.get('en', '') if isinstance(content, dict) else str(content)
            
            # Extract icon from the beginning of the message if present
            icon = ""
            if english_body and english_body[0] in "🚨⚠️🏥⚡⛈️🌡️🌧️🚫👥📢⏰❌⏳🚻💧📦🅿️🎯🎁🙏📣🔍🎉🌙":
                icon = english_body[0]
            
            template = Template(
                name=tpl_data['name'],
                category=tpl_data['category'],
                body=english_body,
                audio_message=english_body,  # Same as body for TTS
                background_color=bg_color,
                text_color=text_color,
                icon=icon,
                priority=tpl_data.get('priority', 50),
                audio_enabled=tpl_data.get('audio_enabled', False),
                audio_languages=["en", "es", "fr", "zh", "vi"],
                variables=tpl_data.get('variables', [])
            )
            db.add(template)
            created += 1
        
        db.commit()
        print(f"✅ Created {created} templates")
        
        # Print summary by category
        print("\n📊 Templates by category:")
        categories = {}
        for tpl in templates_data:
            cat = tpl['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            print(f"   {cat}: {count}")
        
        # Print language info
        print("\n🌍 Languages supported: English, Spanish, French, Chinese, Vietnamese")
        print("   (Translations stored in templates_data.json for TTS rendering)")
        
    except Exception as e:
        print(f"❌ Error seeding templates: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_multilingual_content(template_name: str, language: str = 'en') -> str:
    """Get template content in specified language from JSON file"""
    templates_data = load_templates_from_json()
    
    for tpl in templates_data:
        if tpl['name'] == template_name:
            content = tpl.get('content', {})
            if isinstance(content, dict):
                return content.get(language, content.get('en', ''))
            return str(content)
    
    return ""

def render_template_multilingual(template_name: str, language: str = 'en', **variables) -> str:
    """Render template with variable substitution in specified language"""
    content = get_multilingual_content(template_name, language)
    
    # Substitute variables
    for key, value in variables.items():
        content = content.replace(f'{{{key}}}', str(value))
    
    return content

if __name__ == "__main__":
    import sys
    
    print("🎪 CITYARRAY Festival Edition - Template Seeder")
    print("=" * 50)
    
    # Check for --keep flag to preserve existing templates
    clear_existing = "--keep" not in sys.argv
    
    if not clear_existing:
        print("⚠️  Keeping existing templates (--keep flag)")
    
    seed_templates(clear_existing=clear_existing)
    
    print("\n✨ Done! Run the dashboard with: python3 app.py")

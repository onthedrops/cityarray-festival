#!/usr/bin/env python3
"""
CITYARRAY Control System
- PRIMARY CONTROL: Dashboard Console (HTTP API)
- PRIMARY OUTPUT: LED Sign (bilingual)
- OPTIONAL: Voice input/output (console-controlled)
"""
import subprocess
import requests
import time
import json
import threading
from datetime import datetime
from flask import Flask, request, jsonify
import pytz

from sign_formatter import SignFormatter, Translator, PHRASES

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "sign_ip": "192.168.1.239",
    "api_port": 5001,  # Pi API port for dashboard control
    "openweather_key": "fd9375b142b3e1233b7b2aa0160762b5",
    "airnow_key": "098A2695-A585-4D29-BDB9-D4BEFFC0A402",
    "piper_path": "/home/eion88/cityarray/piper/piper",
    "piper_model": "/home/eion88/.local/share/piper/en_US-lessac-medium.onnx",
    "whisper_path": "/home/eion88/cityarray/whisper.cpp",
    "slide_duration": 5,
    "timezone": "America/Los_Angeles",
}

# System state - controlled by dashboard
STATE = {
    "agent": "festival",
    "languages": ["en", "es"],
    "primary_language": "en",
    "audio_enabled": False,
    "voice_input_enabled": False,
    "paused": False,
    "override_message": None,
    "override_until": 0,
}

# ============================================================================
# DATA SERVICE
# ============================================================================

class DataService:
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
    
    def _cached(self, key, fetch, duration=120):
        now = time.time()
        if key in self.cache and now - self.cache_time.get(key, 0) < duration:
            return self.cache[key]
        data = fetch()
        if data:
            self.cache[key] = data
            self.cache_time[key] = now
        return self.cache.get(key)
    
    def weather(self):
        def fetch():
            try:
                r = requests.get(
                    f"https://api.openweathermap.org/data/2.5/weather?lat=34.05&lon=-118.24&appid={CONFIG['openweather_key']}&units=imperial",
                    timeout=5).json()
                return {
                    "temp_f": round(r['main']['temp']),
                    "temp_c": round((r['main']['temp'] - 32) * 5 / 9),
                    "desc": r['weather'][0]['description']
                }
            except:
                return None
        return self._cached("weather", fetch) or {"temp_f": 72, "temp_c": 22, "desc": "clear"}
    
    def air(self):
        def fetch():
            try:
                r = requests.get(
                    f"https://www.airnowapi.org/aq/observation/latLong/current/?format=application/json&latitude=34.05&longitude=-118.24&distance=25&API_KEY={CONFIG['airnow_key']}",
                    timeout=5).json()
                if r:
                    return {"aqi": r[0]['AQI'], "cat": r[0]['Category']['Name']}
            except:
                return None
        return self._cached("air", fetch) or {"aqi": 42, "cat": "Good"}
    
    def time_str(self):
        return datetime.now(pytz.timezone(CONFIG["timezone"])).strftime("%I:%M %p")


# ============================================================================
# AUDIO SERVICE (Console-controlled)
# ============================================================================

class AudioService:
    def speak(self, text):
        """Speak text - only if audio enabled by console"""
        if not STATE["audio_enabled"]:
            return False
        try:
            p = subprocess.Popen(
                [CONFIG["piper_path"], "--model", CONFIG["piper_model"], "--output-raw"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE
            )
            audio, _ = p.communicate(text.encode())
            subprocess.run(["aplay", "-D", "plughw:2,0", "-r", "22050", "-f", "S16_LE", "-c", "1"],
                          input=audio, capture_output=True)
            return True
        except:
            return False
    
    def listen(self, duration=5):
        """Listen for voice - only if voice input enabled by console"""
        if not STATE["voice_input_enabled"]:
            return None
        try:
            subprocess.run([
                "arecord", "-D", "plughw:2,0", "-d", str(duration), "-f", "S16_LE",
                "-r", "16000", "-c", "1", "/tmp/cmd.wav"
            ], capture_output=True)
            result = subprocess.run([
                f"{CONFIG['whisper_path']}/build/bin/whisper-cli",
                "-m", f"{CONFIG['whisper_path']}/models/ggml-tiny.en.bin",
                "-f", "/tmp/cmd.wav", "-l", "en", "--no-timestamps"
            ], capture_output=True, text=True)
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('['):
                    return line
        except:
            pass
        return None


# ============================================================================
# SLIDE GENERATORS (Per Agent)
# ============================================================================

def festival_slides(data, formatter):
    """Generate festival slides with bilingual support"""
    w = data.weather()
    slides = [
        {"line1": data.time_str(), "line2": "MAIN STAGE", "color": "purple"},
        {"line1": "NOW PLAYING", "line2": "DJ SHADOW", "color": "purple"},
        {"line1": "NEXT 8PM", "line2": "GLASS ANIMALS", "color": "purple"},
        {"line1": f"{w['temp_f']}F", "line2": "HYDRATE", "color": "cyan", "icon": None},
        {"icon": "water", "line1": "WATER", "line2": "50M AHEAD", "color": "blue"},
        {"line1": "RESTROOMS", "line2": "GATE B", "color": "cyan", "dir": "right"},
        {"icon": "med", "line1": "FIRST AID", "line2": "GATE B", "color": "red", "dir": "right"},
        {"line1": "FOOD COURT", "line2": "RIGHT", "color": "amber", "dir": "right"},
        {"line1": "EXIT", "line2": "GATE A", "color": "green", "dir": "right"},
        {"line1": "NEED HELP?", "line2": "HEY CITY", "color": "purple"},
    ]
    return slides


def rideshare_slides(data, formatter):
    """Generate rideshare slides with bilingual support"""
    slides = [
        {"line1": "RIDESHARE", "line2": "PICKUP", "color": "yellow"},
        {"line1": "UBER LYFT", "line2": "ZONE B", "color": "yellow", "dir": "right"},
        {"icon": "arrow_r", "line1": "PICKUP", "line2": "ZONE B", "color": "yellow"},
        {"line1": "WAIT TIME", "line2": "5-10 MIN", "color": "amber"},
        {"line1": "VERIFY", "line2": "DRIVER", "color": "green"},
        {"line1": "CHECK CAR", "line2": "AND PLATE", "color": "green"},
        {"line1": "ACCESSIBLE", "line2": "IN APP", "color": "cyan"},
        {"line1": "NEED HELP?", "line2": "HEY CITY", "color": "yellow"},
    ]
    return slides


def city_slides(data, formatter):
    """Generate city slides with bilingual support"""
    w = data.weather()
    a = data.air()
    aqi_color = "green" if a['aqi'] <= 50 else "amber" if a['aqi'] <= 100 else "red"
    slides = [
        {"line1": data.time_str(), "line2": "LOS ANGELES", "color": "cyan"},
        {"line1": f"{w['temp_f']}F/{w['temp_c']}C", "line2": w['desc'][:10].upper(), "color": "cyan"},
        {"line1": f"AQI {a['aqi']}", "line2": a['cat'][:10].upper(), "color": aqi_color},
        {"line1": "METRO", "line2": "ON TIME", "color": "green"},
        {"line1": "CITY HALL", "line2": "OPEN 8-5", "color": "cyan"},
        {"line1": "LIBRARY", "line2": "630 W 5TH", "color": "cyan"},
        {"line1": "NEED HELP?", "line2": "HEY CITY", "color": "cyan"},
    ]
    return slides


def general_slides(data, formatter):
    """Generate general slides with bilingual support"""
    w = data.weather()
    slides = [
        {"line1": data.time_str(), "line2": "CITYARRAY", "color": "green"},
        {"line1": f"{w['temp_f']}F/{w['temp_c']}C", "line2": w['desc'][:10].upper(), "color": "cyan"},
        {"line1": "ASK ME", "line2": "ANYTHING", "color": "green"},
        {"line1": "NEED HELP?", "line2": "HEY CITY", "color": "green"},
    ]
    return slides


AGENTS = {
    "festival": {"color": "purple", "slides": festival_slides},
    "rideshare": {"color": "yellow", "slides": rideshare_slides},
    "city": {"color": "cyan", "slides": city_slides},
    "general": {"color": "green", "slides": general_slides},
}


# ============================================================================
# DISPLAY ENGINE
# ============================================================================

class DisplayEngine(threading.Thread):
    """Background thread that cycles slides"""
    
    def __init__(self):
        super().__init__(daemon=True)
        self.formatter = SignFormatter(CONFIG["sign_ip"])
        self.data = DataService()
        self.audio = AudioService()
        self.running = True
        self.slide_idx = 0
    
    def run(self):
        """Main display loop"""
        while self.running:
            # Check for override message from console
            if STATE["override_message"] and time.time() < STATE["override_until"]:
                self._display_override()
                continue
            
            # Check if paused
            if STATE["paused"]:
                time.sleep(1)
                continue
            
            # Get current agent slides
            agent = STATE["agent"]
            if agent not in AGENTS:
                agent = "festival"
            
            # Update formatter languages
            self.formatter.set_languages(STATE["languages"])
            
            # Generate slides
            slides = AGENTS[agent]["slides"](self.data, self.formatter)
            
            if not slides:
                time.sleep(1)
                continue
            
            # Get current slide
            slide = slides[self.slide_idx % len(slides)]
            
            # Display with icon if present
            icon = slide.get("icon")
            if icon:
                self.formatter.sign.icon(icon, slide.get("color", "green"))
                time.sleep(2)
            
            # Display content
            if "line1" in slide and "line2" in slide:
                # Add direction arrow if specified
                line2 = slide["line2"]
                if slide.get("dir") == "right":
                    line2 = line2[:8] + " >>"
                elif slide.get("dir") == "left":
                    line2 = "<< " + line2[:7]
                
                self.formatter.format_and_display(
                    {"line1": slide["line1"], "line2": line2},
                    color=slide.get("color", "green")
                )
            elif "text" in slide:
                self.formatter.format_and_display(
                    {"text": slide["text"]},
                    color=slide.get("color", "green")
                )
            
            self.slide_idx += 1
            
            # Don't sleep here - formatter handles timing for each language
    
    def _display_override(self):
        """Display console override message"""
        msg = STATE["override_message"]
        self.formatter.format_and_display(
            msg.get("content", {}),
            color=msg.get("color", "cyan"),
            priority=msg.get("priority", "normal"),
            icon=msg.get("icon")
        )
    
    def stop(self):
        self.running = False


# ============================================================================
# FLASK API - Dashboard Control Interface
# ============================================================================

app = Flask(__name__)
display_engine = None


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current system status"""
    return jsonify({
        "agent": STATE["agent"],
        "languages": STATE["languages"],
        "primary_language": STATE["primary_language"],
        "audio_enabled": STATE["audio_enabled"],
        "voice_input_enabled": STATE["voice_input_enabled"],
        "paused": STATE["paused"],
        "sign_ip": CONFIG["sign_ip"],
        "available_agents": list(AGENTS.keys()),
        "available_phrases": len(PHRASES),
    })


@app.route('/api/agent', methods=['POST'])
def set_agent():
    """Switch agent mode"""
    data = request.json
    agent = data.get("agent", "festival")
    if agent in AGENTS:
        STATE["agent"] = agent
        display_engine.slide_idx = 0  # Reset slides
        return jsonify({"success": True, "agent": agent})
    return jsonify({"success": False, "error": "Unknown agent"}), 400


@app.route('/api/languages', methods=['POST'])
def set_languages():
    """Set active languages"""
    data = request.json
    languages = data.get("languages", ["en", "es"])
    primary = data.get("primary", "en")
    STATE["languages"] = languages
    STATE["primary_language"] = primary
    return jsonify({"success": True, "languages": languages, "primary": primary})


@app.route('/api/audio', methods=['POST'])
def set_audio():
    """Enable/disable audio output"""
    data = request.json
    STATE["audio_enabled"] = data.get("enabled", False)
    return jsonify({"success": True, "audio_enabled": STATE["audio_enabled"]})


@app.route('/api/voice', methods=['POST'])
def set_voice():
    """Enable/disable voice input"""
    data = request.json
    STATE["voice_input_enabled"] = data.get("enabled", False)
    return jsonify({"success": True, "voice_input_enabled": STATE["voice_input_enabled"]})


@app.route('/api/pause', methods=['POST'])
def pause_display():
    """Pause/resume slide cycling"""
    data = request.json
    STATE["paused"] = data.get("paused", False)
    return jsonify({"success": True, "paused": STATE["paused"]})


@app.route('/api/message', methods=['POST'])
def send_message():
    """Send message to display"""
    data = request.json
    content = data.get("content", {})
    duration = data.get("duration", 30)  # seconds
    priority = data.get("priority", "normal")
    color = data.get("color", "cyan")
    icon = data.get("icon")
    
    STATE["override_message"] = {
        "content": content,
        "priority": priority,
        "color": color,
        "icon": icon,
    }
    STATE["override_until"] = time.time() + duration
    
    # Speak if audio enabled and priority is alert/emergency
    if STATE["audio_enabled"] and priority in ["alert", "emergency"]:
        text = content.get("text") or content.get("line1", "")
        display_engine.audio.speak(text)
    
    return jsonify({"success": True, "duration": duration})


@app.route('/api/alert', methods=['POST'])
def send_alert():
    """Send alert (scrolling announcement)"""
    data = request.json
    text = data.get("text", "ALERT")
    duration = data.get("duration", 30)
    
    STATE["override_message"] = {
        "content": {"text": text},
        "priority": "alert",
        "color": data.get("color", "amber"),
    }
    STATE["override_until"] = time.time() + duration
    
    if STATE["audio_enabled"]:
        display_engine.audio.speak(text)
    
    return jsonify({"success": True})


@app.route('/api/emergency', methods=['POST'])
def send_emergency():
    """Send emergency alert (flashing)"""
    data = request.json
    text = data.get("text", "EMERGENCY")
    duration = data.get("duration", 60)
    
    STATE["override_message"] = {
        "content": {"text": text},
        "priority": "emergency",
        "color": "red",
    }
    STATE["override_until"] = time.time() + duration
    
    # Emergency always speaks if audio hardware available
    display_engine.audio.speak(f"Emergency. {text}")
    
    return jsonify({"success": True})


@app.route('/api/clear', methods=['POST'])
def clear_override():
    """Clear any override message"""
    STATE["override_message"] = None
    STATE["override_until"] = 0
    return jsonify({"success": True})


@app.route('/api/sign/direct', methods=['POST'])
def direct_sign():
    """Send direct command to sign (bypass formatter)"""
    data = request.json
    mode = data.get("mode", "display")
    
    sign = display_engine.formatter.sign
    
    if mode == "display":
        sign.display(data.get("text", ""), data.get("color", "green"))
    elif mode == "twoline":
        sign.twoline(data.get("line1", ""), data.get("line2", ""), data.get("color", "green"))
    elif mode == "big":
        sign.big(data.get("text", ""), data.get("color", "green"))
    elif mode == "icon":
        sign.icon(data.get("icon", "check"), data.get("color", "green"))
    elif mode == "scroll":
        sign.scroll_h(data.get("text", ""), data.get("color", "cyan"), data.get("dir", "left"))
    elif mode == "flash":
        sign.flash(data.get("text", ""), data.get("color", "red"))
    
    return jsonify({"success": True})


@app.route('/api/phrases', methods=['GET'])
def get_phrases():
    """Get phrase dictionary"""
    return jsonify(PHRASES)


@app.route('/api/translate', methods=['POST'])
def translate():
    """Translate text"""
    data = request.json
    text = data.get("text", "")
    target = data.get("language", "es")
    
    translator = Translator()
    result = translator.translate(text, target)
    
    return jsonify({"original": text, "translated": result, "language": target})


# ============================================================================
# MAIN
# ============================================================================

def main():
    global display_engine
    
    print("=" * 60)
    print("🏙️  CITYARRAY CONTROL SYSTEM")
    print("=" * 60)
    print()
    print(f"Sign IP: {CONFIG['sign_ip']}")
    print(f"API Port: {CONFIG['api_port']}")
    print()
    print("DASHBOARD CONTROL ENDPOINTS:")
    print(f"  GET  /api/status        - Get system status")
    print(f"  POST /api/agent         - Switch agent mode")
    print(f"  POST /api/languages     - Set languages")
    print(f"  POST /api/audio         - Enable/disable audio")
    print(f"  POST /api/voice         - Enable/disable voice input")
    print(f"  POST /api/pause         - Pause/resume display")
    print(f"  POST /api/message       - Send message")
    print(f"  POST /api/alert         - Send alert")
    print(f"  POST /api/emergency     - Send emergency")
    print(f"  POST /api/clear         - Clear override")
    print(f"  POST /api/sign/direct   - Direct sign control")
    print()
    print("=" * 60)
    
    # Start display engine
    display_engine = DisplayEngine()
    display_engine.start()
    print("Display engine started")
    
    # Show startup message
    display_engine.formatter.sign.twoline("CITYARRAY", "ONLINE", "green")
    time.sleep(2)
    
    # Start Flask API
    print(f"Starting API on port {CONFIG['api_port']}...")
    print("=" * 60)
    print()
    
    try:
        app.run(host='0.0.0.0', port=CONFIG['api_port'], threaded=True)
    except KeyboardInterrupt:
        pass
    finally:
        display_engine.stop()
        display_engine.formatter.sign.display("READY", "green")
        print("\nShutdown complete.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
CITYARRAY Proactive Display v5
Usage: python cityarray_proactive.py [agent]
Agents: festival, rideshare, city, general
Ctrl+C to stop
"""
import subprocess
import requests
import time
from datetime import datetime
import pytz
import sys

CONFIG = {
    "sign_ip": "192.168.1.239",
    "piper_path": "/home/eion88/cityarray/piper/piper",
    "piper_model": "/home/eion88/.local/share/piper/en_US-lessac-medium.onnx",
    "openweather_key": "fd9375b142b3e1233b7b2aa0160762b5",
    "airnow_key": "098A2695-A585-4D29-BDB9-D4BEFFC0A402",
    "slide_duration": 5,
}

# ============================================================================
# SIGN
# ============================================================================

def sign_post(endpoint, data):
    try:
        requests.post(f"http://{CONFIG['sign_ip']}{endpoint}", json=data, timeout=2)
    except:
        pass

def sign_twoline(l1, l2, color):
    sign_post("/twoline", {"line1": l1[:10], "line2": l2[:10], "color": color})

def sign_icon(name, color):
    sign_post("/icon", {"icon": name, "color": color})

def sign_display(text, color):
    sign_post("/display", {"text": text[:10], "color": color})

# ============================================================================
# DATA
# ============================================================================

weather_cache = None
weather_time = 0
air_cache = None
air_time = 0

def get_weather():
    global weather_cache, weather_time
    if weather_cache and time.time() - weather_time < 120:
        return weather_cache
    try:
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?lat=34.05&lon=-118.24&appid={CONFIG['openweather_key']}&units=imperial",
            timeout=5).json()
        weather_cache = {"f": round(r['main']['temp']), "c": round((r['main']['temp']-32)*5/9), "desc": r['weather'][0]['description']}
        weather_time = time.time()
        return weather_cache
    except:
        return {"f": 72, "c": 22, "desc": "clear"}

def get_air():
    global air_cache, air_time
    if air_cache and time.time() - air_time < 120:
        return air_cache
    try:
        r = requests.get(
            f"https://www.airnowapi.org/aq/observation/latLong/current/?format=application/json&latitude=34.05&longitude=-118.24&distance=25&API_KEY={CONFIG['airnow_key']}",
            timeout=5).json()
        if r:
            air_cache = {"aqi": r[0]['AQI'], "cat": r[0]['Category']['Name']}
            air_time = time.time()
            return air_cache
    except:
        pass
    return {"aqi": 42, "cat": "Good"}

def get_time():
    return datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%I:%M %p")

# ============================================================================
# SLIDES
# ============================================================================

def festival_slides():
    w = get_weather()
    return [
        ("twoline", get_time(), "MAIN STAGE", "purple"),
        ("twoline", "NOW PLAYING", "DJ SHADOW", "purple"),
        ("twoline", "NEXT 8PM", "GLASS ANML", "purple"),
        ("twoline", f"{w['f']}F", "HYDRATE!", "cyan"),
        ("icon", "water", "blue"),
        ("twoline", "WATER", "50M AHEAD", "blue"),
        ("twoline", "RESTROOMS", "GATE B >>", "cyan"),
        ("icon", "med", "red"),
        ("twoline", "FIRST AID", "GATE B >>", "red"),
        ("twoline", "FOOD COURT", "RIGHT >>", "amber"),
        ("twoline", "EXIT", "GATE A >>", "green"),
        ("twoline", "NEED HELP?", "HEY CITY", "purple"),
    ]

def rideshare_slides():
    return [
        ("twoline", "RIDESHARE", "PICKUP", "yellow"),
        ("twoline", "UBER LYFT", "ZONE B >>", "yellow"),
        ("icon", "arrow_r", "yellow"),
        ("twoline", "PICKUP", "ZONE B >>", "yellow"),
        ("twoline", "WAIT TIME", "5-10 MIN", "amber"),
        ("twoline", "VERIFY", "DRIVER", "green"),
        ("twoline", "CHECK CAR", "& PLATE", "green"),
        ("twoline", "ACCESSIBLE", "IN APP", "cyan"),
        ("twoline", "NEED HELP?", "HEY CITY", "yellow"),
    ]

def city_slides():
    w = get_weather()
    a = get_air()
    aqi_color = "green" if a['aqi'] <= 50 else "amber" if a['aqi'] <= 100 else "red"
    return [
        ("twoline", get_time(), "LOS ANGELES", "cyan"),
        ("twoline", f"{w['f']}F/{w['c']}C", w['desc'][:10].upper(), "cyan"),
        ("twoline", f"AQI: {a['aqi']}", a['cat'][:10].upper(), aqi_color),
        ("twoline", "METRO", "ON TIME", "green"),
        ("twoline", "CITY HALL", "OPEN 8-5", "cyan"),
        ("twoline", "LIBRARY", "630 W 5TH", "cyan"),
        ("twoline", "NEED HELP?", "HEY CITY", "cyan"),
    ]

def general_slides():
    w = get_weather()
    return [
        ("twoline", get_time(), "CITYARRAY", "green"),
        ("twoline", f"{w['f']}F/{w['c']}C", w['desc'][:10].upper(), "cyan"),
        ("twoline", "ASK ME", "ANYTHING", "green"),
        ("twoline", "NEED HELP?", "HEY CITY", "green"),
    ]

AGENTS = {
    "festival": {"color": "purple", "slides": festival_slides},
    "rideshare": {"color": "yellow", "slides": rideshare_slides},
    "city": {"color": "cyan", "slides": city_slides},
    "general": {"color": "green", "slides": general_slides},
}

# ============================================================================
# MAIN
# ============================================================================

def main():
    # Get agent from command line
    agent = sys.argv[1] if len(sys.argv) > 1 else "festival"
    if agent not in AGENTS:
        print(f"Unknown agent: {agent}")
        print(f"Available: {', '.join(AGENTS.keys())}")
        sys.exit(1)
    
    print("=" * 50)
    print(f"🏙️  CITYARRAY - {agent.upper()} MODE")
    print("=" * 50)
    print(f"Sign: {CONFIG['sign_ip']}")
    print(f"Slide duration: {CONFIG['slide_duration']}s")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 50)
    print()
    
    # Announce
    color = AGENTS[agent]["color"]
    sign_twoline(agent.upper(), "MODE ON", color)
    
    # Speak announcement
    try:
        p = subprocess.Popen(
            [CONFIG["piper_path"], "--model", CONFIG["piper_model"], "--output-raw"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        audio, _ = p.communicate(f"{agent} mode active.".encode())
        subprocess.run(["aplay", "-D", "plughw:2,0", "-r", "22050", "-f", "S16_LE", "-c", "1"],
                      input=audio, capture_output=True)
    except:
        pass
    
    time.sleep(2)
    
    slide_idx = 0
    
    try:
        while True:
            slides = AGENTS[agent]["slides"]()
            slide = slides[slide_idx % len(slides)]
            
            # Display slide
            if slide[0] == "twoline":
                sign_twoline(slide[1], slide[2], slide[3])
            elif slide[0] == "icon":
                sign_icon(slide[1], slide[2])
            
            # Print status
            num = slide_idx % len(slides) + 1
            total = len(slides)
            info = slide[1] if len(slide) > 1 else slide[0]
            print(f"📺 Slide {num}/{total}: {info}")
            
            slide_idx += 1
            time.sleep(CONFIG["slide_duration"])
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
        sign_display("READY", "green")
        print("Done.")


if __name__ == "__main__":
    main()

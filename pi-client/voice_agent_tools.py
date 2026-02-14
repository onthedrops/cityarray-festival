#!/usr/bin/env python3
"""
CITYARRAY Voice Agent with Tools
- Weather via OpenWeatherMap
- Air Quality via AirNow
- Time via Python
- AI via Ollama
"""
import subprocess
import requests
import os
from datetime import datetime
import pytz

WHISPER_PATH = os.path.expanduser("~/cityarray/whisper.cpp")
PIPER_PATH = os.path.expanduser("~/cityarray/piper/piper")
PIPER_MODEL = os.path.expanduser("~/.local/share/piper/en_US-lessac-medium.onnx")

# API Keys
OPENWEATHER_API_KEY = "fd9375b142b3e1233b7b2aa0160762b5"
AIRNOW_API_KEY = "098A2695-A585-4D29-BDB9-D4BEFFC0A402"

# Common city coordinates
CITIES = {
    "los angeles": {"lat": 34.05, "lon": -118.24, "tz": "America/Los_Angeles"},
    "la": {"lat": 34.05, "lon": -118.24, "tz": "America/Los_Angeles"},
    "new york": {"lat": 40.71, "lon": -74.01, "tz": "America/New_York"},
    "nyc": {"lat": 40.71, "lon": -74.01, "tz": "America/New_York"},
    "tokyo": {"lat": 35.68, "lon": 139.69, "tz": "Asia/Tokyo"},
    "london": {"lat": 51.51, "lon": -0.13, "tz": "Europe/London"},
    "paris": {"lat": 48.86, "lon": 2.35, "tz": "Europe/Paris"},
    "berlin": {"lat": 52.52, "lon": 13.40, "tz": "Europe/Berlin"},
    "sydney": {"lat": -33.87, "lon": 151.21, "tz": "Australia/Sydney"},
    "beijing": {"lat": 39.90, "lon": 116.41, "tz": "Asia/Shanghai"},
    "seoul": {"lat": 37.57, "lon": 126.98, "tz": "Asia/Seoul"},
    "dubai": {"lat": 25.20, "lon": 55.27, "tz": "Asia/Dubai"},
    "san francisco": {"lat": 37.77, "lon": -122.42, "tz": "America/Los_Angeles"},
    "sf": {"lat": 37.77, "lon": -122.42, "tz": "America/Los_Angeles"},
    "chicago": {"lat": 41.88, "lon": -87.63, "tz": "America/Chicago"},
    "miami": {"lat": 25.76, "lon": -80.19, "tz": "America/New_York"},
    "denver": {"lat": 39.74, "lon": -104.99, "tz": "America/Denver"},
    "seattle": {"lat": 47.61, "lon": -122.33, "tz": "America/Los_Angeles"},
    "austin": {"lat": 30.27, "lon": -97.74, "tz": "America/Chicago"},
    "moscow": {"lat": 55.76, "lon": 37.62, "tz": "Europe/Moscow"},
    "amsterdam": {"lat": 52.37, "lon": 4.90, "tz": "Europe/Amsterdam"},
    "glasgow": {"lat": 55.86, "lon": -4.25, "tz": "Europe/London"},
    "edinburgh": {"lat": 55.95, "lon": -3.19, "tz": "Europe/London"},
    "madrid": {"lat": 40.42, "lon": -3.70, "tz": "Europe/Madrid"},
    "rome": {"lat": 41.90, "lon": 12.50, "tz": "Europe/Rome"},
    "mumbai": {"lat": 19.08, "lon": 72.88, "tz": "Asia/Kolkata"},
    "delhi": {"lat": 28.61, "lon": 77.21, "tz": "Asia/Kolkata"},
    "singapore": {"lat": 1.35, "lon": 103.82, "tz": "Asia/Singapore"},
    "hong kong": {"lat": 22.32, "lon": 114.17, "tz": "Asia/Hong_Kong"},
    "bangkok": {"lat": 13.76, "lon": 100.50, "tz": "Asia/Bangkok"},
    "cairo": {"lat": 30.04, "lon": 31.24, "tz": "Africa/Cairo"},
    "toronto": {"lat": 43.65, "lon": -79.38, "tz": "America/Toronto"},
    "vancouver": {"lat": 49.28, "lon": -123.12, "tz": "America/Vancouver"},
    "mexico city": {"lat": 19.43, "lon": -99.13, "tz": "America/Mexico_City"},
    "sao paulo": {"lat": -23.55, "lon": -46.63, "tz": "America/Sao_Paulo"},
    "buenos aires": {"lat": -34.60, "lon": -58.38, "tz": "America/Argentina/Buenos_Aires"},
    "johannesburg": {"lat": -26.20, "lon": 28.04, "tz": "Africa/Johannesburg"},
    "lagos": {"lat": 6.52, "lon": 3.38, "tz": "Africa/Lagos"},
    "istanbul": {"lat": 41.01, "lon": 28.98, "tz": "Europe/Istanbul"},
    "athens": {"lat": 37.98, "lon": 23.73, "tz": "Europe/Athens"},
    "vienna": {"lat": 48.21, "lon": 16.37, "tz": "Europe/Vienna"},
    "zurich": {"lat": 47.37, "lon": 8.54, "tz": "Europe/Zurich"},
    "brussels": {"lat": 50.85, "lon": 4.35, "tz": "Europe/Brussels"},
    "stockholm": {"lat": 59.33, "lon": 18.07, "tz": "Europe/Stockholm"},
    "oslo": {"lat": 59.91, "lon": 10.75, "tz": "Europe/Oslo"},
    "copenhagen": {"lat": 55.68, "lon": 12.57, "tz": "Europe/Copenhagen"},
    "helsinki": {"lat": 60.17, "lon": 24.94, "tz": "Europe/Helsinki"},
    "warsaw": {"lat": 52.23, "lon": 21.01, "tz": "Europe/Warsaw"},
    "prague": {"lat": 50.08, "lon": 14.44, "tz": "Europe/Prague"},
    "budapest": {"lat": 47.50, "lon": 19.04, "tz": "Europe/Budapest"},
    "lisbon": {"lat": 38.72, "lon": -9.14, "tz": "Europe/Lisbon"},
    "dublin": {"lat": 53.35, "lon": -6.26, "tz": "Europe/Dublin"},
    "manchester": {"lat": 53.48, "lon": -2.24, "tz": "Europe/London"},
    "birmingham": {"lat": 52.49, "lon": -1.90, "tz": "Europe/London"},
    "moscow": {"lat": 55.76, "lon": 37.62, "tz": "Europe/Moscow"},
    "here": {"lat": 34.05, "lon": -118.24, "tz": "America/Los_Angeles"},  # Default to LA
}

def get_weather(city):
    """Get weather for a city"""
    city_lower = city.lower().strip()
    city_info = CITIES.get(city_lower)
    
    if city_info:
        lat, lon = city_info["lat"], city_info["lon"]
    else:
        # Try geocoding
        try:
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}"
            geo_resp = requests.get(geo_url, timeout=5).json()
            if geo_resp:
                lat, lon = geo_resp[0]["lat"], geo_resp[0]["lon"]
            else:
                return f"I couldn't find {city}."
        except:
            return f"I couldn't find {city}."
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=imperial"
        resp = requests.get(url, timeout=5).json()
        
        temp = round(resp["main"]["temp"])
        feels = round(resp["main"]["feels_like"])
        desc = resp["weather"][0]["description"]
        humidity = resp["main"]["humidity"]
        
        return f"In {city.title()}, it's {temp}°F and {desc}. Feels like {feels}°F with {humidity}% humidity."
    except Exception as e:
        return f"Couldn't get weather: {e}"

def get_air_quality(city):
    """Get air quality for a city"""
    city_lower = city.lower().strip()
    city_info = CITIES.get(city_lower)
    
    if city_info:
        lat, lon = city_info["lat"], city_info["lon"]
    else:
        return "I don't have air quality data for that location."
    
    try:
        url = f"https://www.airnowapi.org/aq/observation/latLong/current/?format=application/json&latitude={lat}&longitude={lon}&distance=25&API_KEY={AIRNOW_API_KEY}"
        resp = requests.get(url, timeout=5).json()
        
        if resp:
            aqi = resp[0]["AQI"]
            category = resp[0]["Category"]["Name"]
            pollutant = resp[0].get("ParameterName", "PM2.5")
            return f"Air quality in {city.title()} is {category} with an AQI of {aqi}. Main pollutant: {pollutant}."
        else:
            return f"No air quality data available for {city.title()}."
    except Exception as e:
        return f"Couldn't get air quality: {e}"

def get_time(city):
    """Get current time for a city"""
    city_lower = city.lower().strip()
    city_info = CITIES.get(city_lower)
    
    if city_info:
        tz_name = city_info["tz"]
    else:
        # Try common timezone mappings
        tz_map = {
            "japan": "Asia/Tokyo",
            "korea": "Asia/Seoul", 
            "china": "Asia/Shanghai",
            "uk": "Europe/London",
            "france": "Europe/Paris",
            "germany": "Europe/Berlin",
            "australia": "Australia/Sydney",
        }
        tz_name = tz_map.get(city_lower, None)
        if not tz_name:
            return f"I don't know the timezone for {city}."
    
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%A, %B %d")
        return f"In {city.title()}, it's {time_str} on {date_str}."
    except:
        return f"Couldn't get time for {city}."

def detect_intent(text):
    """Simple intent detection"""
    text_lower = text.lower()
    
    # Weather
    if any(w in text_lower for w in ["weather", "temperature", "hot", "cold", "rain", "sunny", "forecast"]):
        return "weather"
    
    # Air quality
    if any(w in text_lower for w in ["air quality", "air", "pollution", "aqi", "smog"]):
        return "air"
    
    # Time
    if any(w in text_lower for w in ["time", "clock", "hour", "what time"]):
        return "time"
    
    return "chat"

def extract_city(text):
    """Extract city from text"""
    text_lower = text.lower()
    
    for city in CITIES.keys():
        if city in text_lower:
            return city
    
    # Common patterns
    patterns = ["in ", "for ", "at "]
    for p in patterns:
        if p in text_lower:
            idx = text_lower.find(p) + len(p)
            remaining = text_lower[idx:].strip()
            # Take first word/phrase
            city = remaining.split("?")[0].split(".")[0].strip()
            return city if city else None
    
    return None

def think(prompt):
    """Query Ollama for general chat"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:3b",
                "prompt": f"You are a helpful festival assistant. Be brief (1-2 sentences). User: {prompt}",
                "stream": False
            },
            timeout=30
        )
        return response.json().get("response", "I'm not sure about that.")
    except:
        return "I'm having trouble thinking right now."

def listen(duration=5):
    """Record and transcribe"""
    wav_file = "/tmp/voice_input.wav"
    
    subprocess.run([
        "arecord", "-D", "plughw:2,0", "-d", str(duration), "-f", "S16_LE", 
        "-r", "16000", "-c", "1", wav_file
    ], capture_output=True)
    
    result = subprocess.run([
        f"{WHISPER_PATH}/build/bin/whisper-cli",
        "-m", f"{WHISPER_PATH}/models/ggml-tiny.en.bin",
        "-f", wav_file,
        "-l", "en",
        "--no-timestamps"
    ], capture_output=True, text=True)
    
    text = ""
    for line in result.stdout.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('[') and not line.startswith('whisper'):
            text = line
            break
    return text

def speak(text):
    """Speak via Piper"""
    try:
        process = subprocess.Popen(
            [PIPER_PATH, "--model", PIPER_MODEL, "--output-raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        audio_data, _ = process.communicate(text.encode())
        subprocess.run(
            ["aplay", "-D", "plughw:2,0", "-r", "22050", "-f", "S16_LE", "-c", "1"],
            input=audio_data,
            capture_output=True
        )
    except Exception as e:
        print(f"Speech error: {e}")

def process_query(text):
    """Process query with tool use"""
    intent = detect_intent(text)
    city = extract_city(text)
    
    print(f"  [Intent: {intent}, City: {city}]")
    
    if intent == "weather":
        if city:
            return get_weather(city)
        else:
            return get_weather("here")
    
    elif intent == "air":
        if city:
            return get_air_quality(city)
        else:
            return get_air_quality("here")
    
    elif intent == "time":
        if city:
            return get_time(city)
        else:
            return get_time("here")
    
    else:
        return think(text)

def main():
    print("=" * 50)
    print("🎤 CITYARRAY Voice Agent with Tools")
    print("=" * 50)
    print("I can help with:")
    print("  🌤️  Weather - 'What's the weather in Tokyo?'")
    print("  💨  Air Quality - 'How's the air in LA?'")
    print("  🕐  Time - 'What time is it in London?'")
    print("  💬  General questions")
    print("\nSay 'exit' to quit\n")
    
    # Warm up
    print("Loading AI model...")
    think("hello")
    print("Ready!\n")
    
    while True:
        print("🎤 Listening... (5 seconds)")
        user_input = listen(5)
        
        if not user_input:
            print("  (no speech detected)\n")
            continue
        
        print(f"You: {user_input}")
        
        if any(word in user_input.lower() for word in ["exit", "quit", "stop"]):
            speak("Goodbye!")
            print("👋 Goodbye!")
            break
        
        response = process_query(user_input)
        print(f"AI: {response}")
        speak(response)
        print()

if __name__ == "__main__":
    main()

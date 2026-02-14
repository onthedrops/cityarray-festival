#!/usr/bin/env python3
import threading, queue, subprocess, requests, os, numpy as np, time, pickle, wave, struct
from datetime import datetime
import pytz
from collections import deque

CONFIG = {
    "dashboard_host": "192.168.1.80", "dashboard_port": 8000, "sign_zone": "Main Stage",
    "whisper_path": os.path.expanduser("~/cityarray/whisper.cpp"),
    "piper_path": os.path.expanduser("~/cityarray/piper/piper"),
    "piper_model": os.path.expanduser("~/.local/share/piper/en_US-lessac-medium.onnx"),
    "wake_model": os.path.expanduser("~/cityarray/wake_word_training/hey_city_model.pkl"),
    "openweather_key": "fd9375b142b3e1233b7b2aa0160762b5",
    "airnow_key": "098A2695-A585-4D29-BDB9-D4BEFFC0A402",
    "camera_enabled": False, "voice_enabled": True, "wake_threshold": 0.45,
}

CITIES = {
    "los angeles": {"lat": 34.05, "lon": -118.24, "tz": "America/Los_Angeles"},
    "la": {"lat": 34.05, "lon": -118.24, "tz": "America/Los_Angeles"},
    "new york": {"lat": 40.71, "lon": -74.01, "tz": "America/New_York"},
    "nyc": {"lat": 40.71, "lon": -74.01, "tz": "America/New_York"},
    "tokyo": {"lat": 35.68, "lon": 139.69, "tz": "Asia/Tokyo"},
    "london": {"lat": 51.51, "lon": -0.13, "tz": "Europe/London"},
    "paris": {"lat": 48.86, "lon": 2.35, "tz": "Europe/Paris"},
    "berlin": {"lat": 52.52, "lon": 13.40, "tz": "Europe/Berlin"},
    "moscow": {"lat": 55.76, "lon": 37.62, "tz": "Europe/Moscow"},
    "amsterdam": {"lat": 52.37, "lon": 4.90, "tz": "Europe/Amsterdam"},
    "glasgow": {"lat": 55.86, "lon": -4.25, "tz": "Europe/London"},
    "sydney": {"lat": -33.87, "lon": 151.21, "tz": "Australia/Sydney"},
    "singapore": {"lat": 1.35, "lon": 103.82, "tz": "Asia/Singapore"},
    "dubai": {"lat": 25.20, "lon": 55.27, "tz": "Asia/Dubai"},
    "toronto": {"lat": 43.65, "lon": -79.38, "tz": "America/Toronto"},
    "chicago": {"lat": 41.88, "lon": -87.63, "tz": "America/Chicago"},
    "miami": {"lat": 25.76, "lon": -80.19, "tz": "America/New_York"},
    "seattle": {"lat": 47.61, "lon": -122.33, "tz": "America/Los_Angeles"},
    "san francisco": {"lat": 37.77, "lon": -122.42, "tz": "America/Los_Angeles"},
    "sf": {"lat": 37.77, "lon": -122.42, "tz": "America/Los_Angeles"},
    "hong kong": {"lat": 22.32, "lon": 114.17, "tz": "Asia/Hong_Kong"},
    "mumbai": {"lat": 19.08, "lon": 72.88, "tz": "Asia/Kolkata"},
    "here": {"lat": 34.05, "lon": -118.24, "tz": "America/Los_Angeles"}}

msg_queue = queue.Queue()

class Speech:
    def __init__(self): self.lock = threading.Lock()
    def speak(self, text):
        with self.lock:
            try:
                p = subprocess.Popen([CONFIG["piper_path"], "--model", CONFIG["piper_model"], "--output-raw"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                audio, _ = p.communicate(text.encode())
                subprocess.run(["aplay", "-D", "plughw:2,0", "-r", "22050", "-f", "S16_LE", "-c", "1"], input=audio, capture_output=True)
            except: pass

speech = Speech()

class AI:
    def think(self, prompt):
        try:
            r = requests.post("http://localhost:11434/api/generate", json={"model": "llama3.2:3b", "prompt": f"You are a helpful festival assistant. Be concise but complete (1-2 sentences). User: {prompt}", "stream": False}, timeout=30)
            return r.json().get("response", "Not sure.")
        except: return "Trouble thinking."

ai = AI()

def get_weather(city):
    info = CITIES.get(city.lower(), CITIES["here"])
    try:
        r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={info['lat']}&lon={info['lon']}&appid={CONFIG['openweather_key']}&units=imperial", timeout=5).json()
        temp_f = round(r['main']['temp'])
        temp_c = round((temp_f - 32) * 5 / 9)
        feels_f = round(r['main']['feels_like'])
        feels_c = round((feels_f - 32) * 5 / 9)
        desc = r['weather'][0]['description']
        humidity = r['main']['humidity']
        return f"In {city.title()}, it's {temp_f} fahrenheit, {temp_c} celsius, and {desc}. Feels like {feels_f} fahrenheit, {feels_c} celsius, with {humidity}% humidity."
    except: return "Can't get weather."

def get_air(city):
    info = CITIES.get(city.lower())
    if not info: return "No air data for that location."
    try:
        r = requests.get(f"https://www.airnowapi.org/aq/observation/latLong/current/?format=application/json&latitude={info['lat']}&longitude={info['lon']}&distance=25&API_KEY={CONFIG['airnow_key']}", timeout=5).json()
        if r: return f"Air quality in {city.title()} is {r[0]['Category']['Name']} with AQI {r[0]['AQI']}."
        return "No air data available."
    except: return "Can't get air quality."

def get_time(city):
    info = CITIES.get(city.lower())
    if not info: return f"Unknown timezone: {city}"
    return f"{city.title()}: {datetime.now(pytz.timezone(info['tz'])).strftime('%I:%M %p')}."

class VoiceAgent(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True
        try:
            with open(CONFIG["wake_model"], 'rb') as f: d = pickle.load(f)
            self.wake_mean, self.wake_std = d['mean'], d['std']
        except: self.wake_mean = None
    
    def detect_wake(self, samples):
        if self.wake_mean is None: return False
        e = [np.sqrt(np.mean(samples[i:i+1600]**2)) for i in range(0, len(samples)-1600, 1600)]
        if len(e) < 10: return False
        return max(0, 1 - np.mean(np.abs(np.array(e[:10]) - self.wake_mean) / self.wake_std) / 5) > CONFIG["wake_threshold"]
    
    def listen(self):
        subprocess.run(["arecord", "-D", "plughw:2,0", "-d", "5", "-f", "S16_LE", "-r", "16000", "-c", "1", "/tmp/cmd.wav"], capture_output=True)
        r = subprocess.run([f"{CONFIG['whisper_path']}/build/bin/whisper-cli", "-m", f"{CONFIG['whisper_path']}/models/ggml-tiny.en.bin", "-f", "/tmp/cmd.wav", "-l", "en", "--no-timestamps"], capture_output=True, text=True)
        for l in r.stdout.split("\n"):
            l = l.strip()
            if l and not l.startswith('[') and not l.startswith('whisper'): return l
        return ""
    
    def process(self, text):
        t = text.lower()
        city = next((c for c in CITIES if c in t), "here")
        if any(w in t for w in ["weather", "temperature", "hot", "cold"]): return get_weather(city)
        if any(w in t for w in ["time", "clock", "hour"]): return get_time(city)
        if any(w in t for w in ["air", "pollution", "aqi", "quality"]): return get_air(city)
        return ai.think(text)
    
    def run(self):
        print("[Voice] Ready - say Hey City")
        ai.think("hi")
        while self.running:
            subprocess.run(["arecord", "-D", "plughw:2,0", "-d", "2", "-f", "S16_LE", "-r", "16000", "-c", "1", "/tmp/wake.wav"], capture_output=True)
            try:
                with wave.open("/tmp/wake.wav", 'rb') as w:
                    samples = np.array(struct.unpack(f'{w.getnframes()}h', w.readframes(w.getnframes())), dtype=np.float32) / 32768.0
            except: continue
            if self.detect_wake(samples):
                print("[Voice] Wake detected!")
                speech.speak("Yes?")
                cmd = self.listen()
                if cmd:
                    print(f"You: {cmd}")
                    resp = self.process(cmd)
                    print(f"AI: {resp}")
                    speech.speak(resp)

if __name__ == "__main__":
    print("CITYARRAY Master - Ctrl+C to stop")
    v = VoiceAgent()
    v.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Bye")
        v.running = False

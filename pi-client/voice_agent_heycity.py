#!/usr/bin/env python3
"""
CITYARRAY Voice Agent - "Hey City" wake word
"""
import subprocess
import requests
import os
import numpy as np
import time
import pickle
import wave
import struct
from datetime import datetime
import pytz

WHISPER_PATH = os.path.expanduser("~/cityarray/whisper.cpp")
PIPER_PATH = os.path.expanduser("~/cityarray/piper/piper")
PIPER_MODEL = os.path.expanduser("~/.local/share/piper/en_US-lessac-medium.onnx")
WAKE_MODEL = os.path.expanduser("~/cityarray/wake_word_training/hey_city_model.pkl")

OPENWEATHER_API_KEY = "fd9375b142b3e1233b7b2aa0160762b5"
AIRNOW_API_KEY = "098A2695-A585-4D29-BDB9-D4BEFFC0A402"

CITIES = {
    "los angeles": {"lat": 34.05, "lon": -118.24, "tz": "America/Los_Angeles"},
    "la": {"lat": 34.05, "lon": -118.24, "tz": "America/Los_Angeles"},
    "new york": {"lat": 40.71, "lon": -74.01, "tz": "America/New_York"},
    "tokyo": {"lat": 35.68, "lon": 139.69, "tz": "Asia/Tokyo"},
    "london": {"lat": 51.51, "lon": -0.13, "tz": "Europe/London"},
    "paris": {"lat": 48.86, "lon": 2.35, "tz": "Europe/Paris"},
    "moscow": {"lat": 55.76, "lon": 37.62, "tz": "Europe/Moscow"},
    "amsterdam": {"lat": 52.37, "lon": 4.90, "tz": "Europe/Amsterdam"},
    "glasgow": {"lat": 55.86, "lon": -4.25, "tz": "Europe/London"},
    "sydney": {"lat": -33.87, "lon": 151.21, "tz": "Australia/Sydney"},
    "singapore": {"lat": 1.35, "lon": 103.82, "tz": "Asia/Singapore"},
    "dubai": {"lat": 25.20, "lon": 55.27, "tz": "Asia/Dubai"},
    "toronto": {"lat": 43.65, "lon": -79.38, "tz": "America/Toronto"},
    "here": {"lat": 34.05, "lon": -118.24, "tz": "America/Los_Angeles"},
}

class HeyCityDetector:
    def __init__(self, model_path):
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
        self.mean = data['mean']
        self.std = data['std']
        self.threshold = 0.45
    
    def extract_features(self, samples):
        chunk_size = 1600
        energies = []
        for i in range(0, len(samples) - chunk_size, chunk_size):
            chunk = samples[i:i+chunk_size]
            energies.append(np.sqrt(np.mean(chunk**2)))
        return np.array(energies[:10]) if len(energies) >= 10 else None
    
    def predict(self, samples):
        features = self.extract_features(samples)
        if features is None:
            return 0.0
        distance = np.mean(np.abs(features - self.mean) / self.std)
        return max(0, 1 - distance / 5)

class VoiceAgent:
    def __init__(self):
        print("=" * 50)
        print("🏙️  CITYARRAY Voice Agent")
        print("=" * 50)
        
        print("Loading wake word model...")
        self.detector = HeyCityDetector(WAKE_MODEL)
        print("✅ Wake word: 'Hey City'")
        
        print("Loading AI model...")
        self.think("hello")
        print("✅ Ready!\n")
        print("=" * 50)
        print("Say 'Hey City' to activate")
        print("=" * 50 + "\n")
    
    def listen_for_wake(self):
        """Listen continuously for wake word"""
        print("👂 Listening for 'Hey City'...", end="", flush=True)
        
        while True:
            # Record 2 second chunks
            subprocess.run([
                "arecord", "-D", "plughw:2,0", "-d", "2", "-f", "S16_LE",
                "-r", "16000", "-c", "1", "/tmp/wake_check.wav"
            ], capture_output=True)
            
            # Read audio
            try:
                with wave.open("/tmp/wake_check.wav", 'rb') as wf:
                    frames = wf.readframes(wf.getnframes())
                    samples = np.array(struct.unpack(f'{len(frames)//2}h', frames), dtype=np.float32)
                    samples = samples / 32768.0
            except:
                continue
            
            # Check wake word
            score = self.detector.predict(samples)
            
            if score > self.detector.threshold:
                print(f"\n🔔 'Hey City' detected! (score: {score:.2f})")
                return True
            else:
                print(".", end="", flush=True)
    
    def listen_command(self, duration=5):
        """Record command after wake word"""
        self.play_tone()
        print(f"🎤 Listening ({duration}s)...")
        
        subprocess.run([
            "arecord", "-D", "plughw:2,0", "-d", str(duration), "-f", "S16_LE",
            "-r", "16000", "-c", "1", "/tmp/command.wav"
        ], capture_output=True)
        
        result = subprocess.run([
            f"{WHISPER_PATH}/build/bin/whisper-cli",
            "-m", f"{WHISPER_PATH}/models/ggml-tiny.en.bin",
            "-f", "/tmp/command.wav", "-l", "en", "--no-timestamps"
        ], capture_output=True, text=True)
        
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('[') and not line.startswith('whisper'):
                return line
        return ""
    
    def play_tone(self):
        """Acknowledgment beep"""
        subprocess.run(
            'echo "Listening" | ' + PIPER_PATH + ' --model ' + PIPER_MODEL + 
            ' --output-raw | aplay -D plughw:2,0 -r 22050 -f S16_LE -c 1',
            shell=True, capture_output=True
        )
    
    def speak(self, text):
        try:
            process = subprocess.Popen(
                [PIPER_PATH, "--model", PIPER_MODEL, "--output-raw"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE
            )
            audio, _ = process.communicate(text.encode())
            subprocess.run(
                ["aplay", "-D", "plughw:2,0", "-r", "22050", "-f", "S16_LE", "-c", "1"],
                input=audio, capture_output=True
            )
        except Exception as e:
            print(f"Speech error: {e}")
    
    def think(self, prompt):
        try:
            r = requests.post("http://localhost:11434/api/generate", json={
                "model": "llama3.2:3b",
                "prompt": f"Be brief (1-2 sentences). User: {prompt}",
                "stream": False
            }, timeout=30)
            return r.json().get("response", "I'm not sure.")
        except:
            return "I'm having trouble."
    
    def get_weather(self, city):
        info = CITIES.get(city.lower().strip())
        if info:
            lat, lon = info["lat"], info["lon"]
        else:
            try:
                r = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}", timeout=5).json()
                if r:
                    lat, lon = r[0]["lat"], r[0]["lon"]
                else:
                    return f"Can't find {city}."
            except:
                return f"Can't find {city}."
        
        try:
            r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=imperial", timeout=5).json()
            return f"In {city.title()}, it's {round(r['main']['temp'])}°F and {r['weather'][0]['description']}."
        except:
            return f"Can't get weather."
    
    def get_time(self, city):
        info = CITIES.get(city.lower().strip())
        if not info:
            return f"Don't know timezone for {city}."
        try:
            tz = pytz.timezone(info["tz"])
            now = datetime.now(tz)
            return f"In {city.title()}, it's {now.strftime('%I:%M %p')}."
        except:
            return f"Can't get time."
    
    def get_air(self, city):
        info = CITIES.get(city.lower().strip())
        if not info:
            return "No air data for that location."
        try:
            r = requests.get(f"https://www.airnowapi.org/aq/observation/latLong/current/?format=application/json&latitude={info['lat']}&longitude={info['lon']}&distance=25&API_KEY={AIRNOW_API_KEY}", timeout=5).json()
            if r:
                return f"Air quality in {city.title()} is {r[0]['Category']['Name']} with AQI {r[0]['AQI']}."
            return "No air data available."
        except:
            return "Can't get air quality."
    
    def process(self, text):
        t = text.lower()
        city = None
        for c in CITIES:
            if c in t:
                city = c
                break
        if not city:
            for p in ["in ", "for "]:
                if p in t:
                    city = t.split(p)[1].split("?")[0].split(".")[0].strip()
                    break
        
        if any(w in t for w in ["weather", "temperature", "hot", "cold"]):
            return self.get_weather(city or "here")
        if any(w in t for w in ["time", "clock"]):
            return self.get_time(city or "here")
        if any(w in t for w in ["air", "pollution", "aqi"]):
            return self.get_air(city or "here")
        return self.think(text)
    
    def run(self):
        try:
            while True:
                if self.listen_for_wake():
                    cmd = self.listen_command(5)
                    if not cmd:
                        self.speak("I didn't catch that.")
                        continue
                    
                    print(f"You: {cmd}")
                    
                    if any(w in cmd.lower() for w in ["exit", "quit", "stop"]):
                        self.speak("Goodbye!")
                        break
                    
                    response = self.process(cmd)
                    print(f"AI: {response}")
                    self.speak(response)
                    print()
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")

if __name__ == "__main__":
    agent = VoiceAgent()
    agent.run()

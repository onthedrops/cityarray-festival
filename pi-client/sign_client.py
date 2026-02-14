#!/usr/bin/env python3
"""
CITYARRAY Sign Client - Connects Dashboard to Physical LED Sign
With Bilingual Support (EN/ES)
"""

import asyncio
import json
import websockets
import requests
import subprocess
import time
from datetime import datetime

# Configuration
DASHBOARD_HOST = "192.168.1.80"
DASHBOARD_PORT = 8000
SIGN_IP = "192.168.1.239"
SIGN_NAME = "Main Stage Sign"
SIGN_ZONE = "Main Stage"
PIPER_PATH = "/home/eion88/cityarray/piper/piper"
PIPER_MODEL = "/home/eion88/.local/share/piper/en_US-lessac-medium.onnx"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Display settings
LANGUAGES = ["en", "es"]
SLIDE_DURATION = 5  # seconds per language

# ============================================================================
# PHRASE DICTIONARY (Extended ~100 phrases)
# ============================================================================

PHRASES = {
    # === WAYFINDING ===
    "WATER": "AGUA",
    "WATER STATION": "ESTACIÓN DE AGUA",
    "RESTROOMS": "BAÑOS",
    "BATHROOMS": "BAÑOS",
    "EXIT": "SALIDA",
    "ENTRANCE": "ENTRADA",
    "FIRST AID": "PRIMEROS AUXILIOS",
    "MEDICAL": "MÉDICO",
    "FOOD": "COMIDA",
    "FOOD COURT": "ÁREA DE COMIDA",
    "DRINKS": "BEBIDAS",
    "BAR": "BAR",
    "ATM": "CAJERO",
    "INFO": "INFORMACIÓN",
    "INFO BOOTH": "PUNTO DE INFORMACIÓN",
    "LOST AND FOUND": "OBJETOS PERDIDOS",
    "PARKING": "ESTACIONAMIENTO",
    "TICKETS": "BOLETOS",
    "VIP": "VIP",
    "MERCH": "MERCANCÍA",
    "MERCHANDISE": "MERCANCÍA",
    
    # === DIRECTIONS ===
    "LEFT": "IZQUIERDA",
    "RIGHT": "DERECHA",
    "AHEAD": "ADELANTE",
    "BEHIND": "ATRÁS",
    "STRAIGHT": "RECTO",
    "NORTH": "NORTE",
    "SOUTH": "SUR",
    "EAST": "ESTE",
    "WEST": "OESTE",
    "UP": "ARRIBA",
    "DOWN": "ABAJO",
    "NEAR": "CERCA",
    "FAR": "LEJOS",
    "HERE": "AQUÍ",
    "THERE": "ALLÍ",
    "THIS WAY": "POR AQUÍ",
    "FOLLOW": "SIGA",
    
    # === DISTANCES ===
    "METERS": "METROS",
    "BLOCKS": "CUADRAS",
    "MINUTES": "MINUTOS",
    "HOURS": "HORAS",
    
    # === STATUS ===
    "OPEN": "ABIERTO",
    "CLOSED": "CERRADO",
    "FULL": "LLENO",
    "AVAILABLE": "DISPONIBLE",
    "WAIT": "ESPERE",
    "READY": "LISTO",
    "LOADING": "CARGANDO",
    "PLEASE WAIT": "POR FAVOR ESPERE",
    "SOLD OUT": "AGOTADO",
    "FREE": "GRATIS",
    "BUSY": "OCUPADO",
    "CONNECTED": "CONECTADO",
    "CONNECTING": "CONECTANDO",
    "DASHBOARD": "TABLERO",
    
    # === ALERTS ===
    "EMERGENCY": "EMERGENCIA",
    "DANGER": "PELIGRO",
    "WARNING": "ADVERTENCIA",
    "CAUTION": "PRECAUCIÓN",
    "EVACUATE": "EVACUAR",
    "SHELTER": "REFUGIO",
    "CALL 911": "LLAME 911",
    "STAY CALM": "MANTENGA CALMA",
    "MOVE BACK": "RETROCEDA",
    "CLEAR AREA": "DESPEJE ÁREA",
    "DO NOT ENTER": "NO ENTRE",
    "STOP": "ALTO",
    "ALERT": "ALERTA",
    "ALL CLEAR": "TODO BIEN",
    "SAFE": "SEGURO",
    
    # === WEATHER ===
    "HOT": "CALIENTE",
    "COLD": "FRÍO",
    "RAIN": "LLUVIA",
    "SUNNY": "SOLEADO",
    "CLOUDY": "NUBLADO",
    "WINDY": "VENTOSO",
    "HYDRATE": "HIDRÁTESE",
    "STAY COOL": "MANTÉNGASE FRESCO",
    "SEEK SHADE": "BUSQUE SOMBRA",
    "LIGHTNING": "RELÁMPAGO",
    
    # === FESTIVAL ===
    "MAIN STAGE": "ESCENARIO PRINCIPAL",
    "STAGE": "ESCENARIO",
    "NOW PLAYING": "AHORA TOCANDO",
    "NEXT": "SIGUIENTE",
    "LINEUP": "PROGRAMA",
    "SCHEDULE": "HORARIO",
    "SHOW STARTS": "SHOW COMIENZA",
    "DOORS OPEN": "PUERTAS ABREN",
    "LAST CALL": "ÚLTIMA LLAMADA",
    "ENCORE": "ENCORE",
    
    # === RIDESHARE ===
    "PICKUP": "RECOGIDA",
    "PICKUP ZONE": "ZONA DE RECOGIDA",
    "DROP OFF": "BAJADA",
    "RIDESHARE": "VIAJE COMPARTIDO",
    "WAIT TIME": "TIEMPO DE ESPERA",
    "YOUR DRIVER": "SU CONDUCTOR",
    "VERIFY": "VERIFIQUE",
    "CHECK CAR": "REVISE AUTO",
    "CHECK PLATE": "REVISE PLACA",
    "ACCESSIBLE": "ACCESIBLE",
    "WHEELCHAIR": "SILLA DE RUEDAS",
    
    # === CITY ===
    "METRO": "METRO",
    "BUS": "AUTOBÚS",
    "TRAIN": "TREN",
    "STATION": "ESTACIÓN",
    "TRANSIT": "TRANSPORTE",
    "CITY HALL": "AYUNTAMIENTO",
    "LIBRARY": "BIBLIOTECA",
    "MUSEUM": "MUSEO",
    "PARK": "PARQUE",
    "HOSPITAL": "HOSPITAL",
    "POLICE": "POLICÍA",
    "FIRE DEPT": "BOMBEROS",
    
    # === COMMON ===
    "YES": "SÍ",
    "NO": "NO",
    "HELP": "AYUDA",
    "NEED HELP": "NECESITA AYUDA",
    "ASK ME": "PREGÚNTEME",
    "WELCOME": "BIENVENIDOS",
    "THANK YOU": "GRACIAS",
    "SORRY": "DISCULPE",
    "GOODBYE": "ADIÓS",
    "HELLO": "HOLA",
    "HEY CITY": "HEY CITY",
}


class Translator:
    """Translates text using dictionary + Ollama fallback"""
    
    def translate(self, text, target="es"):
        """Translate text to target language"""
        if target == "en":
            return text
        
        upper = text.upper().strip()
        
        # Try exact match
        if upper in PHRASES:
            return PHRASES[upper]
        
        # Try word-by-word for short phrases
        words = upper.split()
        if len(words) <= 4:
            translated = []
            all_found = True
            for word in words:
                clean = word.strip(".,!?")
                if clean in PHRASES:
                    translated.append(PHRASES[clean])
                else:
                    translated.append(word)
                    if clean.isalpha():
                        all_found = False
            if all_found or len(words) <= 2:
                return " ".join(translated)
        
        # Ollama fallback for unknown text
        return self._ollama_translate(text, target)
    
    def _ollama_translate(self, text, target):
        """Use Ollama for translation"""
        lang_name = {"es": "Spanish", "vi": "Vietnamese", "zh": "Chinese"}.get(target, target)
        try:
            r = requests.post(OLLAMA_URL, json={
                "model": "llama3.2:3b",
                "prompt": f"Translate to {lang_name}. Reply ONLY with the translation, no explanation: {text}",
                "stream": False
            }, timeout=10)
            result = r.json().get("response", "").strip()
            # Clean up
            result = result.strip('"\'').split('\n')[0]
            print(f"🌐 Translated: '{text}' → '{result}'")
            return result if result else text
        except Exception as e:
            print(f"⚠️ Translation error: {e}")
            return text


class SignClient:
    def __init__(self):
        self.sign_id = None
        self.ws = None
        self.connected = False
        self.translator = Translator()
        self.bilingual_enabled = True
        
    def send_to_sign(self, endpoint, data):
        """Send command to physical LED sign"""
        try:
            url = f"http://{SIGN_IP}{endpoint}"
            resp = requests.post(url, json=data, timeout=2)
            return resp.ok
        except Exception as e:
            print(f"❌ Sign error: {e}")
            return False
    
    def sign_display(self, text, color="green"):
        self.send_to_sign("/display", {"text": text[:10], "color": color})
    
    def sign_twoline(self, line1, line2, color="green"):
        self.send_to_sign("/twoline", {"line1": line1[:10], "line2": line2[:10], "color": color})
    
    def sign_big(self, text, color="green"):
        self.send_to_sign("/big", {"text": text[:5], "color": color})
    
    def sign_scroll(self, text, color="cyan", direction="left"):
        self.send_to_sign("/scroll", {"text": f"   {text}   ", "color": color, "dir": direction})
    
    def sign_flash(self, text, color="red"):
        self.send_to_sign("/flash", {"text": text[:10], "color": color})
    
    def sign_icon(self, icon, color="green"):
        self.send_to_sign("/icon", {"icon": icon, "color": color})
    
    def sign_clear(self):
        self.send_to_sign("/display", {"text": "READY", "color": "green"})
    
    def display_bilingual(self, line1, line2, color="cyan", scroll_if_long=True):
        """Display message in English then Spanish"""
        for lang in LANGUAGES:
            if lang == "en":
                t1, t2 = line1, line2
            else:
                t1 = self.translator.translate(line1, lang)
                t2 = self.translator.translate(line2, lang) if line2 else ""
            
            print(f"📺 [{lang.upper()}] {t1} / {t2}")
            
            # Check if needs scroll
            if len(t1) > 10 or len(t2) > 10:
                if scroll_if_long:
                    combined = f"{t1} - {t2}" if t2 else t1
                    self.sign_scroll(combined, color)
                else:
                    # Truncate
                    self.sign_twoline(t1[:10], t2[:10], color)
            else:
                if t2:
                    self.sign_twoline(t1, t2, color)
                elif len(t1) <= 5:
                    self.sign_big(t1, color)
                else:
                    self.sign_display(t1, color)
            
            time.sleep(SLIDE_DURATION)
    
    def display_bilingual_scroll(self, text, color="cyan"):
        """Scroll message in English then Spanish"""
        for lang in LANGUAGES:
            if lang == "en":
                t = text
            else:
                t = self.translator.translate(text, lang)
            
            print(f"📜 [{lang.upper()}] {t}")
            self.sign_scroll(t, color)
            time.sleep(SLIDE_DURATION + 3)  # Extra time for scroll
    
    def display_bilingual_flash(self, text, color="red"):
        """Flash message in English then Spanish"""
        for lang in LANGUAGES:
            if lang == "en":
                t = text
            else:
                t = self.translator.translate(text, lang)
            
            print(f"⚡ [{lang.upper()}] {t}")
            self.sign_flash(t[:10], color)
            time.sleep(SLIDE_DURATION)
        
    async def register(self):
        """Register this sign with the dashboard"""
        url = f"http://{DASHBOARD_HOST}:{DASHBOARD_PORT}/api/signs"
        data = {
            "name": SIGN_NAME,
            "display_type": "led",
            "has_camera": True,
            "has_speaker": True,
            "has_microphone": True
        }
        try:
            resp = requests.post(url, json=data, params={"zone": SIGN_ZONE})
            if resp.ok:
                result = resp.json()
                self.sign_id = result["id"]
                print(f"✅ Registered as: {self.sign_id}")
                return True
            else:
                print(f"❌ Registration failed: {resp.text}")
        except Exception as e:
            print(f"❌ Cannot reach dashboard: {e}")
        return False
    
    async def connect(self):
        """Connect to dashboard WebSocket"""
        if not self.sign_id:
            if not await self.register():
                return
        
        uri = f"ws://{DASHBOARD_HOST}:{DASHBOARD_PORT}/ws/sign/{self.sign_id}"
        print(f"🔌 Connecting to {uri}")
        
        self.sign_twoline("CONNECTING", "DASHBOARD", "cyan")
        
        while True:
            try:
                async with websockets.connect(uri) as ws:
                    self.ws = ws
                    self.connected = True
                    print("✅ Connected to dashboard!")
                    self.sign_twoline("CONNECTED", "READY", "green")
                    
                    heartbeat_task = asyncio.create_task(self.heartbeat())
                    
                    async for message in ws:
                        await self.handle_message(json.loads(message))
                    
            except websockets.exceptions.ConnectionClosed:
                print("🔌 Connection closed, reconnecting...")
                self.sign_twoline("RECONNECT", "WAIT...", "amber")
            except Exception as e:
                print(f"❌ Connection error: {e}")
                self.sign_twoline("ERROR", "RETRY...", "red")
            
            self.connected = False
            await asyncio.sleep(5)
    
    async def heartbeat(self):
        """Send periodic heartbeat"""
        while self.connected:
            try:
                await self.ws.send(json.dumps({
                    "type": "heartbeat",
                    "data": {
                        "battery": 100,
                        "signal_strength": 95,
                        "bilingual": self.bilingual_enabled,
                        "languages": LANGUAGES
                    }
                }))
            except:
                pass
            await asyncio.sleep(5)
    
    async def handle_message(self, data):
        """Handle incoming message from dashboard"""
        msg_type = data.get("type")
        print(f"📨 Received: {msg_type}")
        
        if msg_type == "new_message":
            await self.display_message(data.get("data", {}))
        elif msg_type == "clear_message":
            self.sign_clear()
        elif msg_type == "display":
            d = data.get("data", {})
            if self.bilingual_enabled:
                self.display_bilingual(d.get("text", ""), "", d.get("color", "green"))
            else:
                self.sign_display(d.get("text", ""), d.get("color", "green"))
        elif msg_type == "twoline":
            d = data.get("data", {})
            if self.bilingual_enabled:
                self.display_bilingual(d.get("line1", ""), d.get("line2", ""), d.get("color", "green"))
            else:
                self.sign_twoline(d.get("line1", ""), d.get("line2", ""), d.get("color", "green"))
        elif msg_type == "scroll":
            d = data.get("data", {})
            if self.bilingual_enabled:
                self.display_bilingual_scroll(d.get("text", ""), d.get("color", "cyan"))
            else:
                self.sign_scroll(d.get("text", ""), d.get("color", "cyan"), d.get("dir", "left"))
        elif msg_type == "flash":
            d = data.get("data", {})
            if self.bilingual_enabled:
                self.display_bilingual_flash(d.get("text", "ALERT"), d.get("color", "red"))
            else:
                self.sign_flash(d.get("text", "ALERT"), d.get("color", "red"))
        elif msg_type == "icon":
            d = data.get("data", {})
            self.sign_icon(d.get("icon", "check"), d.get("color", "green"))
        elif msg_type == "set_bilingual":
            self.bilingual_enabled = data.get("enabled", True)
            print(f"🌐 Bilingual: {self.bilingual_enabled}")
    
    async def display_message(self, message):
        """Display message on LED with bilingual support"""
        content = message.get("content", "")
        priority = message.get("priority", 0)
        color = message.get("color", "cyan")
        
        print(f"📺 DISPLAY: {content} (Priority: {priority})")
        
        if priority >= 90:
            # Emergency - flash bilingual
            self.display_bilingual_flash(content[:10], "red")
        elif priority >= 70:
            # Alert - scroll bilingual
            self.display_bilingual_scroll(content, "amber")
        elif len(content) <= 21 and " " in content:
            # Try two lines
            words = content.split()
            mid = len(words) // 2 or 1
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])
            self.display_bilingual(line1, line2, color)
        else:
            self.display_bilingual(content, "", color)
        
        # TTS if audio enabled
        if message.get("audio_enabled"):
            await self.speak(content)
        
        # Acknowledge
        if self.ws:
            await self.ws.send(json.dumps({
                "type": "ack",
                "message_id": message.get("id")
            }))
    
    async def speak(self, text):
        """Text-to-speech using Piper"""
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
            print(f"🔊 Spoke: {text}")
        except Exception as e:
            print(f"⚠️ TTS error: {e}")


async def main():
    print("=" * 60)
    print("🎪 CITYARRAY Sign Client - Bilingual")
    print("=" * 60)
    print(f"   Dashboard: {DASHBOARD_HOST}:{DASHBOARD_PORT}")
    print(f"   LED Sign:  {SIGN_IP}")
    print(f"   Zone:      {SIGN_ZONE}")
    print(f"   Languages: {', '.join(LANGUAGES)}")
    print("=" * 60)
    print()
    
    client = SignClient()
    
    # Test sign connection
    print("Testing sign connection...")
    if client.send_to_sign("/display", {"text": "STARTING", "color": "cyan"}):
        print("✅ Sign connected!")
    else:
        print("⚠️ Sign not responding")
    
    # Test translation
    print("\nTesting translation...")
    print(f"  WATER → {client.translator.translate('WATER', 'es')}")
    print(f"  FIRST AID → {client.translator.translate('FIRST AID', 'es')}")
    print(f"  EVACUATE → {client.translator.translate('EVACUATE', 'es')}")
    print()
    
    await client.connect()

if __name__ == "__main__":
    asyncio.run(main())

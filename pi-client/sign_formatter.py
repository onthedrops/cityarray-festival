#!/usr/bin/env python3
"""
CITYARRAY Sign Formatter
- Bilingual support (EN/ES base, expandable)
- Auto-selects best display mode for content
- Handles translation with dictionary + LLM fallback
"""
import requests
import time
import re

CONFIG = {
    "sign_ip": "192.168.1.239",
    "slide_duration": 5,
    "languages": ["en", "es"],  # Base languages
    "primary_language": "en",
}

# ============================================================================
# EXTENDED PHRASE DICTIONARY (~100 phrases)
# ============================================================================

PHRASES = {
    # === WAYFINDING ===
    "WATER": {"es": "AGUA"},
    "WATER STATION": {"es": "ESTACIÓN DE AGUA"},
    "RESTROOMS": {"es": "BAÑOS"},
    "BATHROOMS": {"es": "BAÑOS"},
    "EXIT": {"es": "SALIDA"},
    "ENTRANCE": {"es": "ENTRADA"},
    "FIRST AID": {"es": "PRIMEROS AUXILIOS"},
    "MEDICAL": {"es": "MÉDICO"},
    "FOOD": {"es": "COMIDA"},
    "FOOD COURT": {"es": "ÁREA DE COMIDA"},
    "DRINKS": {"es": "BEBIDAS"},
    "BAR": {"es": "BAR"},
    "ATM": {"es": "CAJERO"},
    "INFO": {"es": "INFORMACIÓN"},
    "INFO BOOTH": {"es": "PUNTO DE INFORMACIÓN"},
    "LOST AND FOUND": {"es": "OBJETOS PERDIDOS"},
    "PARKING": {"es": "ESTACIONAMIENTO"},
    "TICKETS": {"es": "BOLETOS"},
    "VIP": {"es": "VIP"},
    "MERCH": {"es": "MERCANCÍA"},
    "MERCHANDISE": {"es": "MERCANCÍA"},
    
    # === DIRECTIONS ===
    "LEFT": {"es": "IZQUIERDA"},
    "RIGHT": {"es": "DERECHA"},
    "AHEAD": {"es": "ADELANTE"},
    "BEHIND": {"es": "ATRÁS"},
    "STRAIGHT": {"es": "RECTO"},
    "NORTH": {"es": "NORTE"},
    "SOUTH": {"es": "SUR"},
    "EAST": {"es": "ESTE"},
    "WEST": {"es": "OESTE"},
    "UP": {"es": "ARRIBA"},
    "DOWN": {"es": "ABAJO"},
    "NEAR": {"es": "CERCA"},
    "FAR": {"es": "LEJOS"},
    "HERE": {"es": "AQUÍ"},
    "THERE": {"es": "ALLÍ"},
    "THIS WAY": {"es": "POR AQUÍ"},
    "FOLLOW": {"es": "SIGA"},
    
    # === DISTANCES ===
    "METERS": {"es": "METROS"},
    "BLOCKS": {"es": "CUADRAS"},
    "MINUTES": {"es": "MINUTOS"},
    "HOURS": {"es": "HORAS"},
    
    # === STATUS ===
    "OPEN": {"es": "ABIERTO"},
    "CLOSED": {"es": "CERRADO"},
    "FULL": {"es": "LLENO"},
    "AVAILABLE": {"es": "DISPONIBLE"},
    "WAIT": {"es": "ESPERE"},
    "READY": {"es": "LISTO"},
    "LOADING": {"es": "CARGANDO"},
    "PLEASE WAIT": {"es": "POR FAVOR ESPERE"},
    "SOLD OUT": {"es": "AGOTADO"},
    "FREE": {"es": "GRATIS"},
    "BUSY": {"es": "OCUPADO"},
    
    # === ALERTS ===
    "EMERGENCY": {"es": "EMERGENCIA"},
    "DANGER": {"es": "PELIGRO"},
    "WARNING": {"es": "ADVERTENCIA"},
    "CAUTION": {"es": "PRECAUCIÓN"},
    "EVACUATE": {"es": "EVACUAR"},
    "SHELTER": {"es": "REFUGIO"},
    "CALL 911": {"es": "LLAME 911"},
    "STAY CALM": {"es": "MANTENGA CALMA"},
    "MOVE BACK": {"es": "RETROCEDA"},
    "CLEAR AREA": {"es": "DESPEJE ÁREA"},
    "DO NOT ENTER": {"es": "NO ENTRE"},
    "STOP": {"es": "ALTO"},
    
    # === WEATHER ===
    "HOT": {"es": "CALIENTE"},
    "COLD": {"es": "FRÍO"},
    "RAIN": {"es": "LLUVIA"},
    "SUNNY": {"es": "SOLEADO"},
    "CLOUDY": {"es": "NUBLADO"},
    "WINDY": {"es": "VENTOSO"},
    "HYDRATE": {"es": "HIDRÁTESE"},
    "STAY COOL": {"es": "MANTÉNGASE FRESCO"},
    "SEEK SHADE": {"es": "BUSQUE SOMBRA"},
    "LIGHTNING": {"es": "RELÁMPAGO"},
    
    # === FESTIVAL ===
    "MAIN STAGE": {"es": "ESCENARIO PRINCIPAL"},
    "STAGE": {"es": "ESCENARIO"},
    "NOW PLAYING": {"es": "AHORA TOCANDO"},
    "NEXT": {"es": "SIGUIENTE"},
    "LINEUP": {"es": "PROGRAMA"},
    "SCHEDULE": {"es": "HORARIO"},
    "SHOW STARTS": {"es": "SHOW COMIENZA"},
    "DOORS OPEN": {"es": "PUERTAS ABREN"},
    "LAST CALL": {"es": "ÚLTIMA LLAMADA"},
    "ENCORE": {"es": "ENCORE"},
    
    # === RIDESHARE ===
    "PICKUP": {"es": "RECOGIDA"},
    "PICKUP ZONE": {"es": "ZONA DE RECOGIDA"},
    "DROP OFF": {"es": "BAJADA"},
    "RIDESHARE": {"es": "VIAJE COMPARTIDO"},
    "WAIT TIME": {"es": "TIEMPO DE ESPERA"},
    "YOUR DRIVER": {"es": "SU CONDUCTOR"},
    "VERIFY": {"es": "VERIFIQUE"},
    "CHECK CAR": {"es": "REVISE AUTO"},
    "CHECK PLATE": {"es": "REVISE PLACA"},
    "ACCESSIBLE": {"es": "ACCESIBLE"},
    "WHEELCHAIR": {"es": "SILLA DE RUEDAS"},
    
    # === CITY ===
    "METRO": {"es": "METRO"},
    "BUS": {"es": "AUTOBÚS"},
    "TRAIN": {"es": "TREN"},
    "STATION": {"es": "ESTACIÓN"},
    "TRANSIT": {"es": "TRANSPORTE"},
    "CITY HALL": {"es": "AYUNTAMIENTO"},
    "LIBRARY": {"es": "BIBLIOTECA"},
    "MUSEUM": {"es": "MUSEO"},
    "PARK": {"es": "PARQUE"},
    "HOSPITAL": {"es": "HOSPITAL"},
    "POLICE": {"es": "POLICÍA"},
    "FIRE DEPT": {"es": "BOMBEROS"},
    
    # === COMMON RESPONSES ===
    "YES": {"es": "SÍ"},
    "NO": {"es": "NO"},
    "HELP": {"es": "AYUDA"},
    "NEED HELP": {"es": "NECESITA AYUDA"},
    "ASK ME": {"es": "PREGÚNTEME"},
    "WELCOME": {"es": "BIENVENIDOS"},
    "THANK YOU": {"es": "GRACIAS"},
    "SORRY": {"es": "DISCULPE"},
    "GOODBYE": {"es": "ADIÓS"},
    "HELLO": {"es": "HOLA"},
    "HEY CITY": {"es": "HEY CITY"},
}

# ============================================================================
# SIGN COMMUNICATION
# ============================================================================

class Sign:
    def __init__(self, ip):
        self.url = f"http://{ip}"
    
    def _post(self, endpoint, data):
        try:
            requests.post(f"{self.url}{endpoint}", json=data, timeout=2)
            return True
        except:
            return False
    
    def display(self, text, color="green"):
        """Single line, max 10 chars"""
        self._post("/display", {"text": text[:10], "color": color})
    
    def twoline(self, l1, l2, color="green"):
        """Two lines, max 10 chars each"""
        self._post("/twoline", {"line1": l1[:10], "line2": l2[:10], "color": color})
    
    def big(self, text, color="green"):
        """Large text, max 5 chars"""
        self._post("/big", {"text": text[:5], "color": color})
    
    def icon(self, name, color="green"):
        """Icon display"""
        self._post("/icon", {"icon": name, "color": color})
    
    def scroll_h(self, text, color="cyan", direction="left"):
        """Horizontal scroll"""
        self._post("/scroll", {"text": text, "color": color, "dir": direction})
    
    def scroll_v(self, text, color="cyan", direction="up"):
        """Vertical scroll"""
        self._post("/scroll", {"text": text, "color": color, "dir": direction})
    
    def flash(self, text, color="red"):
        """Flashing alert"""
        self._post("/flash", {"text": text[:10], "color": color})


# ============================================================================
# TRANSLATOR
# ============================================================================

class Translator:
    def __init__(self):
        self.phrases = PHRASES
    
    def translate(self, text, target_lang="es"):
        """Translate text, using dictionary first, LLM fallback"""
        if target_lang == "en":
            return text
        
        # Try exact match
        upper = text.upper()
        if upper in self.phrases and target_lang in self.phrases[upper]:
            return self.phrases[upper][target_lang]
        
        # Try word-by-word for short phrases
        words = upper.split()
        if len(words) <= 3:
            translated = []
            for word in words:
                if word in self.phrases and target_lang in self.phrases[word]:
                    translated.append(self.phrases[word][target_lang])
                else:
                    translated.append(word)  # Keep original if not found
            return " ".join(translated)
        
        # LLM fallback for longer/unknown text
        return self._llm_translate(text, target_lang)
    
    def _llm_translate(self, text, target_lang):
        """Use Ollama for translation"""
        lang_name = {"es": "Spanish", "vi": "Vietnamese", "zh": "Chinese"}.get(target_lang, target_lang)
        try:
            r = requests.post("http://localhost:11434/api/generate", json={
                "model": "llama3.2:3b",
                "prompt": f"Translate to {lang_name}. Only respond with the translation, nothing else: {text}",
                "stream": False
            }, timeout=15)
            result = r.json().get("response", "").strip()
            # Clean up any quotes or extra text
            result = result.strip('"\'')
            return result if result else text
        except:
            return text  # Return original if translation fails
    
    def get_languages(self):
        """Get available languages from dictionary"""
        langs = set(["en"])
        for phrase in self.phrases.values():
            langs.update(phrase.keys())
        return sorted(list(langs))


# ============================================================================
# SIGN FORMATTER - Decides best display method
# ============================================================================

class SignFormatter:
    def __init__(self, sign_ip):
        self.sign = Sign(sign_ip)
        self.translator = Translator()
        self.languages = CONFIG["languages"]
        self.primary = CONFIG["primary_language"]
        self.slide_duration = CONFIG["slide_duration"]
    
    def format_and_display(self, message, color="green", priority="normal", icon=None):
        """
        Format message and display on sign in all active languages
        
        Args:
            message: dict with line1, line2 OR text for single line/scroll
            color: display color
            priority: normal, alert, emergency
            icon: optional icon to show before text
        """
        if priority == "emergency":
            self._display_emergency(message, color)
        elif priority == "alert":
            self._display_alert(message, color)
        else:
            self._display_normal(message, color, icon)
    
    def _display_emergency(self, message, color="red"):
        """Flash in all languages"""
        text = message.get("text", message.get("line1", "EMERGENCY"))
        for lang in self.languages:
            translated = self.translator.translate(text, lang)
            # Emergency always flashes
            if len(translated) <= 10:
                self.sign.flash(translated, color)
            else:
                self.sign.flash(translated[:10], color)
            time.sleep(self.slide_duration)
    
    def _display_alert(self, message, color="amber"):
        """Scroll alert in all languages"""
        text = message.get("text", message.get("line1", "ALERT"))
        for lang in self.languages:
            translated = self.translator.translate(text, lang)
            self.sign.scroll_h(f"   {translated}   ", color)
            time.sleep(self.slide_duration)
    
    def _display_normal(self, message, color, icon=None):
        """Display normal message with optimal formatting per language"""
        
        # Show icon first if provided
        if icon:
            self.sign.icon(icon, color)
            time.sleep(2)
        
        # Handle two-line vs single-line
        if "line1" in message and "line2" in message:
            self._display_twoline(message["line1"], message["line2"], color)
        elif "text" in message:
            self._display_single(message["text"], color)
        elif "items" in message:
            self._display_list(message["items"], color)
    
    def _display_twoline(self, line1, line2, color):
        """Display two lines in all languages"""
        for lang in self.languages:
            t1 = self.translator.translate(line1, lang)
            t2 = self.translator.translate(line2, lang)
            
            # Check lengths
            if len(t1) <= 10 and len(t2) <= 10:
                # Fits in twoline
                self.sign.twoline(t1, t2, color)
            elif len(t1) <= 10:
                # Line 1 fits, scroll line 2
                self.sign.display(t1, color)
                time.sleep(2)
                self.sign.scroll_h(f"   {t2}   ", color)
            else:
                # Both need scroll
                self.sign.scroll_h(f"   {t1} - {t2}   ", color)
            
            time.sleep(self.slide_duration)
    
    def _display_single(self, text, color):
        """Display single text in all languages"""
        for lang in self.languages:
            translated = self.translator.translate(text, lang)
            
            if len(translated) <= 5:
                self.sign.big(translated, color)
            elif len(translated) <= 10:
                self.sign.display(translated, color)
            else:
                self.sign.scroll_h(f"   {translated}   ", color)
            
            time.sleep(self.slide_duration)
    
    def _display_list(self, items, color):
        """Display list of items using vertical scroll"""
        for lang in self.languages:
            # Translate all items
            translated = [self.translator.translate(item, lang) for item in items]
            
            # Show each item scrolling up
            for item in translated:
                if len(item) <= 10:
                    self.sign.display(item, color)
                else:
                    self.sign.scroll_h(f"   {item}   ", color)
                time.sleep(2)
            
            time.sleep(1)  # Pause between languages
    
    def set_languages(self, languages):
        """Update active languages"""
        self.languages = languages
    
    def set_primary(self, lang):
        """Set primary language (shown first)"""
        self.primary = lang
        # Reorder languages with primary first
        if lang in self.languages:
            self.languages.remove(lang)
            self.languages.insert(0, lang)


# ============================================================================
# TEST / DEMO
# ============================================================================

def demo():
    """Demo the sign formatter"""
    formatter = SignFormatter(CONFIG["sign_ip"])
    
    print("=" * 50)
    print("CITYARRAY Sign Formatter Demo")
    print(f"Languages: {formatter.languages}")
    print("=" * 50)
    
    # Test 1: Simple two-line (fits)
    print("\n1. Two-line (fits in both languages)")
    formatter.format_and_display({
        "line1": "WATER",
        "line2": "50M AHEAD"
    }, color="blue", icon="water")
    
    # Test 2: Two-line (Spanish scrolls)
    print("\n2. Two-line (Spanish needs scroll)")
    formatter.format_and_display({
        "line1": "FIRST AID",
        "line2": "GATE B"
    }, color="red", icon="med")
    
    # Test 3: Single short text
    print("\n3. Single short text (BIG)")
    formatter.format_and_display({
        "text": "STOP"
    }, color="red")
    
    # Test 4: Single long text
    print("\n4. Single long text (scroll)")
    formatter.format_and_display({
        "text": "WELCOME TO THE FESTIVAL"
    }, color="purple")
    
    # Test 5: List (vertical)
    print("\n5. List display")
    formatter.format_and_display({
        "items": ["WATER", "FOOD", "EXIT", "HELP"]
    }, color="cyan")
    
    # Test 6: Emergency
    print("\n6. Emergency alert")
    formatter.format_and_display({
        "text": "EVACUATE"
    }, color="red", priority="emergency")
    
    # Test 7: Alert
    print("\n7. Alert message")
    formatter.format_and_display({
        "text": "SHOW STARTS IN 5 MINUTES"
    }, color="amber", priority="alert")
    
    print("\n" + "=" * 50)
    print("Demo complete!")
    formatter.sign.display("READY", "green")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        print("Usage: python sign_formatter.py demo")
        print("\nOr import and use:")
        print("  from sign_formatter import SignFormatter")
        print("  formatter = SignFormatter('192.168.1.239')")
        print("  formatter.format_and_display({'line1': 'WATER', 'line2': '50M'}, color='blue')")

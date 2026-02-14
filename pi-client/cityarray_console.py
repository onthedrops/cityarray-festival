#!/usr/bin/env python3
"""
CITYARRAY Console - Type messages to display and speak
"""
import requests
import subprocess
import sys

CONFIG = {
    "sign_ip": "192.168.1.239",
    "piper_path": "/home/eion88/cityarray/piper/piper",
    "piper_model": "/home/eion88/.local/share/piper/en_US-lessac-medium.onnx",
}

def sign_post(endpoint, data):
    try:
        requests.post(f"http://{CONFIG['sign_ip']}{endpoint}", json=data, timeout=2)
    except:
        print("[SIGN] Connection failed")

def speak(text):
    try:
        p = subprocess.Popen(
            [CONFIG["piper_path"], "--model", CONFIG["piper_model"], "--output-raw"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        audio, _ = p.communicate(text.encode())
        subprocess.run(["aplay", "-D", "plughw:2,0", "-r", "22050", "-f", "S16_LE", "-c", "1"],
                      input=audio, capture_output=True)
    except:
        print("[SPEAK] Audio failed")

def display_message(text, color="cyan"):
    """Auto-format message for sign based on length"""
    text = text.strip()
    
    if len(text) <= 5:
        # Big text
        sign_post("/big", {"text": text.upper(), "color": color})
        print(f"[SIGN BIG] {text.upper()}")
    elif len(text) <= 10:
        # Single line
        sign_post("/display", {"text": text.upper(), "color": color})
        print(f"[SIGN] {text.upper()}")
    elif " " in text and len(text) <= 21:
        # Try two lines
        words = text.split()
        mid = len(words) // 2
        line1 = " ".join(words[:mid]) if mid > 0 else words[0]
        line2 = " ".join(words[mid:]) if mid > 0 else " ".join(words[1:])
        if len(line1) <= 10 and len(line2) <= 10:
            sign_post("/twoline", {"line1": line1.upper(), "line2": line2.upper(), "color": color})
            print(f"[SIGN] {line1.upper()} / {line2.upper()}")
        else:
            # Scroll
            sign_post("/scroll", {"text": f"   {text.upper()}   ", "color": color, "dir": "left"})
            print(f"[SIGN SCROLL] {text.upper()}")
    else:
        # Scroll
        sign_post("/scroll", {"text": f"   {text.upper()}   ", "color": color, "dir": "left"})
        print(f"[SIGN SCROLL] {text.upper()}")

def main():
    print("=" * 50)
    print("🏙️  CITYARRAY CONSOLE")
    print("=" * 50)
    print()
    print("Type a message and press Enter to display + speak")
    print()
    print("Commands:")
    print("  /color red      - Change color")
    print("  /flash TEXT     - Flash message")
    print("  /icon water     - Show icon")
    print("  /sign only      - Sign only (no audio)")
    print("  /audio only     - Audio only (no sign)")
    print("  /both           - Both sign + audio (default)")
    print("  /q              - Quit")
    print()
    print("Colors: red, amber, yellow, green, cyan, blue, purple, white")
    print("Icons: arrow_r, arrow_l, check, x, warn, heart, water, med")
    print()
    print("=" * 50)
    print()
    
    color = "cyan"
    mode = "both"  # both, sign, audio
    
    while True:
        try:
            msg = input(f"[{color}] > ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        
        if not msg:
            continue
        
        # Commands
        if msg.startswith("/"):
            parts = msg.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""
            
            if cmd == "/q" or cmd == "/quit":
                break
            elif cmd == "/color":
                if arg in ["red", "amber", "yellow", "green", "cyan", "blue", "purple", "white"]:
                    color = arg
                    print(f"Color set to {color}")
                else:
                    print("Invalid color")
            elif cmd == "/flash":
                sign_post("/flash", {"text": arg[:10].upper(), "color": color})
                print(f"[FLASH] {arg.upper()}")
                if mode in ["both", "audio"]:
                    speak(arg)
            elif cmd == "/icon":
                sign_post("/icon", {"icon": arg, "color": color})
                print(f"[ICON] {arg}")
            elif cmd == "/sign":
                mode = "sign"
                print("Mode: Sign only")
            elif cmd == "/audio":
                mode = "audio"
                print("Mode: Audio only")
            elif cmd == "/both":
                mode = "both"
                print("Mode: Sign + Audio")
            elif cmd == "/scroll":
                sign_post("/scroll", {"text": f"   {arg.upper()}   ", "color": color, "dir": "left"})
                print(f"[SCROLL] {arg.upper()}")
                if mode in ["both", "audio"]:
                    speak(arg)
            elif cmd == "/up":
                sign_post("/scroll", {"text": f"   {arg.upper()}   ", "color": color, "dir": "up"})
                print(f"[SCROLL UP] {arg.upper()}")
            elif cmd == "/down":
                sign_post("/scroll", {"text": f"   {arg.upper()}   ", "color": color, "dir": "down"})
                print(f"[SCROLL DOWN] {arg.upper()}")
            elif cmd == "/ready":
                sign_post("/display", {"text": "READY", "color": "green"})
                print("[SIGN] READY")
            else:
                print(f"Unknown command: {cmd}")
            continue
        
        # Regular message
        if mode in ["both", "sign"]:
            display_message(msg, color)
        
        if mode in ["both", "audio"]:
            speak(msg)
    
    print("\nGoodbye!")
    sign_post("/display", {"text": "READY", "color": "green"})


if __name__ == "__main__":
    main()

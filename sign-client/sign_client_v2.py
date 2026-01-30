#!/usr/bin/env python3
"""
CITYARRAY Sign Client - Production Version
Features:
- Cellular failover (primary WiFi, fallback cellular)
- Offline mode with cached templates
- Message queue for sync when reconnected
- Local emergency operation
"""

import asyncio
import json
import os
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    subprocess.run(["pip", "install", "websockets"])
    import websockets

try:
    import requests
except ImportError:
    print("Installing requests...")
    subprocess.run(["pip", "install", "requests"])
    import requests

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    # Dashboard connection
    "dashboard_host": "192.168.1.80",  # Local development
    "dashboard_port": 8000,
    "cloud_host": "",  # Future: cloud.cityarray.io
    "cloud_port": 443,
    
    # Sign identity
    "sign_name": "Main Stage Sign",
    "sign_zone": "Main Stage",
    "sign_id_file": "~/.cityarray_sign_id",
    
    # Network interfaces (in priority order)
    "interfaces": ["wlan0", "eth0", "usb0", "ppp0"],  # ppp0 = cellular
    
    # Offline storage
    "cache_dir": "~/.cityarray_cache",
    "message_queue_file": "~/.cityarray_queue.json",
    
    # Timing
    "heartbeat_interval": 5,
    "reconnect_delay": 5,
    "network_check_interval": 30,
}

# Expand paths
CONFIG["sign_id_file"] = os.path.expanduser(CONFIG["sign_id_file"])
CONFIG["cache_dir"] = os.path.expanduser(CONFIG["cache_dir"])
CONFIG["message_queue_file"] = os.path.expanduser(CONFIG["message_queue_file"])


# =============================================================================
# EMERGENCY TEMPLATES (Always available offline)
# =============================================================================

EMERGENCY_TEMPLATES = {
    "evacuate": {
        "content": "⚠️ EVACUATE NOW ⚠️\nFollow exit signs\nStay calm",
        "priority": 100,
        "audio": True,
        "color": "red"
    },
    "shelter": {
        "content": "🏠 SHELTER IN PLACE\nStay indoors\nAwait instructions",
        "priority": 95,
        "audio": True,
        "color": "red"
    },
    "medical": {
        "content": "🚑 MEDICAL EMERGENCY\nClear the area\nHelp is coming",
        "priority": 90,
        "audio": True,
        "color": "red"
    },
    "weather": {
        "content": "⛈️ SEVERE WEATHER\nSeek shelter immediately",
        "priority": 85,
        "audio": True,
        "color": "amber"
    },
    "lost_child": {
        "content": "👶 LOST CHILD ALERT\nCheck information booth",
        "priority": 80,
        "audio": True,
        "color": "amber"
    },
    "all_clear": {
        "content": "✅ ALL CLEAR\nResume normal activities",
        "priority": 50,
        "audio": True,
        "color": "green"
    }
}


# =============================================================================
# NETWORK MANAGER
# =============================================================================

class NetworkManager:
    """Manages network connections with failover"""
    
    def __init__(self):
        self.current_interface = None
        self.is_cellular = False
        
    def check_connectivity(self, host, port):
        """Check if we can reach the dashboard"""
        import socket
        try:
            sock = socket.create_connection((host, port), timeout=5)
            sock.close()
            return True
        except:
            return False
    
    def get_active_interface(self):
        """Detect which network interface is active"""
        try:
            result = subprocess.run(
                ["ip", "route", "get", "8.8.8.8"],
                capture_output=True, text=True, timeout=5
            )
            for iface in CONFIG["interfaces"]:
                if iface in result.stdout:
                    self.current_interface = iface
                    self.is_cellular = iface in ["ppp0", "usb0", "wwan0"]
                    return iface
        except:
            pass
        return None
    
    def get_signal_strength(self):
        """Get cellular signal strength if on cellular"""
        if not self.is_cellular:
            return None
        try:
            # For Sixfab/Waveshare modems
            result = subprocess.run(
                ["mmcli", "-m", "0", "--signal-get"],
                capture_output=True, text=True, timeout=10
            )
            # Parse signal strength from output
            for line in result.stdout.split("\n"):
                if "rssi" in line.lower():
                    return line.strip()
        except:
            pass
        return "unknown"
    
    def enable_cellular(self):
        """Attempt to enable cellular connection"""
        print("📶 Attempting cellular failover...")
        try:
            # For NetworkManager-based systems
            subprocess.run(["nmcli", "con", "up", "cellular"], timeout=30)
            return True
        except:
            pass
        
        try:
            # For ppp-based cellular
            subprocess.run(["pon", "cellular"], timeout=30)
            return True
        except:
            pass
        
        print("⚠️ Cellular failover not configured")
        return False


# =============================================================================
# LOCAL CACHE
# =============================================================================

class LocalCache:
    """Manages offline template cache and message queue"""
    
    def __init__(self):
        os.makedirs(CONFIG["cache_dir"], exist_ok=True)
        self.db_path = os.path.join(CONFIG["cache_dir"], "cache.db")
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite cache database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS templates
                     (id TEXT PRIMARY KEY, name TEXT, content TEXT, 
                      priority INTEGER, category TEXT, data TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS pending_messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      content TEXT, created_at TEXT, sent INTEGER DEFAULT 0)''')
        conn.commit()
        conn.close()
    
    def cache_templates(self, templates):
        """Cache templates from dashboard"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        for t in templates:
            c.execute('''INSERT OR REPLACE INTO templates 
                        (id, name, content, priority, category, data)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (t["id"], t.get("name"), t.get("body", t.get("content")),
                      t.get("priority", 50), t.get("category"), json.dumps(t)))
        conn.commit()
        conn.close()
        print(f"💾 Cached {len(templates)} templates")
    
    def get_template(self, template_id):
        """Get template from cache"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT data FROM templates WHERE id = ?", (template_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return None
    
    def get_emergency_templates(self):
        """Get cached emergency templates"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT data FROM templates WHERE category = 'emergency'")
        rows = c.fetchall()
        conn.close()
        return [json.loads(r[0]) for r in rows]
    
    def queue_message(self, content):
        """Queue a message for later sync"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO pending_messages (content, created_at) VALUES (?, ?)",
                 (content, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
    
    def get_pending_messages(self):
        """Get messages waiting to be synced"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, content FROM pending_messages WHERE sent = 0")
        rows = c.fetchall()
        conn.close()
        return rows
    
    def mark_sent(self, msg_id):
        """Mark a queued message as sent"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE pending_messages SET sent = 1 WHERE id = ?", (msg_id,))
        conn.commit()
        conn.close()


# =============================================================================
# DISPLAY MANAGER
# =============================================================================

class DisplayManager:
    """Manages the LED display via Matrix Portal S3"""
    
    def __init__(self, matrix_portal_ip=None):
        self.matrix_ip = matrix_portal_ip
        self.current_message = None
        self.current_color = "green"
    
    async def display(self, content, priority=50, color=None):
        """Display message on LED panel"""
        self.current_message = content
        
        # Determine color based on priority
        if color:
            self.current_color = color
        elif priority >= 90:
            self.current_color = "red"
        elif priority >= 70:
            self.current_color = "amber"
        else:
            self.current_color = "green"
        
        print(f"📺 DISPLAY [{self.current_color.upper()}]: {content}")
        
        # Send to Matrix Portal if configured
        if self.matrix_ip:
            try:
                requests.post(
                    f"http://{self.matrix_ip}/display",
                    json={"text": content, "color": self.current_color},
                    timeout=5
                )
            except Exception as e:
                print(f"⚠️ Matrix Portal error: {e}")
    
    async def clear(self):
        """Clear the display"""
        self.current_message = None
        print("🧹 Display cleared")
        
        if self.matrix_ip:
            try:
                requests.post(f"http://{self.matrix_ip}/clear", timeout=5)
            except:
                pass


# =============================================================================
# AUDIO MANAGER  
# =============================================================================

class AudioManager:
    """Manages TTS and audio announcements"""
    
    def __init__(self):
        self.tts_engine = self._detect_tts()
    
    def _detect_tts(self):
        """Detect available TTS engine"""
        # Check for piper (best quality)
        try:
            result = subprocess.run(["which", "piper"], capture_output=True)
            if result.returncode == 0:
                return "piper"
        except:
            pass
        
        # Check for espeak (fallback)
        try:
            result = subprocess.run(["which", "espeak"], capture_output=True)
            if result.returncode == 0:
                return "espeak"
        except:
            pass
        
        return None
    
    async def speak(self, text, language="en"):
        """Speak text using TTS"""
        if not self.tts_engine:
            print("⚠️ No TTS engine available")
            return
        
        print(f"🔊 Speaking: {text[:50]}...")
        
        try:
            if self.tts_engine == "piper":
                # Piper TTS (high quality, fast)
                process = subprocess.Popen(
                    ["piper", "--model", f"en_US-lessac-medium", "--output-raw"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE
                )
                audio_data, _ = process.communicate(text.encode())
                # Play with aplay
                subprocess.run(["aplay", "-r", "22050", "-f", "S16_LE", "-"],
                             input=audio_data, capture_output=True)
            else:
                # espeak fallback
                subprocess.run(["espeak", text], capture_output=True, timeout=30)
        except Exception as e:
            print(f"⚠️ TTS error: {e}")


# =============================================================================
# MAIN SIGN CLIENT
# =============================================================================

class SignClient:
    """Main sign client with failover support"""
    
    def __init__(self):
        self.sign_id = self._load_sign_id()
        self.ws = None
        self.connected = False
        self.offline_mode = False
        
        self.network = NetworkManager()
        self.cache = LocalCache()
        self.display = DisplayManager()
        self.audio = AudioManager()
    
    def _load_sign_id(self):
        """Load persisted sign ID"""
        try:
            with open(CONFIG["sign_id_file"], "r") as f:
                return f.read().strip()
        except:
            return None
    
    def _save_sign_id(self, sign_id):
        """Persist sign ID"""
        with open(CONFIG["sign_id_file"], "w") as f:
            f.write(sign_id)
    
    async def register(self):
        """Register with dashboard"""
        host = CONFIG["dashboard_host"]
        port = CONFIG["dashboard_port"]
        
        url = f"http://{host}:{port}/api/signs"
        data = {
            "name": CONFIG["sign_name"],
            "display_type": "led",
            "has_camera": True,
            "has_speaker": True,
            "has_microphone": True
        }
        
        try:
            resp = requests.post(
                url, json=data, 
                params={"zone": CONFIG["sign_zone"]},
                timeout=10
            )
            if resp.ok:
                result = resp.json()
                self.sign_id = result["id"]
                self._save_sign_id(self.sign_id)
                print(f"✅ Registered as: {self.sign_id}")
                
                # Cache templates
                await self._sync_templates()
                return True
            else:
                print(f"❌ Registration failed: {resp.text}")
        except requests.exceptions.ConnectionError:
            print("❌ Cannot reach dashboard - entering offline mode")
            self.offline_mode = True
        except Exception as e:
            print(f"❌ Registration error: {e}")
        
        return False
    
    async def _sync_templates(self):
        """Sync templates from dashboard to local cache"""
        try:
            host = CONFIG["dashboard_host"]
            port = CONFIG["dashboard_port"]
            resp = requests.get(f"http://{host}:{port}/api/templates", timeout=10)
            if resp.ok:
                self.cache.cache_templates(resp.json())
        except Exception as e:
            print(f"⚠️ Template sync failed: {e}")
    
    async def connect(self):
        """Connect to dashboard with failover"""
        # Check if we have a sign ID, if not register
        if not self.sign_id:
            if not await self.register():
                if self.offline_mode:
                    await self.run_offline()
                return
        
        host = CONFIG["dashboard_host"]
        port = CONFIG["dashboard_port"]
        uri = f"ws://{host}:{port}/ws/sign/{self.sign_id}"
        
        retry_count = 0
        max_retries_before_cellular = 3
        
        while True:
            # Check network
            interface = self.network.get_active_interface()
            if interface:
                print(f"📡 Network: {interface}" + 
                      (" (cellular)" if self.network.is_cellular else ""))
            
            try:
                print(f"🔌 Connecting to {uri}")
                async with websockets.connect(uri, ping_interval=20) as ws:
                    self.ws = ws
                    self.connected = True
                    self.offline_mode = False
                    retry_count = 0
                    
                    print("✅ Connected to dashboard!")
                    
                    # Sync any pending messages
                    await self._sync_pending()
                    
                    # Start tasks
                    heartbeat_task = asyncio.create_task(self._heartbeat())
                    network_task = asyncio.create_task(self._monitor_network())
                    
                    # Listen for messages
                    async for message in ws:
                        await self._handle_message(json.loads(message))
                    
            except websockets.exceptions.ConnectionClosed:
                print("🔌 Connection closed")
            except Exception as e:
                print(f"❌ Connection error: {e}")
                retry_count += 1
            
            self.connected = False
            
            # Failover logic
            if retry_count >= max_retries_before_cellular:
                if not self.network.is_cellular:
                    print("🔄 Primary connection failed, trying cellular...")
                    if self.network.enable_cellular():
                        retry_count = 0
                        await asyncio.sleep(10)  # Wait for cellular to connect
                        continue
                    else:
                        print("📴 Entering offline mode")
                        await self.run_offline()
                        return
            
            await asyncio.sleep(CONFIG["reconnect_delay"])
    
    async def _heartbeat(self):
        """Send periodic heartbeat"""
        while self.connected:
            try:
                signal = self.network.get_signal_strength()
                await self.ws.send(json.dumps({
                    "type": "heartbeat",
                    "data": {
                        "battery": 100,  # TODO: Real battery monitoring
                        "signal_strength": 95 if not self.network.is_cellular else 70,
                        "network_type": "cellular" if self.network.is_cellular else "wifi",
                        "cellular_signal": signal,
                        "crowd_count": 0,
                        "crowd_density": 0
                    }
                }))
            except:
                break
            await asyncio.sleep(CONFIG["heartbeat_interval"])
    
    async def _monitor_network(self):
        """Monitor network quality"""
        while self.connected:
            await asyncio.sleep(CONFIG["network_check_interval"])
            interface = self.network.get_active_interface()
            if interface != self.network.current_interface:
                print(f"🔄 Network changed: {interface}")
    
    async def _sync_pending(self):
        """Sync any messages queued while offline"""
        pending = self.cache.get_pending_messages()
        if pending:
            print(f"📤 Syncing {len(pending)} pending messages...")
            for msg_id, content in pending:
                try:
                    # Report to dashboard that we displayed this message
                    await self.ws.send(json.dumps({
                        "type": "offline_message_report",
                        "content": content
                    }))
                    self.cache.mark_sent(msg_id)
                except:
                    break
    
    async def _handle_message(self, data):
        """Handle incoming message"""
        msg_type = data.get("type")
        print(f"📨 Received: {msg_type}")
        
        if msg_type == "new_message":
            await self._display_message(data.get("data", {}))
        elif msg_type == "clear_message":
            await self.display.clear()
        elif msg_type == "emergency":
            await self._handle_emergency(data.get("data", {}))
    
    async def _display_message(self, message):
        """Display a message"""
        content = message.get("content", "")
        priority = message.get("priority", 50)
        
        await self.display.display(content, priority)
        
        # TTS if enabled
        if message.get("audio_enabled"):
            await self.audio.speak(content)
        
        # Acknowledge
        if self.ws:
            try:
                await self.ws.send(json.dumps({
                    "type": "ack",
                    "message_id": message.get("id")
                }))
            except:
                pass
    
    async def _handle_emergency(self, data):
        """Handle emergency with high priority"""
        template_key = data.get("template", "evacuate")
        template = EMERGENCY_TEMPLATES.get(template_key, EMERGENCY_TEMPLATES["evacuate"])
        
        await self.display.display(
            template["content"],
            template["priority"],
            template["color"]
        )
        
        if template.get("audio"):
            await self.audio.speak(template["content"])
    
    async def run_offline(self):
        """Run in offline mode with local capabilities"""
        print("\n" + "="*50)
        print("📴 OFFLINE MODE - Local operation only")
        print("="*50)
        print("Available commands:")
        print("  evacuate  - Show evacuation message")
        print("  shelter   - Show shelter in place")
        print("  medical   - Show medical emergency")
        print("  weather   - Show severe weather")
        print("  clear     - Clear display")
        print("  reconnect - Try to reconnect")
        print("  quit      - Exit")
        print("="*50 + "\n")
        
        while True:
            try:
                cmd = await asyncio.get_event_loop().run_in_executor(
                    None, input, "offline> "
                )
                cmd = cmd.strip().lower()
                
                if cmd in EMERGENCY_TEMPLATES:
                    template = EMERGENCY_TEMPLATES[cmd]
                    await self.display.display(
                        template["content"],
                        template["priority"],
                        template["color"]
                    )
                    if template.get("audio"):
                        await self.audio.speak(template["content"])
                    # Queue for later sync
                    self.cache.queue_message(f"OFFLINE: {cmd}")
                    
                elif cmd == "clear":
                    await self.display.clear()
                    
                elif cmd == "reconnect":
                    print("🔄 Attempting to reconnect...")
                    self.offline_mode = False
                    await self.connect()
                    return
                    
                elif cmd == "quit":
                    print("👋 Shutting down")
                    return
                    
                else:
                    print(f"Unknown command: {cmd}")
                    
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Shutting down")
                return


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    print("="*50)
    print("🎪 CITYARRAY Sign Client v2.0")
    print("   With cellular failover & offline mode")
    print("="*50)
    print(f"   Dashboard: {CONFIG['dashboard_host']}:{CONFIG['dashboard_port']}")
    print(f"   Sign: {CONFIG['sign_name']}")
    print(f"   Zone: {CONFIG['sign_zone']}")
    print("="*50 + "\n")
    
    client = SignClient()
    
    try:
        await client.connect()
    except KeyboardInterrupt:
        print("\n👋 Shutting down")


if __name__ == "__main__":
    asyncio.run(main())

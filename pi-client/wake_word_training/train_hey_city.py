#!/usr/bin/env python3
"""
Train custom "Hey City" wake word
"""
import os
import subprocess
from pathlib import Path

print("=" * 50)
print("🎤 Training 'Hey City' Wake Word")
print("=" * 50)

Path("positive").mkdir(exist_ok=True)
Path("negative").mkdir(exist_ok=True)

# Generate positive samples with Piper
print("\n📢 Generating synthetic samples...")
piper = os.path.expanduser("~/cityarray/piper/piper")
model = os.path.expanduser("~/.local/share/piper/en_US-lessac-medium.onnx")

for i, phrase in enumerate(["hey city"] * 5):
    out = f"positive/synth_{i:03d}.wav"
    subprocess.run(f'echo "{phrase}" | {piper} --model {model} --output_file {out}', shell=True, capture_output=True)
    print(f"  ✅ {out}")

# Generate negative samples
print("\n📢 Generating negative samples...")
negatives = ["hey siri", "hey kitty", "hey cindy", "a city", "hey sydney", "hasty", "the city", "hey sweetie"]
for i, phrase in enumerate(negatives):
    out = f"negative/neg_{i:03d}.wav"
    subprocess.run(f'echo "{phrase}" | {piper} --model {model} --output_file {out}', shell=True, capture_output=True)
    print(f"  ✅ {out}")

# Record your voice
print("\n" + "=" * 50)
print("🎤 Record YOUR voice saying 'Hey City' 10 times")
print("=" * 50)

for i in range(10):
    input(f"\n[{i+1}/10] Press Enter, then say 'Hey City'...")
    out = f"positive/voice_{i:03d}.wav"
    subprocess.run(["arecord", "-D", "plughw:2,0", "-d", "3", "-f", "S16_LE", "-r", "16000", "-c", "1", out])
    print(f"  ✅ Saved {out}")

print("\n✅ Done! Samples collected.")
print(f"   Positive: {len(list(Path('positive').glob('*.wav')))}")
print(f"   Negative: {len(list(Path('negative').glob('*.wav')))}")

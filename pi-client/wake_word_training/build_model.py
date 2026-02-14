#!/usr/bin/env python3
"""
Build "Hey City" wake word detector using audio embeddings
"""
import os
import numpy as np
from pathlib import Path
import subprocess
import pickle

# Simple MFCC-based wake word detector
class WakeWordDetector:
    def __init__(self):
        self.positive_embeddings = []
        self.threshold = 0.7
    
    def extract_features(self, wav_file):
        """Extract simple audio features"""
        import wave
        import struct
        
        try:
            with wave.open(wav_file, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                samples = np.array(struct.unpack(f'{len(frames)//2}h', frames), dtype=np.float32)
                samples = samples / 32768.0  # Normalize
                
                # Simple energy-based features
                chunk_size = 1600  # 100ms at 16kHz
                energies = []
                for i in range(0, len(samples) - chunk_size, chunk_size):
                    chunk = samples[i:i+chunk_size]
                    energies.append(np.sqrt(np.mean(chunk**2)))
                
                return np.array(energies[:20])  # First 2 seconds
        except:
            return None
    
    def train(self, positive_dir):
        """Train on positive samples"""
        print("Training on positive samples...")
        
        for wav_file in Path(positive_dir).glob("*.wav"):
            features = self.extract_features(str(wav_file))
            if features is not None and len(features) >= 10:
                self.positive_embeddings.append(features[:10])
                print(f"  ✅ {wav_file.name}")
        
        self.positive_embeddings = np.array(self.positive_embeddings)
        self.mean_embedding = np.mean(self.positive_embeddings, axis=0)
        self.std_embedding = np.std(self.positive_embeddings, axis=0) + 0.001
        
        print(f"\nTrained on {len(self.positive_embeddings)} samples")
    
    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump({
                'mean': self.mean_embedding,
                'std': self.std_embedding,
                'threshold': self.threshold
            }, f)
        print(f"Saved model to {path}")
    
    def predict(self, wav_file):
        """Check if audio matches wake word"""
        features = self.extract_features(wav_file)
        if features is None or len(features) < 10:
            return 0.0
        
        features = features[:10]
        # Normalized distance from mean
        distance = np.mean(np.abs(features - self.mean_embedding) / self.std_embedding)
        score = max(0, 1 - distance / 5)
        return score

# Train
detector = WakeWordDetector()
detector.train("positive")
detector.save("hey_city_model.pkl")

# Test
print("\n📊 Testing on samples...")
print("\nPositive samples (should be > 0.5):")
for wav in list(Path("positive").glob("*.wav"))[:5]:
    score = detector.predict(str(wav))
    status = "✅" if score > 0.5 else "❌"
    print(f"  {status} {wav.name}: {score:.2f}")

print("\nNegative samples (should be < 0.5):")
for wav in Path("negative").glob("*.wav"):
    score = detector.predict(str(wav))
    status = "✅" if score < 0.5 else "❌"
    print(f"  {status} {wav.name}: {score:.2f}")

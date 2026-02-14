#!/usr/bin/env python3
"""
CITYARRAY AI Camera Stream
Live detection overlay viewable at http://<pi-ip>:5000
"""

from flask import Flask, Response, render_template_string, jsonify
from picamera2 import Picamera2
import cv2
import numpy as np
import time
from collections import deque

# Try Hailo
HAILO_AVAILABLE = False
try:
    from hailo_platform import HEF, VDevice, InferVStreams, InputVStreamParams, OutputVStreamParams
    HAILO_AVAILABLE = True
except:
    pass

app = Flask(__name__)

# Config
CONFIG = {
    "model_path": "/home/eion88/cityarray/models/yolov8n.hef",
    "confidence_threshold": 0.4,
    "person_class_id": 0,
}

# Global state
camera = None
detector = None
stats = {"count": 0, "fps": 0, "using_hailo": False}
count_history = deque(maxlen=30)

class HailoDetector:
    def __init__(self, model_path):
        self.hef = HEF(model_path)
        self.input_vstream_info = self.hef.get_input_vstream_infos()[0]
        self.input_shape = self.input_vstream_info.shape
        self.input_height = self.input_shape[0]
        self.input_width = self.input_shape[1]
        
        self.target = VDevice()
        self.network_group = self.target.configure(self.hef)[0]
        self.network_group_params = self.network_group.create_params()
        self.input_vstreams_params = InputVStreamParams.make(self.network_group)
        self.output_vstreams_params = OutputVStreamParams.make(self.network_group)
    
    def detect(self, frame):
        orig_h, orig_w = frame.shape[:2]
        
        # Preprocess
        resized = cv2.resize(frame, (self.input_width, self.input_height))
        resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        input_batch = np.expand_dims(resized.astype(np.uint8), axis=0)
        
        detections = []
        try:
            with InferVStreams(self.network_group, self.input_vstreams_params, self.output_vstreams_params) as pipeline:
                with self.network_group.activate(self.network_group_params):
                    output = pipeline.infer({self.input_vstream_info.name: input_batch})
            
            for name, data in output.items():
                raw = data[0]
                if len(raw.shape) == 2:
                    if raw.shape[1] > raw.shape[0]:
                        raw = raw.T
                    
                    for det in raw:
                        if len(det) < 5:
                            continue
                        scores = det[4:]
                        class_id = np.argmax(scores)
                        conf = scores[class_id]
                        
                        if class_id == CONFIG["person_class_id"] and conf > CONFIG["confidence_threshold"]:
                            x, y, w, h = det[:4]
                            x1 = int((x - w/2) * orig_w / self.input_width)
                            y1 = int((y - h/2) * orig_h / self.input_height)
                            x2 = int((x + w/2) * orig_w / self.input_width)
                            y2 = int((y + h/2) * orig_h / self.input_height)
                            detections.append({
                                "bbox": [max(0,x1), max(0,y1), min(orig_w,x2), min(orig_h,y2)],
                                "confidence": float(conf)
                            })
        except Exception as e:
            print(f"Detection error: {e}")
        
        return detections

class OpenCVDetector:
    def __init__(self):
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    def detect(self, frame):
        small = cv2.resize(frame, None, fx=0.5, fy=0.5)
        boxes, weights = self.hog.detectMultiScale(small, winStride=(8,8), padding=(4,4), scale=1.05)
        
        detections = []
        for (x,y,w,h), weight in zip(boxes, weights):
            if weight > 0.5:
                detections.append({
                    "bbox": [int(x*2), int(y*2), int((x+w)*2), int((y+h)*2)],
                    "confidence": float(weight)
                })
        return detections

def init():
    global camera, detector, stats
    
    print("Starting camera...")
    camera = Picamera2()
    config = camera.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
    camera.configure(config)
    camera.start()
    time.sleep(2)
    
    print("Loading detector...")
    if HAILO_AVAILABLE:
        try:
            detector = HailoDetector(CONFIG["model_path"])
            stats["using_hailo"] = True
            print("✅ Hailo detector ready")
        except Exception as e:
            print(f"Hailo failed: {e}")
            detector = OpenCVDetector()
            print("⚠️ Using OpenCV fallback")
    else:
        detector = OpenCVDetector()
        print("⚠️ Using OpenCV fallback")

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>CITYARRAY AI Camera</title>
    <style>
        body { background: #0a0a1a; color: white; font-family: Arial; text-align: center; padding: 20px; margin: 0; }
        h1 { color: #00ff88; margin-bottom: 10px; }
        .container { display: inline-block; position: relative; }
        img { border: 3px solid #00ff88; border-radius: 10px; max-width: 100%; }
        .stats { margin-top: 15px; font-size: 18px; }
        .stat { display: inline-block; margin: 0 20px; padding: 10px 20px; background: #1a1a2e; border-radius: 8px; }
        .count { color: #00ff88; font-size: 32px; font-weight: bold; }
        .label { color: #888; font-size: 12px; }
        .hailo { color: #ff6b6b; }
    </style>
    <script>
        setInterval(function() {
            fetch('/stats').then(r => r.json()).then(data => {
                document.getElementById('count').innerText = data.count;
                document.getElementById('fps').innerText = data.fps.toFixed(1);
                document.getElementById('detector').innerText = data.using_hailo ? 'HAILO 16 TOPS' : 'CPU';
            });
        }, 500);
    </script>
</head>
<body>
    <h1>🎥 CITYARRAY AI Camera</h1>
    <div class="container">
        <img src="/video_feed">
    </div>
    <div class="stats">
        <div class="stat">
            <div class="count" id="count">0</div>
            <div class="label">PEOPLE</div>
        </div>
        <div class="stat">
            <div class="count" id="fps">0</div>
            <div class="label">FPS</div>
        </div>
        <div class="stat">
            <div class="count hailo" id="detector">-</div>
            <div class="label">DETECTOR</div>
        </div>
    </div>
</body>
</html>
"""

frame_count = 0
fps_time = time.time()
current_fps = 0

def generate_frames():
    global frame_count, fps_time, current_fps, stats, count_history
    
    while True:
        frame = camera.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Run detection
        detections = detector.detect(frame_bgr)
        count = len(detections)
        count_history.append(count)
        smoothed = int(np.mean(count_history))
        
        # Draw boxes
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            conf = det["confidence"]
            
            # Green box
            cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0, 255, 136), 2)
            
            # Label background
            label = f"Person {conf:.0%}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame_bgr, (x1, y1-20), (x1+w+4, y1), (0, 255, 136), -1)
            cv2.putText(frame_bgr, label, (x1+2, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # FPS calculation
        frame_count += 1
        elapsed = time.time() - fps_time
        if elapsed >= 1.0:
            current_fps = frame_count / elapsed
            frame_count = 0
            fps_time = time.time()
        
        # Update stats
        stats["count"] = smoothed
        stats["fps"] = current_fps
        
        # Overlay
        overlay = f"People: {smoothed} | FPS: {current_fps:.1f}"
        cv2.putText(frame_bgr, overlay, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 136), 2)
        cv2.putText(frame_bgr, time.strftime("%H:%M:%S"), (540, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        
        # Encode
        ret, buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def get_stats():
    return jsonify(stats)

if __name__ == '__main__':
    init()
    print("\n" + "=" * 50)
    print("🎥 CITYARRAY AI Camera Stream")
    print("=" * 50)
    print(f"View at: http://192.168.1.112:5000")
    print(f"Detector: {'Hailo' if stats['using_hailo'] else 'OpenCV CPU'}")
    print("Press Ctrl+C to stop\n")
    app.run(host='0.0.0.0', port=5000, threaded=True)

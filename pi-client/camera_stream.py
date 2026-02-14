#!/usr/bin/env python3
"""
CITYARRAY Camera Stream
View at http://<pi-ip>:5000
"""

from flask import Flask, Response, render_template_string
from picamera2 import Picamera2
import cv2
import time

app = Flask(__name__)

camera = Picamera2()
config = camera.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
camera.configure(config)
camera.start()
time.sleep(2)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>CITYARRAY Camera</title>
    <style>
        body { background: #1a1a2e; color: white; font-family: Arial; text-align: center; padding: 20px; }
        h1 { color: #00ff88; }
        img { border: 3px solid #00ff88; border-radius: 10px; max-width: 100%; }
    </style>
</head>
<body>
    <h1>🎥 CITYARRAY Camera Feed</h1>
    <img src="/video_feed">
</body>
</html>
"""

def generate_frames():
    while True:
        frame = camera.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame_bgr, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 136), 2)
        ret, buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("View at: http://192.168.1.112:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)

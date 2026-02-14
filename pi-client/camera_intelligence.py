#!/usr/bin/env python3
"""
CITYARRAY Camera Intelligence
- Real-time crowd detection via Hailo + YOLOv8
- Auto-alerts to dashboard
- Safety event detection
"""

import cv2
import numpy as np
import time
import requests
from datetime import datetime
from collections import deque
from picamera2 import Picamera2

# Try Hailo, fall back to OpenCV
HAILO_AVAILABLE = False
try:
    from hailo_platform import HEF, VDevice, InferVStreams, InputVStreamParams, OutputVStreamParams
    HAILO_AVAILABLE = True
except ImportError:
    print("Hailo not available, using OpenCV fallback")

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "dashboard_host": "192.168.1.80",
    "dashboard_port": 8000,
    "sign_zone": "Main Stage",
    "camera_width": 640,
    "camera_height": 480,
    "model_path": "/home/eion88/cityarray/models/yolov8n.hef",
    "confidence_threshold": 0.5,
    "person_class_id": 0,
    "crowd_warning": 50,
    "crowd_critical": 100,
    "density_warning": 1.5,
    "density_critical": 2.5,
    "alert_cooldown": 60,
    "stats_interval": 10,
    "fov_width": 10,
    "fov_height": 7,
}

# ============================================================================
# HAILO DETECTOR
# ============================================================================

class HailoDetector:
    def __init__(self, model_path):
        print(f"Loading Hailo model: {model_path}")
        self.hef = HEF(model_path)
        
        self.input_vstream_info = self.hef.get_input_vstream_infos()[0]
        self.output_vstream_infos = self.hef.get_output_vstream_infos()
        
        self.input_shape = self.input_vstream_info.shape
        self.input_height = self.input_shape[0]
        self.input_width = self.input_shape[1]
        
        print(f"Model input: {self.input_height}x{self.input_width}")
        
        self.target = VDevice()
        self.network_group = self.target.configure(self.hef)[0]
        self.network_group_params = self.network_group.create_params()
        
        self.input_vstreams_params = InputVStreamParams.make(self.network_group)
        self.output_vstreams_params = OutputVStreamParams.make(self.network_group)
        
        print("Hailo detector ready!")
    
    def preprocess(self, frame):
        """Resize frame to model input size"""
        resized = cv2.resize(frame, (self.input_width, self.input_height))
        if len(resized.shape) == 3 and resized.shape[2] == 3:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        return resized.astype(np.uint8)
    
    def detect(self, frame):
        """Run detection, return person detections"""
        original_h, original_w = frame.shape[:2]
        
        # Preprocess to model input size
        input_data = self.preprocess(frame)
        
        # Create batch (model expects batch dimension)
        input_batch = np.expand_dims(input_data, axis=0)
        
        detections = []
        
        try:
            with InferVStreams(self.network_group, self.input_vstreams_params, self.output_vstreams_params) as pipeline:
                input_dict = {self.input_vstream_info.name: input_batch}
                
                with self.network_group.activate(self.network_group_params):
                    output = pipeline.infer(input_dict)
            
            # Parse YOLOv8 output
            detections = self.parse_output(output, original_w, original_h)
            
        except Exception as e:
            print(f"Inference error: {e}")
        
        return detections
    
    def parse_output(self, output, orig_w, orig_h):
        """Parse YOLOv8 detections"""
        detections = []
        
        # YOLOv8 has multiple output layers, find the detection one
        for name, data in output.items():
            raw = data[0]  # Remove batch dimension
            
            # YOLOv8n output is typically transposed
            if len(raw.shape) == 2:
                # Shape could be (8400, 84) or (84, 8400)
                if raw.shape[1] > raw.shape[0]:
                    raw = raw.T
                
                # Each row: [x, y, w, h, class_scores...]
                for det in raw:
                    if len(det) < 5:
                        continue
                    
                    # Get class scores (index 4 onwards)
                    scores = det[4:]
                    class_id = np.argmax(scores)
                    conf = scores[class_id]
                    
                    # Only keep persons with high confidence
                    if class_id == CONFIG["person_class_id"] and conf > CONFIG["confidence_threshold"]:
                        x, y, w, h = det[:4]
                        
                        # Convert to corner format and scale
                        x1 = int((x - w/2) * orig_w / self.input_width)
                        y1 = int((y - h/2) * orig_h / self.input_height)
                        x2 = int((x + w/2) * orig_w / self.input_width)
                        y2 = int((y + h/2) * orig_h / self.input_height)
                        
                        detections.append({
                            "bbox": [max(0, x1), max(0, y1), min(orig_w, x2), min(orig_h, y2)],
                            "confidence": float(conf),
                            "class": "person"
                        })
        
        return detections


# ============================================================================
# OPENCV FALLBACK DETECTOR
# ============================================================================

class OpenCVDetector:
    """Fallback using OpenCV HOG"""
    
    def __init__(self):
        print("Using OpenCV HOG detector (CPU fallback)")
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    def detect(self, frame):
        scale = 0.5
        small = cv2.resize(frame, None, fx=scale, fy=scale)
        
        boxes, weights = self.hog.detectMultiScale(
            small, winStride=(8, 8), padding=(4, 4), scale=1.05
        )
        
        detections = []
        for (x, y, w, h), weight in zip(boxes, weights):
            if weight > 0.5:
                detections.append({
                    "bbox": [int(x/scale), int(y/scale), int((x+w)/scale), int((y+h)/scale)],
                    "confidence": float(weight),
                    "class": "person"
                })
        
        return detections


# ============================================================================
# CAMERA INTELLIGENCE
# ============================================================================

class CameraIntelligence:
    def __init__(self):
        print("Initializing camera...")
        self.camera = Picamera2()
        config = self.camera.create_preview_configuration(
            main={"size": (CONFIG["camera_width"], CONFIG["camera_height"]), "format": "RGB888"}
        )
        self.camera.configure(config)
        self.camera.start()
        time.sleep(2)
        print("Camera ready!")
        
        # Initialize detector
        self.using_hailo = False
        if HAILO_AVAILABLE:
            try:
                self.detector = HailoDetector(CONFIG["model_path"])
                self.using_hailo = True
            except Exception as e:
                print(f"Hailo init failed: {e}")
                self.detector = OpenCVDetector()
        else:
            self.detector = OpenCVDetector()
        
        self.people_count_history = deque(maxlen=30)
        self.last_alert_time = {}
        self.last_stats_time = 0
        self.frame_count = 0
        self.fps = 0
        self.fps_time = time.time()
    
    def get_smoothed_count(self):
        if not self.people_count_history:
            return 0
        return int(np.mean(self.people_count_history))
    
    def calculate_density(self, count):
        area = CONFIG["fov_width"] * CONFIG["fov_height"]
        return count / area if area > 0 else 0
    
    def can_alert(self, alert_type, now):
        last = self.last_alert_time.get(alert_type, 0)
        if now - last >= CONFIG["alert_cooldown"]:
            self.last_alert_time[alert_type] = now
            return True
        return False
    
    def send_alert(self, alert):
        try:
            url = f"http://{CONFIG['dashboard_host']}:{CONFIG['dashboard_port']}/api/messages"
            data = {
                "content": alert["message"],
                "priority": alert["priority"],
                "category": "safety",
                "target_type": "zone",
                "target_zones": [CONFIG["sign_zone"]]
            }
            requests.post(url, json=data, timeout=5)
            print(f"\n📡 Alert: {alert['type']}")
        except Exception as e:
            print(f"\n⚠️ Alert failed: {e}")
    
    def check_alerts(self, count, density):
        now = time.time()
        
        if count >= CONFIG["crowd_critical"] and self.can_alert("crowd_critical", now):
            self.send_alert({"type": "crowd_critical", "priority": 90,
                "message": f"🚨 CRITICAL: {count} people - area at capacity!"})
        elif count >= CONFIG["crowd_warning"] and self.can_alert("crowd_warning", now):
            self.send_alert({"type": "crowd_warning", "priority": 70,
                "message": f"⚠️ High crowd: {count} people in {CONFIG['sign_zone']}"})
        
        if density >= CONFIG["density_critical"] and self.can_alert("density_critical", now):
            self.send_alert({"type": "density_critical", "priority": 95,
                "message": f"🚨 DANGER: Density {density:.1f}/m² - spread out!"})
        elif density >= CONFIG["density_warning"] and self.can_alert("density_warning", now):
            self.send_alert({"type": "density_warning", "priority": 75,
                "message": f"⚠️ High density: {density:.1f}/m²"})
    
    def update_fps(self):
        self.frame_count += 1
        now = time.time()
        elapsed = now - self.fps_time
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_time = now
    
    def process_frame(self, frame):
        detections = self.detector.detect(frame)
        count = len(detections)
        
        self.people_count_history.append(count)
        smoothed_count = self.get_smoothed_count()
        density = self.calculate_density(smoothed_count)
        
        self.check_alerts(smoothed_count, density)
        self.update_fps()
        
        return {
            "detections": detections,
            "count": count,
            "smoothed_count": smoothed_count,
            "density": density,
            "fps": self.fps
        }
    
    def draw_overlay(self, frame, results):
        for det in results["detections"]:
            x1, y1, x2, y2 = det["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{det['confidence']:.0%}", (x1, y1-5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Status overlay
        status_color = (0, 255, 0)
        if results["density"] >= CONFIG["density_critical"]:
            status_color = (0, 0, 255)
        elif results["density"] >= CONFIG["density_warning"]:
            status_color = (0, 165, 255)
        
        cv2.putText(frame, f"People: {results['smoothed_count']}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        cv2.putText(frame, f"Density: {results['density']:.2f}/m2", (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        cv2.putText(frame, f"FPS: {results['fps']:.1f} ({'HAILO' if self.using_hailo else 'CPU'})", (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return frame
    
    def run(self, display=False, save_frames=False):
        print("\n" + "=" * 50)
        print("🎥 CITYARRAY Camera Intelligence")
        print("=" * 50)
        print(f"Detector: {'Hailo 16 TOPS' if self.using_hailo else 'OpenCV CPU'}")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                frame = self.camera.capture_array()
                results = self.process_frame(frame)
                
                if display:
                    annotated = self.draw_overlay(frame.copy(), results)
                    cv2.imshow("CITYARRAY", annotated)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                if save_frames and self.frame_count == 0:
                    cv2.imwrite("/tmp/camera_latest.jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                
                if self.frame_count == 0:
                    bar = "█" * min(int(results["density"] * 4), 20)
                    print(f"\r👥 {results['smoothed_count']:3d} | 📊 {results['density']:.2f}/m² [{bar:<20}] | 🎬 {results['fps']:.1f} fps", end="")
        
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping...")
        finally:
            self.camera.stop()
            if display:
                cv2.destroyAllWindows()
    
    def test_single_frame(self):
        print("Capturing test frame...")
        frame = self.camera.capture_array()
        
        results = self.process_frame(frame)
        
        print(f"\nResults:")
        print(f"  People detected: {results['count']}")
        print(f"  Density: {results['density']:.2f}/m²")
        print(f"  Using: {'Hailo' if self.using_hailo else 'OpenCV CPU'}")
        
        annotated = self.draw_overlay(frame.copy(), results)
        cv2.imwrite("/tmp/camera_test.jpg", cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
        print(f"\nSaved: /tmp/camera_test.jpg")
        
        self.camera.stop()
        return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--display", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()
    
    intel = CameraIntelligence()
    
    if args.test:
        intel.test_single_frame()
    else:
        intel.run(display=args.display, save_frames=args.save)

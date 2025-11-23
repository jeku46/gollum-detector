"""
Gollum Detection Server using locally trained YOLO model
"""
from flask import Flask, Response, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from ultralytics import YOLO
import cv2
import threading
import requests
import time
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
latest_frame = None
latest_result = None
frame_lock = threading.Lock()
model = None
cap = None
camera_active = False
last_gollum_state = None
detection_thread = None

# LED control configuration
LED_BASE_URL = "http://10.0.0.106:5000"

# Model path - will be set to trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "gollum_model.pt")
# Fallback to runs directory if gollum_model.pt doesn't exist
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = "/Users/jenniferkuchta/Projects/GollumApp/runs/detect/gollum-yolo112/weights/best.pt"

def control_led(color, state):
    """Control LED on Raspberry Pi"""
    try:
        url = f"{LED_BASE_URL}/led/{color}/{state}"
        response = requests.post(url, timeout=2)
        print(f"LED Control: {color} {state} - Status: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"LED Control Error: {e}")
        return None

def turn_off_all_leds():
    """Turn off both LEDs"""
    control_led('red', 'off')
    control_led('green', 'off')

def detection_loop():
    """Main detection loop running in a separate thread"""
    global latest_frame, latest_result, last_gollum_state, camera_active, cap, model

    while camera_active:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            time.sleep(0.1)
            continue

        # Run detection
        results = model(frame, conf=0.90, verbose=False)

        # Get annotated frame
        annotated_frame = results[0].plot()

        # Check if Gollum was detected
        gollum_found = False
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                if class_name.lower() == "gollum":
                    gollum_found = True
                    break

        # Update shared frame
        with frame_lock:
            latest_frame = annotated_frame
            latest_result = {
                'gollum_found': gollum_found,
                'detections': len(results[0].boxes) if results else 0
            }

        # Only control LEDs and emit event if state changed
        if gollum_found != last_gollum_state:
            last_gollum_state = gollum_found

            # Control LEDs
            if gollum_found:
                control_led('red', 'on')
                control_led('green', 'off')
            else:
                control_led('red', 'off')
                control_led('green', 'on')

            # Emit WebSocket event
            socketio.emit('detection', {
                'gollum_found': gollum_found,
                'timestamp': time.time()
            })

            print(f"Detection: {'GOLLUM FOUND' if gollum_found else 'gollum not found'}")

        # Small delay to prevent CPU overload
        time.sleep(0.033)  # ~30 FPS

def generate_frames():
    """Generator function to stream video frames"""
    global latest_frame

    while True:
        with frame_lock:
            if latest_frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', latest_frame)
                if ret:
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        time.sleep(0.033)  # ~30 FPS

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_camera', methods=['POST'])
def start_camera():
    """Start the camera and detection"""
    global model, cap, camera_active, last_gollum_state, detection_thread

    if camera_active:
        return jsonify({'status': 'already_running'})

    try:
        # Reset state
        last_gollum_state = None

        # Turn off all LEDs
        turn_off_all_leds()

        # Load model if not already loaded
        if model is None:
            print(f"Loading model from: {MODEL_PATH}")
            if not os.path.exists(MODEL_PATH):
                return jsonify({
                    'status': 'error',
                    'message': f'Model not found at {MODEL_PATH}. Please train the model first.'
                }), 500
            model = YOLO(MODEL_PATH)
            print(f"Model loaded! Classes: {model.names}")

        # Open camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return jsonify({'status': 'error', 'message': 'Could not open camera'}), 500

        camera_active = True

        # Start detection thread
        detection_thread = threading.Thread(target=detection_loop, daemon=True)
        detection_thread.start()

        return jsonify({'status': 'started'})
    except Exception as e:
        print(f"Error starting camera: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    """Stop the camera and detection"""
    global cap, camera_active, last_gollum_state

    if not camera_active:
        return jsonify({'status': 'not_running'})

    try:
        camera_active = False

        # Wait for detection thread to stop
        time.sleep(0.2)

        # Release camera
        if cap:
            cap.release()
            cap = None

        last_gollum_state = None

        # Turn off all LEDs
        turn_off_all_leds()

        return jsonify({'status': 'stopped'})
    except Exception as e:
        print(f"Error stopping camera: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Get camera status"""
    return jsonify({
        'camera_active': camera_active,
        'gollum_found': last_gollum_state,
        'model_loaded': model is not None,
        'model_path': MODEL_PATH
    })

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    emit('connected', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    print("=" * 60)
    print("Gollum Detection Server (Local YOLO Model)")
    print("=" * 60)
    print(f"Model path: {MODEL_PATH}")
    print(f"Model exists: {os.path.exists(MODEL_PATH)}")
    print("Server will be available at http://localhost:5001")
    print("=" * 60)
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)

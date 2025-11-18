from flask import Flask, Response, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from inference import InferencePipeline
import cv2
import threading
import requests
import time

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
latest_frame = None
latest_result = None
frame_lock = threading.Lock()
pipeline = None
camera_active = False
last_gollum_state = None

# LED control configuration
LED_BASE_URL = "http://10.0.0.106:5000"

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

def my_sink(result, video_frame):
    """Callback function for InferencePipeline"""
    global latest_frame, latest_result, last_gollum_state

    # Store the latest frame
    with frame_lock:
        # Get the annotated image if available, otherwise use the original frame
        if result.get("output_image"):
            latest_frame = result["output_image"].numpy_image
        else:
            latest_frame = video_frame.image

        latest_result = result

    # Check if Gollum was detected
    gollum_found = False
    if result.get("outputs") and len(result["outputs"]) > 0:
        predictions = result["outputs"][0].get("predictions", {}).get("predictions", [])
        gollum_found = any(pred.get("class") == "gollum" for pred in predictions)

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
    """Start the camera and detection pipeline"""
    global pipeline, camera_active, last_gollum_state

    if camera_active:
        return jsonify({'status': 'already_running'})

    try:
        # Reset state
        last_gollum_state = None

        # Turn off all LEDs
        turn_off_all_leds()

        # Initialize pipeline
        pipeline = InferencePipeline.init_with_workflow(
            api_key="g3kyzU8K82YQwalVS2Ks",
            workspace_name="die-counter",
            workflow_id="gollum-finder-2",
            video_reference=0,  # Built-in webcam
            max_fps=30,
            on_prediction=my_sink,
            workflows_parameters={
                "confidence": "0.95"
            }
        )

        # Start pipeline in a separate thread
        threading.Thread(target=pipeline.start, daemon=True).start()
        camera_active = True

        return jsonify({'status': 'started'})
    except Exception as e:
        print(f"Error starting camera: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    """Stop the camera and detection pipeline"""
    global pipeline, camera_active, last_gollum_state

    if not camera_active:
        return jsonify({'status': 'not_running'})

    try:
        if pipeline:
            pipeline.terminate()
            pipeline = None

        camera_active = False
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
        'gollum_found': last_gollum_state
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
    print("Starting Gollum Detection Server...")
    print("Server will be available at http://localhost:5001")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)

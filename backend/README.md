# Gollum Detection Backend

Flask server for live webcam detection with Roboflow InferencePipeline.

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

```bash
python server.py
```

Server will start on `http://localhost:5001`

## API Endpoints

- `POST /start_camera` - Start webcam and detection
- `POST /stop_camera` - Stop webcam and detection
- `GET /status` - Get current camera status
- `GET /video_feed` - MJPEG video stream
- WebSocket on `/socket.io` - Real-time detection events

## Features

- Live video streaming from webcam
- Real-time Gollum detection using Roboflow
- Automatic LED control on Raspberry Pi
- WebSocket notifications for detection events

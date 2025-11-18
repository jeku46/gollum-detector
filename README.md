# Gollum Detector App

A real-time Gollum detection system with both image upload and live webcam detection modes.

## Features

- **Image Upload Mode**: Upload images to detect if Gollum is present
- **Live Detection Mode**: Real-time webcam detection with live video streaming
- **LED Integration**: Controls Raspberry Pi LEDs based on detection results
  - Red LED: Gollum detected
  - Green LED: No Gollum detected
- **WebSocket Updates**: Real-time detection notifications

## Architecture

- **Frontend**: React + Vite (port 5174)
- **Backend**: Flask + Roboflow InferencePipeline (port 5001)
- **LED Server**: Raspberry Pi Flask server (port 5000)

## Project Structure

```
GollumApp/
├── backend/                 # Python Flask backend
│   ├── server.py           # Main server with detection pipeline
│   ├── train_yolo.py       # Local YOLOv8/v11 training script
│   └── requirements.txt    # Python dependencies
├── gollum-detector/        # React frontend
│   ├── src/
│   │   ├── App.jsx        # Main application component
│   │   └── App.css        # Styles
│   └── package.json       # Node dependencies
├── raspberry-pi/           # Raspberry Pi LED control
│   ├── api.py             # Flask API for LED control
│   ├── program.py         # Button-controlled LED demo
│   ├── requirements.txt   # Pi Python dependencies
│   ├── led-api.service    # Systemd service file
│   └── README.md          # Pi setup instructions
└── README.md              # This file
```

## Setup

### 1. Backend Setup (Python)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup (React)

```bash
cd gollum-detector

# Install dependencies
npm install
```

### 3. Raspberry Pi LED Server

The Raspberry Pi controls the physical LEDs that indicate detection status. See the [`raspberry-pi/`](raspberry-pi/) directory for:
- Complete setup instructions
- Hardware wiring diagram
- Code to run on the Pi
- Systemd service for auto-start

**Quick Setup:**
Make sure your Raspberry Pi LED server is running on `10.0.0.106:5000` with these endpoints:
- `POST /led/red/on`
- `POST /led/red/off`
- `POST /led/green/on`
- `POST /led/green/off`

See [raspberry-pi/README.md](raspberry-pi/README.md) for detailed setup instructions.

## Running the App

You need to run both the backend and frontend servers:

### Terminal 1: Start Backend (Python)

```bash
cd backend
source venv/bin/activate
python server.py
```

Backend will start on `http://localhost:5001`

### Terminal 2: Start Frontend (React)

```bash
cd gollum-detector
npm run dev
```

Frontend will start on `http://localhost:5174`

### Open in Browser

Navigate to `http://localhost:5174`

## Usage

### Image Upload Mode

1. Click "Image Upload" button (default mode)
2. Drag & drop an image or click "Choose File"
3. Click "Detect Gollum"
4. View results and LED indicators

### Live Detection Mode

1. Click "Live Detection" button
2. Click "Start Camera" to activate your webcam
3. Watch live video feed with real-time Gollum detection
4. LEDs update automatically based on detections
5. Click "Stop Camera" when done

## How It Works

### Image Upload Flow
1. Image uploaded → Both LEDs turn OFF
2. Detection starts → Both LEDs turn OFF
3. Detection complete:
   - Gollum found → Red LED ON, "GOLLUM FOUND" displayed
   - No Gollum → Green LED ON, "gollum not found" displayed

### Live Detection Flow
1. Camera starts → Both LEDs turn OFF
2. Continuous detection:
   - Gollum appears → Red LED ON, "GOLLUM FOUND" displayed
   - Gollum leaves → Green LED ON, "gollum not found" displayed
3. Camera stops → Both LEDs turn OFF

## Technical Details

### Backend Endpoints

- `POST /start_camera` - Start webcam and detection pipeline
- `POST /stop_camera` - Stop webcam and detection
- `GET /status` - Get current camera status
- `GET /video_feed` - MJPEG video stream
- WebSocket `/socket.io` - Real-time detection events

### WebSocket Events

**Client receives:**
- `connected` - Connection established
- `detection` - Detection result `{gollum_found: boolean, timestamp: number}`

### Configuration

**Backend (server.py):**
- Roboflow API Key: `g3kyzU8K82YQwalVS2Ks`
- Workspace: `die-counter`
- Workflow: `gollum-finder-2`
- Camera: Device 0 (built-in webcam)
- Max FPS: 30
- Confidence: 0.95

**LED Server:**
- Address: `10.0.0.106:5000`

## Troubleshooting

### Camera not starting
- Make sure no other application is using your webcam
- Check that the backend server is running
- Verify Python dependencies are installed

### LEDs not responding
- Ensure Raspberry Pi is accessible at `10.0.0.106:5000`
- Check that the LED server is running on the Pi
- Verify network connectivity

### Video feed not showing
- Make sure backend is running on port 5001
- Check browser console for errors
- Try refreshing the page

### WebSocket connection issues
- Verify both frontend and backend are running
- Check that ports 5001 and 5174 are not blocked by firewall

## Requirements

**Python (Backend):**
- Python 3.8+
- Flask
- Roboflow Inference SDK
- OpenCV
- Socket.IO

**Node.js (Frontend):**
- Node.js 16+
- React 18
- Vite
- Socket.IO Client

**Hardware:**
- Webcam (built-in or USB)
- Raspberry Pi with LED setup (optional)

## License

This project uses Roboflow's inference API for object detection.

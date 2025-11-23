import { useState, useEffect, useRef } from 'react'
import { io } from 'socket.io-client'
import './App.css'

const BACKEND_URL = 'http://localhost:5001'

function App() {
  // Mode: 'upload' or 'live'
  const [mode, setMode] = useState('upload')

  // Upload mode state
  const [selectedImage, setSelectedImage] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isDetecting, setIsDetecting] = useState(false)
  const [detectionResult, setDetectionResult] = useState(null)
  const [error, setError] = useState(null)

  // Live detection state
  const [cameraActive, setCameraActive] = useState(false)
  const [liveDetection, setLiveDetection] = useState(null)
  const [lastGollumSpotted, setLastGollumSpotted] = useState(null)
  const [confidence, setConfidence] = useState(0.1)
  const socketRef = useRef(null)

  const handleImageSelect = async (file) => {
    if (file && file.type.startsWith('image/')) {
      setSelectedImage(file)
      setDetectionResult(null)
      setError(null)

      // Turn off both LEDs when image is uploaded
      try {
        await Promise.all([
          fetch('/api/led/red/off', { method: 'POST' }),
          fetch('/api/led/green/off', { method: 'POST' })
        ])
      } catch (err) {
        console.error('Failed to turn off LEDs:', err)
      }

      const reader = new FileReader()
      reader.onloadend = () => {
        setPreviewUrl(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleFileInput = (e) => {
    const file = e.target.files[0]
    handleImageSelect(file)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    handleImageSelect(file)
  }

  const detectGollum = async () => {
    if (!previewUrl) return

    setIsDetecting(true)
    setError(null)
    setDetectionResult(null)

    // Turn off both LEDs when detection starts
    try {
      await Promise.all([
        fetch('/api/led/red/off', { method: 'POST' }),
        fetch('/api/led/green/off', { method: 'POST' })
      ])
    } catch (err) {
      console.error('Failed to turn off LEDs:', err)
    }

    try {
      console.log('Sending request to Roboflow...')
      const response = await fetch('https://serverless.roboflow.com/die-counter/workflows/gollum-finder-2', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          api_key: 'g3kyzU8K82YQwalVS2Ks',
          inputs: {
            "image": {"type": "base64", "value": previewUrl.split(',')[1]},
            "confidence": "0.95"
          }
        })
      })

      console.log('Response status:', response.status)
      const result = await response.json()
      console.log('Result:', result)

      if (!response.ok) {
        setError(`API Error: ${result.message || 'Unknown error'}`)
        console.error('API returned error:', result)
      } else {
        setDetectionResult(result)

        // Check if gollum was found and turn on appropriate LED
        const predictions = result?.outputs?.[0]?.predictions?.predictions
        const gollumFound = predictions?.some(pred => pred.class === 'gollum')

        try {
          if (gollumFound) {
            await fetch('/api/led/red/on', { method: 'POST' })
          } else {
            await fetch('/api/led/green/on', { method: 'POST' })
          }
        } catch (err) {
          console.error('Failed to control LED:', err)
        }
      }
    } catch (err) {
      setError('Failed to detect Gollum. Please try again.')
      console.error('Detection error:', err)
    } finally {
      setIsDetecting(false)
    }
  }

  const handleReset = () => {
    setSelectedImage(null)
    setPreviewUrl(null)
    setDetectionResult(null)
    setError(null)
  }

  // WebSocket connection for live detection
  useEffect(() => {
    if (mode === 'live') {
      socketRef.current = io(BACKEND_URL)

      socketRef.current.on('connected', (data) => {
        console.log('WebSocket connected:', data)
      })

      socketRef.current.on('detection', (data) => {
        console.log('Detection event:', data)
        setLiveDetection(data)
        if (data.gollum_found) {
          setLastGollumSpotted(new Date(data.timestamp * 1000))
        }
      })

      return () => {
        if (socketRef.current) {
          socketRef.current.disconnect()
        }
      }
    }
  }, [mode])

  const startCamera = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/start_camera`, {
        method: 'POST'
      })
      const data = await response.json()
      if (data.status === 'started' || data.status === 'already_running') {
        setCameraActive(true)
        setLiveDetection(null)
      }
    } catch (err) {
      console.error('Failed to start camera:', err)
      setError('Failed to start camera')
    }
  }

  const stopCamera = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/stop_camera`, {
        method: 'POST'
      })
      const data = await response.json()
      if (data.status === 'stopped' || data.status === 'not_running') {
        setCameraActive(false)
        setLiveDetection(null)
      }
    } catch (err) {
      console.error('Failed to stop camera:', err)
      setError('Failed to stop camera')
    }
  }

  const updateConfidence = async (newConfidence) => {
    setConfidence(newConfidence)
    try {
      await fetch(`${BACKEND_URL}/set_confidence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confidence: newConfidence })
      })
    } catch (err) {
      console.error('Failed to update confidence:', err)
    }
  }

  const switchMode = (newMode) => {
    // Stop camera when switching modes
    if (mode === 'live' && cameraActive) {
      stopCamera()
    }
    setMode(newMode)
    setError(null)
    setDetectionResult(null)
    setLiveDetection(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Gollum Detector</h1>
        <p className="subtitle">
          {mode === 'upload' ? 'Upload an image to detect if Gollum is present' : 'Live webcam detection'}
        </p>

        <div className="mode-switcher">
          <button
            className={`mode-button ${mode === 'upload' ? 'active' : ''}`}
            onClick={() => switchMode('upload')}
          >
            Image Upload
          </button>
          <button
            className={`mode-button ${mode === 'live' ? 'active' : ''}`}
            onClick={() => switchMode('live')}
          >
            Live Detection
          </button>
        </div>
      </header>

      <main className="app-main">
        {mode === 'upload' ? (
          !previewUrl ? (
          <div
            className={`upload-zone ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="upload-content">
              <svg
                className="upload-icon"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p className="upload-text">Drag and drop an image here</p>
              <p className="upload-text-or">or</p>
              <label className="upload-button">
                Choose File
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileInput}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
          </div>
        ) : (
          <div className="preview-container">
            <div className="preview-image-wrapper">
              <img src={previewUrl} alt="Uploaded preview" className="preview-image" />
            </div>
            <div className="image-info">
              <p className="file-name">{selectedImage.name}</p>
              <p className="file-size">
                {(selectedImage.size / 1024).toFixed(2)} KB
              </p>
            </div>

            <div className="action-buttons">
              <button
                className="detect-button"
                onClick={detectGollum}
                disabled={isDetecting}
              >
                {isDetecting ? 'Detecting...' : 'Detect Gollum'}
              </button>
              <button className="reset-button" onClick={handleReset}>
                Upload Another Image
              </button>
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {detectionResult && (
              <div className="results-container">
                <h2 className="results-title">Detection Results</h2>
                {(() => {
                  const predictions = detectionResult?.outputs?.[0]?.predictions?.predictions
                  const gollumFound = predictions?.some(pred => pred.class === 'gollum')

                  return gollumFound ? (
                    <div className="gollum-found">GOLLUM FOUND</div>
                  ) : (
                    <div className="gollum-not-found">gollum not found</div>
                  )
                })()}
              </div>
            )}
          </div>
        )
        ) : (
          // Live Detection Mode
          <div className="live-container">
            <div className="video-wrapper">
              {cameraActive ? (
                <img
                  src={`${BACKEND_URL}/video_feed`}
                  alt="Live video feed"
                  className="live-video"
                />
              ) : (
                <div className="video-placeholder">
                  <svg
                    className="camera-icon"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                    />
                  </svg>
                  <p>Camera is off</p>
                </div>
              )}
            </div>

            <div className="action-buttons">
              {!cameraActive ? (
                <button className="detect-button" onClick={startCamera}>
                  Start Camera
                </button>
              ) : (
                <button className="reset-button" onClick={stopCamera}>
                  Stop Camera
                </button>
              )}
            </div>

            <div className="confidence-slider">
              <label htmlFor="confidence">
                Confidence: {(confidence * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                id="confidence"
                min="0"
                max="100"
                value={confidence * 100}
                onChange={(e) => updateConfidence(e.target.value / 100)}
              />
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {liveDetection && cameraActive && (
              <div className="results-container">
                <h2 className="results-title">Live Detection</h2>
                {liveDetection.gollum_found ? (
                  <div className="gollum-found">GOLLUM FOUND</div>
                ) : (
                  <div className="gollum-not-found">gollum not found</div>
                )}
                {lastGollumSpotted && (
                  <div className="last-spotted">
                    Last spotted: {lastGollumSpotted.toLocaleTimeString()}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default App

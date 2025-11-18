import { useState } from 'react'
import './App.css'

function App() {
  const [selectedImage, setSelectedImage] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isDetecting, setIsDetecting] = useState(false)
  const [detectionResult, setDetectionResult] = useState(null)
  const [error, setError] = useState(null)

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

  return (
    <div className="app">
      <header className="app-header">
        <h1>Gollum Detector</h1>
        <p className="subtitle">Upload an image to detect if Gollum is present</p>
      </header>

      <main className="app-main">
        {!previewUrl ? (
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
        )}
      </main>
    </div>
  )
}

export default App

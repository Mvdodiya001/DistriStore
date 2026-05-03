/**
 * PreviewModal — In-Browser File Preview (Phase 20)
 *
 * Streams files directly from the /preview endpoint using O(1) memory.
 * Renders different HTML elements based on MIME type:
 *   - Images: <img>
 *   - Video:  <video>
 *   - PDF:    <iframe>
 *   - Text:   <iframe>
 *   - Other:  "Not supported" message
 */

import { useState, useEffect } from 'react'
import { X, Eye, Download, ExternalLink } from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8888`

// Map extensions to preview categories
const PREVIEW_TYPES = {
  image: ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico'],
  video: ['.mp4', '.webm', '.ogg', '.mov'],
  audio: ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'],
  pdf:   ['.pdf'],
  text:  ['.txt', '.md', '.log', '.csv', '.json', '.xml', '.yaml', '.yml',
          '.html', '.css', '.js', '.jsx', '.ts', '.tsx', '.py', '.go',
          '.rs', '.java', '.c', '.cpp', '.h', '.sh', '.bat', '.toml', '.ini'],
}

function getPreviewType(filename) {
  if (!filename) return 'unsupported'
  const ext = '.' + filename.split('.').pop().toLowerCase()
  for (const [type, exts] of Object.entries(PREVIEW_TYPES)) {
    if (exts.includes(ext)) return type
  }
  return 'unsupported'
}

export default function PreviewModal({ isOpen, onClose, fileHash, filename, password = '' }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const previewType = getPreviewType(filename)
  const params = password ? `?password=${encodeURIComponent(password)}` : ''
  const previewUrl = `${API_BASE}/preview/${fileHash}${params}`

  useEffect(() => {
    if (isOpen) {
      setLoading(true)
      setError(null)
    }
  }, [isOpen, fileHash])

  if (!isOpen) return null

  const handleLoad = () => setLoading(false)
  const handleError = () => {
    setLoading(false)
    setError('Failed to load preview. Check password or try downloading.')
  }

  return (
    <div className="preview-overlay" onClick={onClose}>
      <div className="preview-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="preview-header">
          <div className="preview-header-left">
            <Eye size={18} className="preview-icon" />
            <span className="preview-title">{filename || 'Preview'}</span>
            <span className="preview-type-badge">{previewType.toUpperCase()}</span>
          </div>
          <div className="preview-header-actions">
            <a
              href={previewUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="preview-action-btn"
              title="Open in new tab"
            >
              <ExternalLink size={16} />
            </a>
            <button className="preview-action-btn" onClick={onClose} title="Close">
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="preview-body">
          {loading && !error && (
            <div className="preview-loading">
              <div className="spinner" />
              <p>Streaming preview...</p>
            </div>
          )}

          {error && (
            <div className="preview-error">
              <p>❌ {error}</p>
            </div>
          )}

          {previewType === 'image' && (
            <img
              src={previewUrl}
              alt={filename}
              className="preview-image"
              onLoad={handleLoad}
              onError={handleError}
              style={{ display: loading ? 'none' : 'block' }}
            />
          )}

          {previewType === 'video' && (
            <video
              controls
              autoPlay={false}
              className="preview-video"
              onLoadedData={handleLoad}
              onError={handleError}
              style={{ display: loading ? 'none' : 'block' }}
            >
              <source src={previewUrl} />
              Your browser does not support video playback.
            </video>
          )}

          {previewType === 'audio' && (
            <div className="preview-audio-wrap" style={{ display: loading ? 'none' : 'flex' }}>
              <div className="preview-audio-icon">🎵</div>
              <audio
                controls
                className="preview-audio"
                onLoadedData={handleLoad}
                onError={handleError}
              >
                <source src={previewUrl} />
              </audio>
            </div>
          )}

          {(previewType === 'pdf' || previewType === 'text') && (
            <iframe
              src={previewUrl}
              className="preview-iframe"
              title={filename}
              onLoad={handleLoad}
              onError={handleError}
              style={{ display: loading ? 'none' : 'block' }}
            />
          )}

          {previewType === 'unsupported' && (
            <div className="preview-unsupported">
              <div className="preview-unsupported-icon">📄</div>
              <h3>Preview not available</h3>
              <p>This file type cannot be previewed in the browser.</p>
              <p className="preview-unsupported-hint">
                Try downloading the file instead.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Helper hook: returns true if the filename is previewable.
 */
export function isPreviewable(filename) {
  return getPreviewType(filename) !== 'unsupported'
}

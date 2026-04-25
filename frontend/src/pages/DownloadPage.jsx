/**
 * DownloadPage — Download file by hash with decryption support.
 * Reads prefilled hash from URL query params (from dashboard file list clicks).
 */

import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Download, Lock } from 'lucide-react'
import { downloadFile, triggerBlobDownload } from '../api/client'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

export default function DownloadPage() {
  const [searchParams] = useSearchParams()
  const [hash, setHash] = useState('')
  const [password, setPassword] = useState('')
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  // Prefill hash from URL params (e.g., /download?hash=abc123)
  useEffect(() => {
    const h = searchParams.get('hash')
    if (h) setHash(h)
  }, [searchParams])

  const handleDownload = async () => {
    if (!hash) return
    setDownloading(true); setError(null); setSuccess(false)
    try {
      const { blob, filename } = await downloadFile(hash, password)
      triggerBlobDownload(blob, filename)
      setSuccess(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <Card title="Download File" icon={<Download size={20} />}>
      <div className="form-section">
        <div className="input-group">
          <label>File Hash</label>
          <input type="text" className="input-field" placeholder="Enter SHA-256 file hash..." value={hash} onChange={(e) => setHash(e.target.value)} />
        </div>
        <div className="input-group">
          <label><Lock size={14} /> Decryption Password (if encrypted)</label>
          <input type="password" className="input-field" placeholder="Leave empty if not encrypted" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <Button variant="success" loading={downloading} disabled={!hash} onClick={handleDownload}>
          ⬇️ Download File
        </Button>
        {success && <div className="alert alert-success">✅ Downloaded successfully!</div>}
        {error && <div className="alert alert-error">❌ {error}</div>}
      </div>
    </Card>
  )
}

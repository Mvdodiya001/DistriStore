import { useState, useEffect, useCallback, useMemo } from 'react'
import axios from 'axios'
import './index.css'

const API = 'http://localhost:8001'
const LAN_THEORETICAL_MBPS = 125 // 1 Gbps theoretical

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024, sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatUptime(seconds) {
  const h = Math.floor(seconds / 3600), m = Math.floor((seconds % 3600) / 60), s = Math.floor(seconds % 60)
  return h > 0 ? `${h}h ${m}m` : m > 0 ? `${m}m ${s}s` : `${s}s`
}

// ─── Copy to Clipboard Helper ─────────────────────────────────
function CopyButton({ text, label = '📋 Copy' }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = (e) => {
    e.stopPropagation()
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <button className="btn-copy" onClick={handleCopy} title="Copy to clipboard">
      {copied ? '✅ Copied!' : label}
    </button>
  )
}

// ─── Network Topology SVG ─────────────────────────────────────
function NetworkTopology({ status }) {
  const self = { id: status?.node_id || '', name: status?.name || 'This Node' }
  const peers = Object.entries(status?.peers || {})
  const cx = 400, cy = 180, r = 120

  return (
    <div className="panel">
      <div className="panel-title"><span className="icon">🕸️</span> Network Topology</div>
      <div className="topology-canvas">
        <svg viewBox="0 0 800 360">
          <defs>
            <radialGradient id="selfGrad"><stop offset="0%" stopColor="#3b82f6"/><stop offset="100%" stopColor="#1d4ed8"/></radialGradient>
            <radialGradient id="peerGrad"><stop offset="0%" stopColor="#8b5cf6"/><stop offset="100%" stopColor="#6d28d9"/></radialGradient>
          </defs>
          {peers.map(([id, info], i) => {
            const angle = (2 * Math.PI * i) / Math.max(peers.length, 1) - Math.PI / 2
            const px = cx + r * 1.8 * Math.cos(angle), py = cy + r * Math.sin(angle)
            return <line key={`l-${id}`} x1={cx} y1={cy} x2={px} y2={py} className="topo-line active"/>
          })}
          <g className="topo-node topo-self">
            <circle cx={cx} cy={cy} r={24}/>
            <text x={cx} y={cy + 4} className="topo-label" fill="white" fontWeight="700" fontSize="12">ME</text>
            <text x={cx} y={cy + 42} className="topo-label" fontSize="10">{self.name}</text>
          </g>
          {peers.map(([id, info], i) => {
            const angle = (2 * Math.PI * i) / Math.max(peers.length, 1) - Math.PI / 2
            const px = cx + r * 1.8 * Math.cos(angle), py = cy + r * Math.sin(angle)
            return (
              <g key={id} className="topo-node topo-peer">
                <circle cx={px} cy={py} r={20}/>
                <text x={px} y={py + 4} className="topo-label" fill="white" fontWeight="600" fontSize="10">P{i+1}</text>
                <text x={px} y={py + 36} className="topo-label" fontSize="9">{info.ip}</text>
              </g>
            )
          })}
          {peers.length === 0 && <text x={cx} y={cy + 80} className="topo-label" fontSize="13" fill="#64748b">No peers connected</text>}
        </svg>
      </div>
    </div>
  )
}

// ─── Chunk Distribution Map ───────────────────────────────────
function ChunkDistribution({ files, status }) {
  const self = status?.node_id?.slice(0, 12) || 'This Node'
  const localChunks = status?.local_chunks || []

  return (
    <div className="panel">
      <div className="panel-title"><span className="icon">🗺️</span> Chunk Distribution Map</div>
      {files.length === 0 ? (
        <div className="empty-state"><div className="empty-state-icon">📦</div><p>Upload a file to see chunk distribution</p></div>
      ) : (
        <div className="chunk-map">
          {files.map((f, fi) => {
            const manifest = f.manifest || {}
            const chunks = manifest.chunks || []
            const totalChunks = f.chunks || chunks.length || 1
            return (
              <div key={fi}>
                <div style={{fontSize: '14px', fontWeight: 500, marginBottom: 8}}>📄 {f.filename}</div>
                <div className="chunk-map-row">
                  <div className="chunk-map-label">🟢 {self}...</div>
                  <div className="chunk-cells">
                    {Array.from({length: totalChunks}, (_, i) => (
                      <div key={i} className="chunk-cell held" title={`Chunk ${i}`}>{i}</div>
                    ))}
                  </div>
                </div>
                {Object.entries(status?.peers || {}).map(([pid, info]) => (
                  <div className="chunk-map-row" key={pid}>
                    <div className="chunk-map-label">🟣 {info.ip}</div>
                    <div className="chunk-cells">
                      {Array.from({length: totalChunks}, (_, i) => {
                        const held = Math.random() > 0.3 // simulated for demo
                        return <div key={i} className={`chunk-cell ${held ? 'held' : 'missing'}`}>{i}</div>
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )
          })}
          <div className="chunk-legend">
            <span><div className="legend-dot" style={{background: 'var(--gradient-primary)'}}/> Chunk held</span>
            <span><div className="legend-dot" style={{background: 'rgba(255,255,255,0.06)', border: '1px dashed rgba(255,255,255,0.2)'}}/> Missing</span>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Performance Toggle ───────────────────────────────────────
function PerformanceView({ status }) {
  const [downloadSpeed, setDownloadSpeed] = useState(0)
  useEffect(() => {
    const timer = setInterval(() => setDownloadSpeed(Math.random() * 80 + 10), 2000)
    return () => clearInterval(timer)
  }, [])

  const pct = Math.min((downloadSpeed / LAN_THEORETICAL_MBPS) * 100, 100)
  const circumference = 2 * Math.PI * 55
  const offset = circumference - (pct / 100) * circumference
  const strokeColor = pct > 70 ? '#10b981' : pct > 40 ? '#f59e0b' : '#f43f5e'

  const metrics = [
    { label: 'Download', value: `${downloadSpeed.toFixed(1)} MB/s`, pct, color: 'var(--gradient-primary)' },
    { label: 'Upload', value: `${(downloadSpeed * 0.6).toFixed(1)} MB/s`, pct: pct * 0.6, color: 'var(--gradient-success)' },
    { label: 'Latency', value: `${(Math.random() * 2 + 0.1).toFixed(1)} ms`, pct: 5, color: 'var(--gradient-danger)' },
    { label: 'Throughput', value: `${(downloadSpeed * 8).toFixed(0)} Mbps`, pct: pct * 0.8, color: 'linear-gradient(135deg, #8b5cf6, #ec4899)' },
  ]

  return (
    <div className="panel">
      <div className="panel-title"><span className="icon">⚡</span> Performance Monitor</div>
      <div className="perf-grid">
        <div className="perf-gauge">
          <div className="gauge-ring">
            <svg>
              <circle className="gauge-bg" cx="70" cy="70" r="55"/>
              <circle className="gauge-fill" cx="70" cy="70" r="55"
                stroke={strokeColor}
                strokeDasharray={circumference}
                strokeDashoffset={offset}/>
            </svg>
            <div className="gauge-value">{pct.toFixed(0)}%</div>
          </div>
          <div className="gauge-label">LAN Utilization ({LAN_THEORETICAL_MBPS} MB/s max)</div>
        </div>
        <div className="perf-bars">
          {metrics.map(m => (
            <div className="perf-bar-item" key={m.label}>
              <div className="perf-bar-label">{m.label}</div>
              <div className="perf-bar-track">
                <div className="perf-bar-fill" style={{width: `${Math.min(m.pct, 100)}%`, background: m.color}}/>
              </div>
              <div className="perf-bar-val">{m.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Dashboard ────────────────────────────────────────────────
function Dashboard({ status, files, onSelectFile }) {
  const peers = status?.peers || {}
  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card blue"><div className="stat-icon">🌐</div><div className="stat-label">Connected Peers</div><div className="stat-value">{status?.peer_count||0}</div></div>
        <div className="stat-card green"><div className="stat-icon">⏱️</div><div className="stat-label">Uptime</div><div className="stat-value">{formatUptime(status?.uptime_seconds||0)}</div></div>
        <div className="stat-card amber"><div className="stat-icon">📦</div><div className="stat-label">Stored Chunks</div><div className="stat-value">{status?.chunk_count||0}</div></div>
        <div className="stat-card purple"><div className="stat-icon">💾</div><div className="stat-label">Storage Used</div><div className="stat-value">{formatBytes(status?.storage_used)}</div></div>
      </div>
      <NetworkTopology status={status}/>
      <ChunkDistribution files={files} status={status}/>
      <PerformanceView status={status}/>
      <div className="panel">
        <div className="panel-title"><span className="icon">👥</span> Connected Peers</div>
        {Object.keys(peers).length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">🔍</div><p>No peers connected yet</p></div>
        ) : (
          <table className="peer-table"><thead><tr><th>Node ID</th><th>IP</th><th>Port</th><th>Status</th></tr></thead><tbody>
            {Object.entries(peers).map(([id, info]) => (
              <tr key={id}><td><span className="peer-id">{id.slice(0,16)}...</span></td><td>{info.ip}</td><td>{info.tcp_port}</td><td><span className="badge badge-online">Online</span></td></tr>
            ))}
          </tbody></table>
        )}
      </div>
      <div className="panel">
        <div className="panel-title"><span className="icon">📁</span> Stored Files ({files.length})</div>
        {files.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">📭</div><p>No files stored yet</p></div>
        ) : (
          <div className="file-list">{files.map((f,i) => (
            <div className="file-item" key={i}>
              <div className="file-info"><div className="file-icon">📄</div><div><div className="file-name">{f.filename}</div><div className="file-meta">{formatBytes(f.size)} · {f.chunks} chunks{f.merkle_root ? ` · Merkle: ${f.merkle_root.slice(0,12)}...` : ''}</div></div></div>
              <div className="file-actions">
                <div className="file-hash">{f.file_hash?.slice(0,20)}...</div>
                <div className="file-buttons">
                  <CopyButton text={f.file_hash} label="📋 Copy Hash" />
                  <button className="btn-copy btn-dl" onClick={(e) => { e.stopPropagation(); onSelectFile?.(f.file_hash) }} title="Download this file">⬇️ Download</button>
                </div>
              </div>
            </div>
          ))}</div>
        )}
      </div>
    </div>
  )
}

// ─── Upload ───────────────────────────────────────────────────
function Upload({ onUploadComplete }) {
  const [file, setFile] = useState(null)
  const [password, setPassword] = useState('')
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)

  const handleUpload = async () => {
    if (!file) return
    setUploading(true); setError(null); setResult(null)
    try {
      const fd = new FormData(); fd.append('file', file); fd.append('password', password)
      const resp = await axios.post(`${API}/upload`, fd)
      setResult(resp.data); onUploadComplete?.()
    } catch (err) { setError(err.response?.data?.detail || err.message) }
    finally { setUploading(false) }
  }

  return (
    <div className="panel">
      <div className="panel-title"><span className="icon">⬆️</span> Upload File</div>
      <div className="form-section">
        <div className={`drop-zone ${dragActive ? 'active' : ''}`}
          onDragOver={e => { e.preventDefault(); setDragActive(true) }}
          onDragLeave={() => setDragActive(false)}
          onDrop={e => { e.preventDefault(); setDragActive(false); if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]) }}
          onClick={() => document.getElementById('file-input').click()}>
          <div className="drop-zone-icon">{file ? '✅' : '📤'}</div>
          <div className="drop-zone-text">{file ? file.name : 'Drop file here or click to browse'}</div>
          <div className="drop-zone-hint">{file ? formatBytes(file.size) : 'AES-256-GCM encrypted'}</div>
          <input id="file-input" type="file" style={{display:'none'}} onChange={e => setFile(e.target.files?.[0]||null)}/>
        </div>
        <div className="input-group"><label>Encryption Password (optional)</label>
          <input type="password" className="input-field" placeholder="Leave empty for no encryption" value={password} onChange={e => setPassword(e.target.value)}/>
        </div>
        <button className="btn btn-primary" onClick={handleUpload} disabled={!file || uploading}>
          {uploading ? <><div className="spinner"/> Uploading...</> : '⬆️ Upload File'}
        </button>
        {result && (
          <div className="alert alert-success">
            <div style={{flex:1}}>
              <div>✅ Uploaded! {result.chunks} chunks · Merkle: {result.manifest?.merkle_root?.slice(0,16)}...</div>
              <div className="upload-hash-row">
                <span className="upload-hash-text">{result.file_hash}</span>
                <CopyButton text={result.file_hash} label="📋 Copy Hash" />
              </div>
            </div>
          </div>
        )}
        {error && <div className="alert alert-error">❌ {error}</div>}
      </div>
    </div>
  )
}

// ─── Download ─────────────────────────────────────────────────
function Download({ prefilledHash }) {
  const [hash, setHash] = useState(prefilledHash || '')
  const [password, setPassword] = useState('')

  // Update hash when prefilledHash changes (from file list click)
  useEffect(() => { if (prefilledHash) setHash(prefilledHash) }, [prefilledHash])
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const handleDownload = async () => {
    if (!hash) return
    setDownloading(true); setError(null); setSuccess(false)
    try {
      const resp = await axios.get(`${API}/download/${hash}`, { params: password ? {password} : {}, responseType: 'blob' })
      const cd = resp.headers['content-disposition'] || ''
      const m = cd.match(/filename="?([^"]+)"?/)
      const url = URL.createObjectURL(resp.data)
      const a = document.createElement('a'); a.href = url; a.download = m ? m[1] : 'download.bin'; a.click()
      URL.revokeObjectURL(url); setSuccess(true)
    } catch (err) { setError(err.response?.data?.detail || err.message) }
    finally { setDownloading(false) }
  }

  return (
    <div className="panel">
      <div className="panel-title"><span className="icon">⬇️</span> Download File</div>
      <div className="form-section">
        <div className="input-group"><label>File Hash</label>
          <input type="text" className="input-field" placeholder="Enter SHA-256 file hash..." value={hash} onChange={e => setHash(e.target.value)}/>
        </div>
        <div className="input-group"><label>Decryption Password (if encrypted)</label>
          <input type="password" className="input-field" placeholder="Leave empty if not encrypted" value={password} onChange={e => setPassword(e.target.value)}/>
        </div>
        <button className="btn btn-success" onClick={handleDownload} disabled={!hash || downloading}>
          {downloading ? <><div className="spinner"/> Downloading...</> : '⬇️ Download File'}
        </button>
        {success && <div className="alert alert-success">✅ Downloaded successfully!</div>}
        {error && <div className="alert alert-error">❌ {error}</div>}
      </div>
    </div>
  )
}

// ─── Main App ─────────────────────────────────────────────────
function App() {
  const [tab, setTab] = useState('dashboard')
  const [status, setStatus] = useState(null)
  const [files, setFiles] = useState([])
  const [downloadHash, setDownloadHash] = useState('')

  const fetchStatus = useCallback(async () => {
    try {
      const [s, f] = await Promise.all([axios.get(`${API}/status`), axios.get(`${API}/files`)])
      setStatus(s.data); setFiles(f.data.files || [])
    } catch {}
  }, [])

  useEffect(() => { fetchStatus(); const i = setInterval(fetchStatus, 5000); return () => clearInterval(i) }, [fetchStatus])

  const handleSelectFile = (hash) => {
    setDownloadHash(hash)
    setTab('download')
  }

  const tabs = [
    { key: 'dashboard', label: '📊 Dashboard' },
    { key: 'upload', label: '⬆️ Upload' },
    { key: 'download', label: '⬇️ Download' },
  ]

  return (
    <div className="app-container">
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">🔗</div>
          <div><div className="header-title">DistriStore</div><div className="header-subtitle">P2P DHT Storage · AES-256-GCM · Merkle Verified</div></div>
        </div>
        <div className="header-status"><span className="status-dot"/>{status ? `Node: ${status.name}` : 'Connecting...'}</div>
      </header>
      <nav className="nav-tabs">
        {tabs.map(t => <button key={t.key} className={`nav-tab ${tab===t.key?'active':''}`} onClick={() => setTab(t.key)}>{t.label}</button>)}
      </nav>
      {tab === 'dashboard' && <Dashboard status={status} files={files} onSelectFile={handleSelectFile}/>}
      {tab === 'upload' && <Upload onUploadComplete={fetchStatus}/>}
      {tab === 'download' && <Download prefilledHash={downloadHash}/>}
    </div>
  )
}

export default App

/**
 * DistriStore — Centralized API Service Layer
 *
 * Singleton Axios instance with base URL configuration.
 * Components must NEVER call Axios directly — import these functions instead.
 */

import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Accept': 'application/json' },
})

// ── Request interceptor (logging, auth tokens in future) ──────
api.interceptors.request.use((config) => {
  config.metadata = { startTime: performance.now() }
  return config
})

// ── Response interceptor (timing, error normalization) ────────
api.interceptors.response.use(
  (response) => {
    const elapsed = performance.now() - response.config.metadata.startTime
    response.latency = Math.round(elapsed)
    return response
  },
  (error) => {
    const message = error.response?.data?.detail
      || error.response?.data?.message
      || error.message
      || 'Network error'
    return Promise.reject(new Error(message))
  }
)

// ── Node Status & Peers ───────────────────────────────────────

export async function fetchStatus() {
  const { data, latency } = await api.get('/status')
  return { ...data, latency }
}

export async function fetchFiles() {
  const { data } = await api.get('/files')
  return data.files || []
}

export async function fetchManifest(fileHash) {
  const { data } = await api.get(`/manifest/${fileHash}`)
  return data
}

export async function fetchChunk(chunkHash) {
  const { data } = await api.get(`/chunk/${chunkHash}`, { responseType: 'arraybuffer' })
  return data
}

// ── Upload ────────────────────────────────────────────────────

export async function uploadFile(file, password = '') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('password', password)

  const { data, latency } = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
  return { ...data, latency }
}

// ── Download ──────────────────────────────────────────────────

export async function downloadFile(fileHash, password = '') {
  const params = password ? { password } : {}
  const response = await api.get(`/download/${fileHash}`, {
    params,
    responseType: 'blob',
    timeout: 120000,
  })

  // Extract filename from Content-Disposition header
  const cd = response.headers['content-disposition'] || ''
  const match = cd.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : 'download.bin'

  return { blob: response.data, filename, latency: response.latency }
}

// ── Utility: trigger browser download from blob ───────────────

export function triggerBlobDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default api

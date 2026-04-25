/**
 * DistriStore — Zustand Global State Store
 *
 * Single source of truth for node status, peers, files, and performance history.
 * Auto-polls /status and /files every 3 seconds — pages don't manage their own intervals.
 */

import { create } from 'zustand'
import { fetchStatus, fetchFiles } from '../api/client'

const MAX_HISTORY = 60 // Keep 60 data points (3min at 3s intervals)

const useNetworkStore = create((set, get) => ({
  // ── Node State ──────────────────────────────────────────────
  status: null,
  files: [],
  isConnected: false,
  lastUpdate: null,
  error: null,

  // ── Performance History (for charts) ────────────────────────
  latencyHistory: [],
  throughputHistory: [],

  // ── Polling ─────────────────────────────────────────────────
  pollingInterval: null,

  startPolling: (intervalMs = 3000) => {
    const { pollingInterval } = get()
    if (pollingInterval) return // Already polling

    // Immediate first fetch
    get().refresh()

    const id = setInterval(() => get().refresh(), intervalMs)
    set({ pollingInterval: id })
  },

  stopPolling: () => {
    const { pollingInterval } = get()
    if (pollingInterval) {
      clearInterval(pollingInterval)
      set({ pollingInterval: null })
    }
  },

  refresh: async () => {
    try {
      const [statusData, filesData] = await Promise.all([
        fetchStatus(),
        fetchFiles(),
      ])

      const now = Date.now()
      const latency = statusData.latency || 0

      set((state) => ({
        status: statusData,
        files: filesData,
        isConnected: true,
        lastUpdate: now,
        error: null,
        latencyHistory: [
          ...state.latencyHistory.slice(-(MAX_HISTORY - 1)),
          { time: now, value: latency },
        ],
        throughputHistory: [
          ...state.throughputHistory.slice(-(MAX_HISTORY - 1)),
          {
            time: now,
            download: Math.random() * 80 + 20, // placeholder until real metrics
            upload: Math.random() * 40 + 10,
          },
        ],
      }))
    } catch (err) {
      set({ isConnected: false, error: err.message })
    }
  },

  // ── Computed Helpers ────────────────────────────────────────
  getPeerCount: () => {
    const { status } = get()
    return Object.keys(status?.peers || {}).length
  },

  getPeerList: () => {
    const { status } = get()
    const peers = status?.peers || {}
    return Object.entries(peers).map(([id, info]) => ({
      id,
      name: info.name || id.slice(0, 12),
      host: info.host || 'unknown',
      port: info.port || 0,
      health_score: info.health_score || 0,
      lastSeen: info.last_seen || null,
    }))
  },

  getChunkCount: () => {
    const { status } = get()
    return status?.chunk_count || status?.local_chunks?.length || 0
  },

  getStorageUsed: () => {
    const { status } = get()
    return status?.storage_used || 0
  },
}))

export default useNetworkStore

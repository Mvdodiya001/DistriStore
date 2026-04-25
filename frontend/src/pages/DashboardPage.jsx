/**
 * DashboardPage — Main overview with stats, topology, peers, charts, and file list.
 */

import { useNavigate } from 'react-router-dom'
import { Globe, Clock, Database, HardDrive } from 'lucide-react'
import useNetworkStore from '../store/useNetworkStore'
import StatCard from '../components/ui/StatCard'
import Card from '../components/ui/Card'
import CopyButton from '../components/ui/CopyButton'
import NetworkTopology from '../components/network/NetworkTopology'
import PeerTable from '../components/network/PeerTable'
import TransferSpeedChart from '../components/network/TransferSpeedChart'

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

export default function DashboardPage() {
  const status = useNetworkStore((s) => s.status)
  const files = useNetworkStore((s) => s.files)
  const navigate = useNavigate()
  const peerCount = useNetworkStore((s) => s.getPeerCount())

  const handleSelectFile = (hash) => {
    navigate(`/download?hash=${hash}`)
  }

  return (
    <div>
      {/* Stats Grid */}
      <div className="stats-grid">
        <StatCard label="CONNECTED PEERS" value={peerCount} icon={<Globe size={20} />} color="var(--gradient-primary)" />
        <StatCard label="UPTIME" value={formatUptime(status?.uptime_seconds || 0)} icon={<Clock size={20} />} color="linear-gradient(135deg, #06b6d4, #10b981)" />
        <StatCard label="STORED CHUNKS" value={useNetworkStore.getState().getChunkCount()} icon={<Database size={20} />} color="linear-gradient(135deg, #f43f5e, #ec4899)" />
        <StatCard label="STORAGE USED" value={formatBytes(useNetworkStore.getState().getStorageUsed())} icon={<HardDrive size={20} />} color="linear-gradient(135deg, #8b5cf6, #6366f1)" />
      </div>

      {/* Network Visualizations */}
      <NetworkTopology />
      <TransferSpeedChart />

      {/* Peer Table */}
      <PeerTable />

      {/* Stored Files */}
      <Card title="Stored Files" icon="📁">
        {files.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">📭</div><p>No files stored yet</p></div>
        ) : (
          <div className="file-list">
            {files.map((f, i) => (
              <div className="file-item" key={i}>
                <div className="file-info">
                  <div className="file-icon">📄</div>
                  <div>
                    <div className="file-name">{f.filename}</div>
                    <div className="file-meta">
                      {formatBytes(f.size)} · {f.chunks} chunks
                      {f.merkle_root ? ` · Merkle: ${f.merkle_root.slice(0, 12)}...` : ''}
                    </div>
                  </div>
                </div>
                <div className="file-actions">
                  <div className="file-hash">{f.file_hash?.slice(0, 20)}...</div>
                  <div className="file-buttons">
                    <CopyButton text={f.file_hash} label="Copy Hash" />
                    <button
                      className="btn-copy btn-dl"
                      onClick={() => handleSelectFile(f.file_hash)}
                      title="Download this file"
                    >
                      ⬇️ Download
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

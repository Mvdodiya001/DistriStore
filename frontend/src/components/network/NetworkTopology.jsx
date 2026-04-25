/**
 * NetworkTopology — SVG-based topology visualization.
 * Shows self node at center with peer connections radiating outward.
 */

import useNetworkStore from '../../store/useNetworkStore'
import Card from '../ui/Card'

export default function NetworkTopology() {
  const status = useNetworkStore((s) => s.status)
  const self = { id: status?.node_id || '', name: status?.name || 'This Node' }
  const peers = Object.entries(status?.peers || {})
  const cx = 400, cy = 180, r = 120

  return (
    <Card title="Network Topology" icon="🕸️">
      <div className="topology-canvas">
        <svg viewBox="0 0 800 360">
          {/* Connection lines */}
          {peers.map(([id, info], i) => {
            const angle = (2 * Math.PI * i) / Math.max(peers.length, 1)
            const px = cx + r * Math.cos(angle)
            const py = cy + r * Math.sin(angle)
            return (
              <line key={`line-${id}`} x1={cx} y1={cy} x2={px} y2={py}
                stroke="url(#topo-gradient)" strokeWidth="2" opacity="0.6"
                className="topo-line" />
            )
          })}

          {/* Gradient definition */}
          <defs>
            <linearGradient id="topo-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#a855f7" />
              <stop offset="100%" stopColor="#3b82f6" />
            </linearGradient>
          </defs>

          {/* Self node */}
          <circle cx={cx} cy={cy} r="24" fill="rgba(139,92,246,0.3)" stroke="#a855f7" strokeWidth="2" className="topo-node-self" />
          <text x={cx} y={cy + 4} textAnchor="middle" fill="#a855f7" fontSize="11" fontWeight="700">ME</text>
          <text x={cx} y={cy + 42} textAnchor="middle" fill="#94a3b8" fontSize="11">{self.name}</text>

          {/* Peer nodes */}
          {peers.map(([id, info], i) => {
            const angle = (2 * Math.PI * i) / Math.max(peers.length, 1)
            const px = cx + r * Math.cos(angle)
            const py = cy + r * Math.sin(angle)
            return (
              <g key={id}>
                <circle cx={px} cy={py} r="18" fill="rgba(59,130,246,0.2)" stroke="#3b82f6" strokeWidth="1.5" className="topo-node" />
                <text x={px} y={py + 4} textAnchor="middle" fill="#93c5fd" fontSize="9">{(info.name || id).slice(0, 6)}</text>
              </g>
            )
          })}

          {/* Empty state */}
          {peers.length === 0 && (
            <text x={cx} y={cy + 70} textAnchor="middle" fill="#64748b" fontSize="12">No peers connected</text>
          )}
        </svg>
      </div>
    </Card>
  )
}

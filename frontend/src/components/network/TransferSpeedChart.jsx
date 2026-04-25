/**
 * TransferSpeedChart — Real-time line chart showing upload/download throughput.
 * Reads from Zustand global store — no props needed.
 */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import useNetworkStore from '../../store/useNetworkStore'
import Card from '../ui/Card'

function formatTime(ts) {
  const d = new Date(ts)
  return d.toLocaleTimeString([], { minute: '2-digit', second: '2-digit' })
}

export default function TransferSpeedChart() {
  const throughputHistory = useNetworkStore((s) => s.throughputHistory)

  const data = throughputHistory.map((d) => ({
    time: formatTime(d.time),
    Download: d.download.toFixed(1),
    Upload: d.upload.toFixed(1),
  }))

  return (
    <Card title="Transfer Speed" icon="📈">
      <div style={{ width: '100%', height: 250 }}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="time"
              stroke="rgba(255,255,255,0.3)"
              tick={{ fontSize: 11, fill: 'rgba(255,255,255,0.5)' }}
              interval="preserveStartEnd"
            />
            <YAxis
              stroke="rgba(255,255,255,0.3)"
              tick={{ fontSize: 11, fill: 'rgba(255,255,255,0.5)' }}
              label={{ value: 'MB/s', angle: -90, position: 'insideLeft', style: { fill: 'rgba(255,255,255,0.4)', fontSize: 11 } }}
            />
            <Tooltip
              contentStyle={{
                background: 'rgba(15,23,42,0.95)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 8,
                color: '#e2e8f0',
                fontSize: 12,
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
            <Line
              type="monotone"
              dataKey="Download"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              animationDuration={300}
            />
            <Line
              type="monotone"
              dataKey="Upload"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              animationDuration={300}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

/**
 * StatCard — Metric card with gradient top border, icon, label, and value.
 */

export default function StatCard({ label, value, icon, color = 'var(--accent-purple)' }) {
  return (
    <div className="stat-card">
      <div className="stat-bar" style={{ background: color }} />
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {icon && <div className="stat-icon">{icon}</div>}
    </div>
  )
}

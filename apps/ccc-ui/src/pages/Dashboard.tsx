import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

interface DashboardData {
  students: number
  infra_nodes: number
  labs_completed: number
  ctf_solved: number
  battles: number
  blocks: number
}

const cardStyle: React.CSSProperties = {
  background: '#161b22',
  border: '1px solid #30363d',
  borderRadius: 8,
  padding: 24,
  display: 'flex',
  flexDirection: 'column',
  gap: 8,
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api<DashboardData>('/api/dashboard')
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [])

  const stats = data
    ? [
        { label: 'Students', value: data.students, icon: '\u{1F9D1}\u200D\u{1F393}' },
        { label: 'Infra Nodes', value: data.infra_nodes, icon: '\u{1F5A5}\uFE0F' },
        { label: 'Labs Completed', value: data.labs_completed, icon: '\u2705' },
        { label: 'CTF Solved', value: data.ctf_solved, icon: '\u{1F3AF}' },
        { label: 'Battles', value: data.battles, icon: '\u2694\uFE0F' },
        { label: 'Blocks', value: data.blocks, icon: '\u26D3\uFE0F' },
      ]
    : []

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#e6edf3' }}>
        Dashboard
      </h2>

      {loading ? (
        <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
      ) : !data ? (
        <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>
          No data available. Is the CCC API running on :9100?
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
          gap: 16,
        }}>
          {stats.map(s => (
            <div key={s.label} style={cardStyle}>
              <div style={{ fontSize: 28 }}>{s.icon}</div>
              <div style={{ fontSize: 32, fontWeight: 700, color: '#f97316' }}>{s.value}</div>
              <div style={{ fontSize: 13, color: '#8b949e' }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

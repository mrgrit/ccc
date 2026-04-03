import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

export default function Dashboard() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/api/dashboard')
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
  if (error) return <div style={{ color: '#f85149', padding: 40, textAlign: 'center' }}>Error: {error}</div>
  if (!data) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>No data</div>

  const stats = [
    { label: 'Students', value: data.students ?? 0, color: '#a78bfa' },
    { label: 'Infras', value: data.infras ?? 0, color: '#58a6ff' },
    { label: 'Labs Done', value: data.labs_completed ?? 0, color: '#3fb950' },
    { label: 'CTF Solved', value: data.ctf_solved ?? 0, color: '#d29922' },
    { label: 'Battles', value: data.battles ?? 0, color: '#f97316' },
    { label: 'Blocks', value: data.blockchain_blocks ?? 0, color: '#f0883e' },
  ]

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#e6edf3' }}>Dashboard</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16 }}>
        {stats.map(s => (
          <div key={s.label} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 24 }}>
            <div style={{ fontSize: 32, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 13, color: '#8b949e', marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

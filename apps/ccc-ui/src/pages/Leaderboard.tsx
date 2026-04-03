import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

const cats = ['total', 'lab', 'ctf', 'battle'] as const

export default function Leaderboard() {
  const [rows, setRows] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [cat, setCat] = useState('total')

  useEffect(() => {
    setLoading(true)
    api(`/api/leaderboard?category=${cat}`)
      .then(d => setRows(d.leaderboard || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [cat])

  if (error) return <div style={{ color: '#f85149', padding: 40 }}>Error: {error}</div>

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#e6edf3' }}>Leaderboard</h2>

      <div style={{ display: 'flex', gap: 6, marginBottom: 20 }}>
        {cats.map(c => (
          <button key={c} onClick={() => setCat(c)} style={{
            padding: '6px 16px', borderRadius: 6, fontSize: 13, cursor: 'pointer',
            background: cat === c ? '#f97316' : 'transparent', color: cat === c ? '#fff' : '#8b949e',
            border: cat === c ? 'none' : '1px solid #30363d', fontWeight: cat === c ? 600 : 400,
          }}>{c.toUpperCase()}</button>
        ))}
      </div>

      {loading ? (
        <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
      ) : rows.length === 0 ? (
        <div style={{ color: '#8b949e', background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 40, textAlign: 'center' }}>No leaderboard data</div>
      ) : (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr style={{ borderBottom: '1px solid #30363d' }}>
              {['#', 'Name', 'ID', 'CTF', 'Lab', 'Battle'].map(h => (
                <th key={h} style={{ textAlign: h === 'Name' || h === 'ID' ? 'left' : 'center', padding: '12px 16px', fontSize: 12, color: '#8b949e', fontWeight: 600 }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #21262d', background: i < 3 ? 'rgba(249,115,22,0.04)' : 'transparent' }}>
                  <td style={{ padding: '12px 16px', textAlign: 'center', fontWeight: 700, color: i === 0 ? '#ffd700' : i === 1 ? '#c0c0c0' : i === 2 ? '#cd7f32' : '#8b949e' }}>#{i + 1}</td>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>{r.name}</td>
                  <td style={{ padding: '12px 16px', fontSize: 12, color: '#8b949e' }}><code>{r.student_id}</code></td>
                  <td style={{ padding: '12px 16px', textAlign: 'center', color: cat === 'ctf' ? '#f97316' : '#8b949e' }}>{r.ctf_score ?? r.score ?? 0}</td>
                  <td style={{ padding: '12px 16px', textAlign: 'center', color: cat === 'lab' ? '#f97316' : '#8b949e' }}>{r.lab_score ?? r.score ?? 0}</td>
                  <td style={{ padding: '12px 16px', textAlign: 'center', color: cat === 'battle' ? '#f97316' : '#8b949e' }}>{r.battle_score ?? r.score ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

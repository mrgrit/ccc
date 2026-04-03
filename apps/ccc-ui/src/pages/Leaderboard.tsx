import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

interface LeaderboardEntry {
  rank: number
  name: string
  total_score: number
  lab_score: number
  ctf_score: number
  battle_score: number
}

type Category = 'total' | 'lab' | 'ctf' | 'battle'

const sortKey: Record<Category, keyof LeaderboardEntry> = {
  total: 'total_score',
  lab: 'lab_score',
  ctf: 'ctf_score',
  battle: 'battle_score',
}

export default function Leaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState<Category>('total')

  useEffect(() => {
    api<LeaderboardEntry[]>('/api/leaderboard')
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false))
  }, [])

  const sorted = [...entries].sort((a, b) => {
    const key = sortKey[category]
    return (b[key] as number) - (a[key] as number)
  })

  const tabs: { key: Category; label: string }[] = [
    { key: 'total', label: 'Total' },
    { key: 'lab', label: 'Lab' },
    { key: 'ctf', label: 'CTF' },
    { key: 'battle', label: 'Battle' },
  ]

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#e6edf3' }}>
        Leaderboard
      </h2>

      <div style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setCategory(t.key)}
            style={{
              padding: '8px 20px',
              borderRadius: 6,
              border: '1px solid #30363d',
              background: category === t.key ? '#f97316' : 'transparent',
              color: category === t.key ? '#fff' : '#8b949e',
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: category === t.key ? 600 : 400,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
      ) : sorted.length === 0 ? (
        <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>
          No leaderboard data. Is the CCC API running on :9100?
        </div>
      ) : (
        <div style={{
          background: '#161b22',
          border: '1px solid #30363d',
          borderRadius: 8,
          overflow: 'hidden',
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #30363d' }}>
                {['Rank', 'Name', 'Total', 'Lab', 'CTF', 'Battle'].map(h => (
                  <th key={h} style={{
                    padding: '12px 16px',
                    textAlign: h === 'Name' ? 'left' : 'center',
                    fontSize: 12,
                    fontWeight: 600,
                    color: '#8b949e',
                    textTransform: 'uppercase' as const,
                    letterSpacing: 0.5,
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((e, i) => (
                <tr key={e.name} style={{
                  borderBottom: i < sorted.length - 1 ? '1px solid #21262d' : 'none',
                  background: i < 3 ? 'rgba(249,115,22,0.04)' : 'transparent',
                }}>
                  <td style={{ padding: '12px 16px', textAlign: 'center', fontWeight: 700 }}>
                    <span style={{
                      color: i === 0 ? '#ffd700' : i === 1 ? '#c0c0c0' : i === 2 ? '#cd7f32' : '#8b949e',
                      fontSize: 16,
                    }}>
                      {i + 1}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#e6edf3' }}>{e.name}</td>
                  <td style={{
                    padding: '12px 16px', textAlign: 'center', fontWeight: 700,
                    color: category === 'total' ? '#f97316' : '#e6edf3',
                  }}>
                    {e.total_score}
                  </td>
                  <td style={{
                    padding: '12px 16px', textAlign: 'center',
                    color: category === 'lab' ? '#f97316' : '#8b949e',
                    fontWeight: category === 'lab' ? 700 : 400,
                  }}>
                    {e.lab_score}
                  </td>
                  <td style={{
                    padding: '12px 16px', textAlign: 'center',
                    color: category === 'ctf' ? '#f97316' : '#8b949e',
                    fontWeight: category === 'ctf' ? 700 : 400,
                  }}>
                    {e.ctf_score}
                  </td>
                  <td style={{
                    padding: '12px 16px', textAlign: 'center',
                    color: category === 'battle' ? '#f97316' : '#8b949e',
                    fontWeight: category === 'battle' ? 700 : 400,
                  }}>
                    {e.battle_score}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

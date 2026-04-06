import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

const typeColor: Record<string, string> = {
  lab_complete: '#3fb950', ctf_solve: '#58a6ff', battle_join: '#d29922',
  battle_win: '#f97316', rank_up: '#bc8cff', bug_report: '#f85149',
}

export default function Blockchain() {
  const [blocks, setBlocks] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api('/api/cccnet/blocks?limit=100').then(d => setBlocks(d.blocks || [])),
      api('/api/cccnet/stats').then(setStats),
    ]).catch(e => setError(e.message)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
  if (error) return <div style={{ color: '#f85149', padding: 40, textAlign: 'center' }}>Error: {error}</div>

  const byType = stats?.by_type || {}

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#e6edf3' }}>CCCNet Blockchain</h2>

      {stats && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
          {[
            { label: 'Total Blocks', value: stats.total_blocks, color: '#f97316' },
            { label: 'Total Points', value: stats.total_points, color: '#3fb950' },
            { label: 'Types Active', value: Object.keys(byType).length, color: '#58a6ff' },
          ].map(s => (
            <div key={s.label} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: '20px 24px', flex: 1, textAlign: 'center' as const }}>
              <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 12, color: '#8b949e', marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Block type breakdown */}
      {Object.keys(byType).length > 0 && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
          {Object.entries(byType).map(([type, data]: [string, any]) => (
            <span key={type} style={{
              padding: '4px 12px', borderRadius: 10, fontSize: 12, fontWeight: 600,
              background: `${typeColor[type] || '#8b949e'}15`, color: typeColor[type] || '#8b949e',
            }}>{type}: {data.count || 0} ({data.total_points || 0}pt)</span>
          ))}
        </div>
      )}

      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden' }}>
        {blocks.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#8b949e' }}>No blocks yet</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr style={{ borderBottom: '1px solid #30363d' }}>
              {['#', 'Hash', 'Student', 'Type', 'Points'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '12px 16px', fontSize: 12, color: '#8b949e', fontWeight: 600 }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {blocks.map((b, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #21262d' }}>
                  <td style={{ padding: '12px 16px', color: '#f97316', fontWeight: 600 }}>{b.block_index}</td>
                  <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontSize: 12, color: '#8b949e' }}>{b.block_hash?.slice(0, 16)}...</td>
                  <td style={{ padding: '12px 16px', fontSize: 13 }}><code>{b.student_id}</code></td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 10, fontWeight: 600,
                      background: `${typeColor[b.block_type] || '#8b949e'}15`,
                      color: typeColor[b.block_type] || '#8b949e',
                    }}>{b.block_type}</span>
                  </td>
                  <td style={{ padding: '12px 16px', color: '#3fb950', fontWeight: 600 }}>+{b.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

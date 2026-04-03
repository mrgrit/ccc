import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

export default function Blockchain() {
  const [blocks, setBlocks] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api('/api/blockchain/blocks').then(d => setBlocks(d.blocks || [])),
      api('/api/blockchain/stats').then(setStats),
    ]).catch(e => setError(e.message)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
  if (error) return <div style={{ color: '#f85149', padding: 40, textAlign: 'center' }}>Error: {error}</div>

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#e6edf3' }}>Blockchain</h2>

      {stats && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
          {[
            { label: 'Total Blocks', value: stats.total_blocks, color: '#f97316' },
            { label: 'Total Reward', value: stats.total_reward?.toFixed(1), color: '#3fb950' },
            { label: 'Agents', value: stats.agents, color: '#58a6ff' },
          ].map(s => (
            <div key={s.label} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: '20px 24px', flex: 1, textAlign: 'center' as const }}>
              <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 12, color: '#8b949e', marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden' }}>
        {blocks.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#8b949e' }}>No blocks yet</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr style={{ borderBottom: '1px solid #30363d' }}>
              {['#', 'Hash', 'Agent', 'Type', 'Reward'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '12px 16px', fontSize: 12, color: '#8b949e', fontWeight: 600 }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {blocks.map((b, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #21262d' }}>
                  <td style={{ padding: '12px 16px', color: '#f97316', fontWeight: 600 }}>{b.block_index}</td>
                  <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontSize: 12, color: '#8b949e' }}>{b.block_hash?.slice(0, 16)}...</td>
                  <td style={{ padding: '12px 16px', fontSize: 13 }}><code>{b.agent_id}</code></td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 10, fontWeight: 600, background: b.context_type === 'lab' ? '#0d2818' : '#2d1b00', color: b.context_type === 'lab' ? '#3fb950' : '#f97316' }}>{b.context_type}</span>
                  </td>
                  <td style={{ padding: '12px 16px', color: '#3fb950', fontWeight: 600 }}>+{b.reward_amount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

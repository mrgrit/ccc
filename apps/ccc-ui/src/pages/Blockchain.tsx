import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

interface Block {
  index: number
  hash: string
  prev_hash: string
  agent_id: string
  context_type: string
  reward: number
  timestamp?: string
}

interface BlockchainStats {
  total_blocks: number
  total_reward: number
  agents: number
}

const cardStyle: React.CSSProperties = {
  background: '#161b22',
  border: '1px solid #30363d',
  borderRadius: 8,
  padding: 20,
}

export default function Blockchain() {
  const [blocks, setBlocks] = useState<Block[]>([])
  const [stats, setStats] = useState<BlockchainStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api<Block[]>('/api/blockchain/blocks').catch(() => []),
      api<BlockchainStats>('/api/blockchain/stats').catch(() => null),
    ]).then(([b, s]) => {
      setBlocks(b)
      setStats(s)
    }).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#e6edf3' }}>
        Blockchain
      </h2>

      {stats && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
          {[
            { label: 'Total Blocks', value: stats.total_blocks },
            { label: 'Total Reward', value: stats.total_reward.toFixed(2) },
            { label: 'Agents', value: stats.agents },
          ].map(s => (
            <div key={s.label} style={{ ...cardStyle, flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#f97316' }}>{s.value}</div>
              <div style={{ fontSize: 12, color: '#8b949e', marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
      ) : blocks.length === 0 ? (
        <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>
          No blocks found. Is the CCC API running on :9100?
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
                {['#', 'Hash', 'Agent', 'Context', 'Reward', 'Time'].map(h => (
                  <th key={h} style={{
                    padding: '12px 16px',
                    textAlign: 'left',
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
              {blocks.map((b, i) => (
                <tr key={b.index} style={{
                  borderBottom: i < blocks.length - 1 ? '1px solid #21262d' : 'none',
                }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#f97316' }}>
                    {b.index}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontSize: 12, color: '#8b949e' }}>
                    {b.hash.substring(0, 16)}...
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 13, color: '#e6edf3' }}>
                    {b.agent_id}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      fontSize: 11,
                      padding: '2px 8px',
                      borderRadius: 10,
                      background: 'rgba(249,115,22,0.12)',
                      color: '#f97316',
                      fontWeight: 600,
                    }}>
                      {b.context_type}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#3fb950' }}>
                    +{b.reward.toFixed(2)}
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 12, color: '#484f58' }}>
                    {b.timestamp || '-'}
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

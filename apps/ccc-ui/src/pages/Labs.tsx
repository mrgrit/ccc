import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

interface Lab {
  id: string
  title: string
  version: 'non-ai' | 'ai'
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  steps: number
  points: number
  description?: string
}

const difficultyColors: Record<string, string> = {
  beginner: '#3fb950',
  intermediate: '#58a6ff',
  advanced: '#d29922',
  expert: '#f85149',
}

const cardStyle: React.CSSProperties = {
  background: '#161b22',
  border: '1px solid #30363d',
  borderRadius: 8,
  padding: 20,
  display: 'flex',
  flexDirection: 'column',
  gap: 12,
}

export default function Labs() {
  const [labs, setLabs] = useState<Lab[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'non-ai' | 'ai'>('all')

  useEffect(() => {
    api<Lab[]>('/api/labs/catalog')
      .then(setLabs)
      .catch(() => setLabs([]))
      .finally(() => setLoading(false))
  }, [])

  const filtered = filter === 'all' ? labs : labs.filter(l => l.version === filter)

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, color: '#e6edf3' }}>Labs</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          {(['all', 'non-ai', 'ai'] as const).map(v => (
            <button
              key={v}
              onClick={() => setFilter(v)}
              style={{
                padding: '6px 16px',
                borderRadius: 6,
                border: '1px solid #30363d',
                background: filter === v ? (v === 'ai' ? '#f97316' : v === 'non-ai' ? '#58a6ff' : '#30363d') : 'transparent',
                color: filter === v ? '#fff' : '#8b949e',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: filter === v ? 600 : 400,
              }}
            >
              {v === 'all' ? 'All' : v === 'non-ai' ? 'Non-AI' : 'AI'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
      ) : filtered.length === 0 ? (
        <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>
          No labs found. {labs.length === 0 ? 'Is the CCC API running on :9100?' : 'Try a different filter.'}
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: 16,
        }}>
          {filtered.map(lab => (
            <div key={lab.id} style={{
              ...cardStyle,
              borderLeft: `3px solid ${lab.version === 'ai' ? '#f97316' : '#58a6ff'}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3', flex: 1 }}>{lab.title}</h3>
                <span style={{
                  fontSize: 11,
                  padding: '2px 8px',
                  borderRadius: 10,
                  background: lab.version === 'ai' ? 'rgba(249,115,22,0.15)' : 'rgba(88,166,255,0.15)',
                  color: lab.version === 'ai' ? '#f97316' : '#58a6ff',
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                  marginLeft: 8,
                }}>
                  {lab.version === 'ai' ? 'AI' : 'Non-AI'}
                </span>
              </div>
              {lab.description && (
                <div style={{ fontSize: 13, color: '#8b949e', lineHeight: 1.4 }}>{lab.description}</div>
              )}
              <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 'auto' }}>
                <span style={{
                  fontSize: 11,
                  padding: '2px 8px',
                  borderRadius: 10,
                  background: `${difficultyColors[lab.difficulty]}22`,
                  color: difficultyColors[lab.difficulty],
                  fontWeight: 600,
                }}>
                  {lab.difficulty}
                </span>
                <span style={{ fontSize: 12, color: '#8b949e' }}>{lab.steps} steps</span>
                <span style={{ fontSize: 12, color: '#f97316', fontWeight: 600, marginLeft: 'auto' }}>
                  {lab.points} pts
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

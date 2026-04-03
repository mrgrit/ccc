import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

const diffColor: Record<string, string> = { easy: '#3fb950', medium: '#d29922', hard: '#f85149' }

export default function Labs() {
  const [labs, setLabs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState<'all' | 'non-ai' | 'ai'>('all')

  useEffect(() => {
    api('/api/labs/catalog')
      .then(d => setLabs(d.labs || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const filtered = filter === 'all' ? labs : labs.filter(l => l.version === filter)

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
  if (error) return <div style={{ color: '#f85149', padding: 40, textAlign: 'center' }}>Error: {error}</div>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, color: '#e6edf3' }}>Labs ({filtered.length})</h2>
        <div style={{ display: 'flex', gap: 6 }}>
          {(['all', 'non-ai', 'ai'] as const).map(v => (
            <button key={v} onClick={() => setFilter(v)} style={{
              padding: '6px 16px', borderRadius: 6, fontSize: 13, cursor: 'pointer',
              border: '1px solid #30363d',
              background: filter === v ? (v === 'ai' ? '#f97316' : v === 'non-ai' ? '#58a6ff' : '#30363d') : 'transparent',
              color: filter === v ? '#fff' : '#8b949e', fontWeight: filter === v ? 600 : 400,
            }}>{v === 'all' ? 'All' : v === 'non-ai' ? 'Non-AI' : 'AI'}</button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div style={{ color: '#8b949e', background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 40, textAlign: 'center' }}>
          {labs.length === 0 ? 'No labs found.' : 'No labs match this filter.'}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
          {filtered.map(lab => (
            <div key={lab.lab_id} style={{
              background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 20,
              borderLeft: `3px solid ${lab.version === 'ai' ? '#f97316' : '#58a6ff'}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 11, color: '#8b949e' }}>
                  {lab.course} / Week {lab.week}
                </span>
                <span style={{
                  fontSize: 11, padding: '2px 8px', borderRadius: 10, fontWeight: 600,
                  background: lab.version === 'ai' ? 'rgba(249,115,22,0.15)' : 'rgba(88,166,255,0.15)',
                  color: lab.version === 'ai' ? '#f97316' : '#58a6ff',
                }}>{lab.version === 'ai' ? 'AI' : 'Non-AI'}</span>
              </div>
              <h3 style={{ fontSize: 15, fontWeight: 600, color: '#e6edf3', marginBottom: 10 }}>{lab.title}</h3>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', fontSize: 12 }}>
                <span style={{ padding: '2px 8px', borderRadius: 10, color: diffColor[lab.difficulty] || '#8b949e', background: `${diffColor[lab.difficulty] || '#484f58'}22` }}>{lab.difficulty}</span>
                <span style={{ color: '#8b949e' }}>{lab.steps} steps</span>
                <span style={{ color: lab.valid ? '#3fb950' : '#f85149', fontSize: 11 }}>{lab.valid ? 'valid' : 'errors'}</span>
                <span style={{ color: '#f97316', fontWeight: 600, marginLeft: 'auto' }}>{lab.total_points} pts</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

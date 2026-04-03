import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

const diffColor: Record<string, string> = { easy: '#3fb950', medium: '#d29922', hard: '#f85149' }
const catColor: Record<string, string> = { recon: '#58a6ff', exploit: '#f85149', defense: '#3fb950', analysis: '#d29922', response: '#bc8cff' }

export default function Labs() {
  const [labs, setLabs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState<'all' | 'non-ai' | 'ai'>('all')
  const [selected, setSelected] = useState<any>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    api('/api/labs/catalog')
      .then(d => setLabs(d.labs || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const openDetail = async (labId: string) => {
    setDetailLoading(true)
    try {
      const d = await api(`/api/labs/catalog/${labId}`)
      setSelected(d)
    } catch (e: any) {
      alert('Failed to load: ' + e.message)
    }
    setDetailLoading(false)
  }

  const filtered = filter === 'all' ? labs : labs.filter(l => l.version === filter)

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
  if (error) return <div style={{ color: '#f85149', padding: 40, textAlign: 'center' }}>Error: {error}</div>

  return (
    <div style={{ display: 'flex', gap: 24 }}>
      {/* Left: Lab list */}
      <div style={{ flex: selected ? '0 0 380px' : 1, transition: 'flex 0.2s' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: '#e6edf3' }}>Labs ({filtered.length})</h2>
          <div style={{ display: 'flex', gap: 6 }}>
            {(['all', 'non-ai', 'ai'] as const).map(v => (
              <button key={v} onClick={() => setFilter(v)} style={{
                padding: '6px 14px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
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
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {filtered.map(lab => (
              <div key={lab.lab_id} onClick={() => openDetail(lab.lab_id)} style={{
                background: selected?.lab_id === lab.lab_id ? '#1c2333' : '#161b22',
                border: selected?.lab_id === lab.lab_id ? '1px solid #f97316' : '1px solid #30363d',
                borderRadius: 8, padding: 16, cursor: 'pointer',
                borderLeft: `3px solid ${lab.version === 'ai' ? '#f97316' : '#58a6ff'}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 11, color: '#8b949e' }}>Week {lab.week}</span>
                  <span style={{
                    fontSize: 10, padding: '1px 6px', borderRadius: 10, fontWeight: 600,
                    background: lab.version === 'ai' ? 'rgba(249,115,22,0.15)' : 'rgba(88,166,255,0.15)',
                    color: lab.version === 'ai' ? '#f97316' : '#58a6ff',
                  }}>{lab.version === 'ai' ? 'AI' : 'Non-AI'}</span>
                </div>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#e6edf3', marginBottom: 6 }}>{lab.title}</div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 11 }}>
                  <span style={{ color: diffColor[lab.difficulty] || '#8b949e' }}>{lab.difficulty}</span>
                  <span style={{ color: '#484f58' }}>{lab.steps} steps</span>
                  <span style={{ color: '#f97316', fontWeight: 600, marginLeft: 'auto' }}>{lab.total_points}pts</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right: Detail panel */}
      {selected && (
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ position: 'sticky', top: 0 }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
              <div>
                <div style={{ fontSize: 12, color: '#8b949e', marginBottom: 4 }}>{selected.course} / Week {selected.week}</div>
                <h2 style={{ fontSize: 20, fontWeight: 700, color: '#e6edf3' }}>{selected.title}</h2>
              </div>
              <button onClick={() => setSelected(null)} style={{
                background: '#21262d', color: '#8b949e', border: '1px solid #30363d',
                borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 12,
              }}>Close</button>
            </div>

            {/* Meta */}
            <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 12, padding: '3px 10px', borderRadius: 10, background: '#21262d', color: diffColor[selected.difficulty] || '#8b949e' }}>{selected.difficulty}</span>
              <span style={{ fontSize: 12, color: '#8b949e' }}>{selected.duration_minutes}min</span>
              <span style={{ fontSize: 12, color: '#8b949e' }}>Pass: {Math.round(selected.pass_threshold * 100)}%</span>
              <span style={{ fontSize: 12, color: '#f97316', fontWeight: 600 }}>{selected.total_points} pts</span>
            </div>

            {/* Description */}
            {selected.description && (
              <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16, marginBottom: 16, fontSize: 13, color: '#8b949e', lineHeight: 1.6 }}>
                {selected.description}
              </div>
            )}

            {/* Objectives */}
            {selected.objectives?.length > 0 && (
              <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16, marginBottom: 16 }}>
                <h4 style={{ fontSize: 13, color: '#e6edf3', marginBottom: 8 }}>Objectives</h4>
                {selected.objectives.map((o: string, i: number) => (
                  <div key={i} style={{ fontSize: 12, color: '#8b949e', padding: '3px 0', display: 'flex', gap: 8 }}>
                    <span style={{ color: '#3fb950' }}>-</span> {o}
                  </div>
                ))}
              </div>
            )}

            {/* Steps */}
            <h4 style={{ fontSize: 14, color: '#e6edf3', marginBottom: 12 }}>Steps ({selected.steps?.length})</h4>
            {detailLoading ? (
              <div style={{ color: '#8b949e' }}>Loading...</div>
            ) : (
              selected.steps?.map((s: any, i: number) => (
                <div key={i} style={{
                  background: '#161b22', border: '1px solid #30363d', borderRadius: 8,
                  padding: 16, marginBottom: 10,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span style={{ background: '#21262d', borderRadius: '50%', width: 24, height: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, color: '#f97316', fontWeight: 700 }}>{s.order}</span>
                      {s.category && <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 10, background: `${catColor[s.category] || '#484f58'}22`, color: catColor[s.category] || '#8b949e' }}>{s.category}</span>}
                    </div>
                    <span style={{ fontSize: 12, color: '#f97316', fontWeight: 600 }}>{s.points}pts</span>
                  </div>

                  <div style={{ fontSize: 13, color: '#e6edf3', marginBottom: 8, lineHeight: 1.5 }}>{s.instruction}</div>

                  {s.hint && (
                    <div style={{ fontSize: 12, color: '#58a6ff', background: '#0d1f3c', borderRadius: 6, padding: '8px 12px', marginBottom: 8 }}>
                      Hint: {s.hint}
                    </div>
                  )}

                  {s.script && (
                    <div style={{ fontSize: 12, fontFamily: 'monospace', color: '#3fb950', background: '#0d1f0d', borderRadius: 6, padding: '8px 12px', marginBottom: 8, whiteSpace: 'pre-wrap' as const, wordBreak: 'break-all' as const }}>
                      $ {s.script}
                    </div>
                  )}

                  {s.verify && (
                    <div style={{ fontSize: 11, color: '#8b949e', display: 'flex', gap: 8 }}>
                      <span>Verify:</span>
                      <code style={{ color: '#d29922' }}>{s.verify.type}</code>
                      <code style={{ color: '#bc8cff' }}>"{s.verify.expect}"</code>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

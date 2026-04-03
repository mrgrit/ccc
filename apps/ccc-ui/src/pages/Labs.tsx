import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

const diffColor: Record<string, string> = { easy: '#3fb950', medium: '#d29922', hard: '#f85149' }
const catColor: Record<string, string> = { recon: '#58a6ff', exploit: '#f85149', defense: '#3fb950', analysis: '#d29922', response: '#bc8cff', config: '#a78bfa', monitor: '#d29922', audit: '#8b949e' }

export default function Labs() {
  const [courses, setCourses] = useState<any[]>([])
  const [labs, setLabs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [labsLoading, setLabsLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedCourse, setSelectedCourse] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'non-ai' | 'ai'>('all')
  const [selected, setSelected] = useState<any>(null)
  const [showAnswers, setShowAnswers] = useState(false)

  // 교과목 목록 로드
  useEffect(() => {
    api('/api/labs/courses')
      .then(d => setCourses(d.courses || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  // 교과목 선택 시 해당 과목 labs 로드
  const selectCourse = async (course: string) => {
    setSelectedCourse(course)
    setSelected(null)
    setLabsLoading(true)
    try {
      const d = await api(`/api/labs/catalog?course=${course}`)
      setLabs(d.labs || [])
    } catch (e: any) { setError(e.message) }
    setLabsLoading(false)
  }

  const openDetail = async (labId: string, admin = false) => {
    try {
      const d = await api(`/api/labs/catalog/${labId}${admin ? '?admin=true' : ''}`)
      setSelected(d)
    } catch (e: any) { alert('Failed: ' + e.message) }
  }

  const filtered = filter === 'all' ? labs : labs.filter(l => l.version === filter)

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading courses... (v2)</div>
  if (error) return <div style={{ color: '#f85149', padding: 40, textAlign: 'center' }}>Error loading courses: {error}</div>

  // 교과목 선택 전: 교과목 카드 그리드
  if (!selectedCourse) {
    return (
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#e6edf3' }}>Courses ({courses.length})</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {courses.map(c => (
            <div key={c.course} onClick={() => selectCourse(c.course)} style={{
              background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 20, cursor: 'pointer',
              transition: 'border-color 0.2s',
            }} onMouseOver={e => (e.currentTarget.style.borderColor = '#f97316')} onMouseOut={e => (e.currentTarget.style.borderColor = '#30363d')}>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3', marginBottom: 8 }}>{c.course}</div>
              <div style={{ fontSize: 13, color: '#8b949e', marginBottom: 12 }}>{c.title}</div>
              <div style={{ display: 'flex', gap: 8, fontSize: 12 }}>
                {c.versions?.map((v: string) => (
                  <span key={v} style={{
                    padding: '2px 8px', borderRadius: 10, fontWeight: 600,
                    background: v === 'ai' ? 'rgba(249,115,22,0.15)' : 'rgba(88,166,255,0.15)',
                    color: v === 'ai' ? '#f97316' : '#58a6ff',
                  }}>{v === 'ai' ? 'AI' : 'Non-AI'}</span>
                ))}
                <span style={{ color: '#8b949e', marginLeft: 'auto' }}>{c.total_labs} labs / {c.weeks} weeks</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // 교과목 선택 후: 주차별 실습 목록
  return (
    <div style={{ display: 'flex', gap: 24 }}>
      {/* Left: Labs list */}
      <div style={{ flex: selected ? '0 0 380px' : 1, transition: 'flex 0.2s' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <button onClick={() => { setSelectedCourse(null); setLabs([]); setSelected(null) }} style={{
              background: '#21262d', color: '#8b949e', border: '1px solid #30363d', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 12,
            }}>Back</button>
            <h2 style={{ fontSize: 20, fontWeight: 700, color: '#e6edf3' }}>{selectedCourse}</h2>
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            {(['all', 'non-ai', 'ai'] as const).map(v => (
              <button key={v} onClick={() => setFilter(v)} style={{
                padding: '5px 12px', borderRadius: 6, fontSize: 11, cursor: 'pointer', border: '1px solid #30363d',
                background: filter === v ? (v === 'ai' ? '#f97316' : v === 'non-ai' ? '#58a6ff' : '#30363d') : 'transparent',
                color: filter === v ? '#fff' : '#8b949e',
              }}>{v === 'all' ? 'All' : v === 'non-ai' ? 'Non-AI' : 'AI'}</button>
            ))}
          </div>
        </div>

        {labsLoading ? (
          <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading labs...</div>
        ) : filtered.length === 0 ? (
          <div style={{ color: '#8b949e', background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 40, textAlign: 'center' }}>No labs found</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {filtered.map(lab => (
              <div key={lab.lab_id} onClick={() => openDetail(lab.lab_id)} style={{
                background: selected?.lab_id === lab.lab_id ? '#1c2333' : '#161b22',
                border: selected?.lab_id === lab.lab_id ? '1px solid #f97316' : '1px solid #30363d',
                borderRadius: 8, padding: 14, cursor: 'pointer',
                borderLeft: `3px solid ${lab.version === 'ai' ? '#f97316' : '#58a6ff'}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 11, color: '#8b949e' }}>Week {lab.week}</span>
                  <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 10, fontWeight: 600, background: lab.version === 'ai' ? 'rgba(249,115,22,0.15)' : 'rgba(88,166,255,0.15)', color: lab.version === 'ai' ? '#f97316' : '#58a6ff' }}>{lab.version === 'ai' ? 'AI' : 'Non-AI'}</span>
                </div>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#e6edf3', marginBottom: 4 }}>{lab.title}</div>
                <div style={{ display: 'flex', gap: 8, fontSize: 11 }}>
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 12, color: '#8b949e', marginBottom: 4 }}>{selected.course} / Week {selected.week}</div>
                <h2 style={{ fontSize: 20, fontWeight: 700, color: '#e6edf3' }}>{selected.title}</h2>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {selected.has_answers && (
                  <button onClick={() => { setShowAnswers(!showAnswers); openDetail(selected.lab_id, !showAnswers) }} style={{
                    background: showAnswers ? '#f85149' : '#21262d', color: showAnswers ? '#fff' : '#8b949e',
                    border: '1px solid #30363d', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 11,
                  }}>{showAnswers ? 'Hide Answers' : 'Answers (Admin)'}</button>
                )}
                <button onClick={() => { setSelected(null); setShowAnswers(false) }} style={{
                  background: '#21262d', color: '#8b949e', border: '1px solid #30363d', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 11,
                }}>Close</button>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10, marginBottom: 12, flexWrap: 'wrap', fontSize: 12 }}>
              <span style={{ padding: '3px 10px', borderRadius: 10, background: '#21262d', color: diffColor[selected.difficulty] || '#8b949e' }}>{selected.difficulty}</span>
              <span style={{ color: '#8b949e' }}>{selected.duration_minutes}min</span>
              <span style={{ color: '#8b949e' }}>Pass: {Math.round(selected.pass_threshold * 100)}%</span>
              <span style={{ color: '#f97316', fontWeight: 600 }}>{selected.total_points}pts</span>
            </div>

            {selected.description && (
              <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 14, marginBottom: 12, fontSize: 13, color: '#8b949e', lineHeight: 1.6 }}>{selected.description}</div>
            )}

            {selected.objectives?.length > 0 && (
              <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 14, marginBottom: 12 }}>
                <h4 style={{ fontSize: 13, color: '#e6edf3', marginBottom: 6 }}>Objectives</h4>
                {selected.objectives.map((o: string, i: number) => (
                  <div key={i} style={{ fontSize: 12, color: '#8b949e', padding: '2px 0' }}>- {o}</div>
                ))}
              </div>
            )}

            <h4 style={{ fontSize: 14, color: '#e6edf3', marginBottom: 10 }}>Steps ({selected.steps?.length})</h4>
            {selected.steps?.map((s: any, i: number) => (
              <div key={i} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 14, marginBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span style={{ background: '#21262d', borderRadius: '50%', width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, color: '#f97316', fontWeight: 700 }}>{s.order}</span>
                    {s.category && <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 10, background: `${catColor[s.category] || '#484f58'}22`, color: catColor[s.category] || '#8b949e' }}>{s.category}</span>}
                  </div>
                  <span style={{ fontSize: 11, color: '#f97316', fontWeight: 600 }}>{s.points}pts</span>
                </div>
                <div style={{ fontSize: 13, color: '#e6edf3', marginBottom: 6, lineHeight: 1.5 }}>{s.instruction}</div>
                {s.hint && <div style={{ fontSize: 12, color: '#58a6ff', background: '#0d1f3c', borderRadius: 6, padding: '6px 10px', marginBottom: 6 }}>Hint: {s.hint}</div>}
                {s.script && <div style={{ fontSize: 12, fontFamily: 'monospace', color: '#3fb950', background: '#0d1f0d', borderRadius: 6, padding: '6px 10px', marginBottom: 6, whiteSpace: 'pre-wrap' as const }}>$ {s.script}</div>}
                {s.verify && <div style={{ fontSize: 11, color: '#8b949e', display: 'flex', gap: 6 }}>Verify: <code style={{ color: '#d29922' }}>{s.verify.type}</code> <code style={{ color: '#bc8cff' }}>"{s.verify.expect}"</code></div>}
                {s.answer && (
                  <div style={{ marginTop: 6, background: '#1a0a0a', border: '1px solid #f8514966', borderRadius: 6, padding: '8px 10px' }}>
                    <div style={{ fontSize: 10, color: '#f85149', fontWeight: 600, marginBottom: 3 }}>Answer (Admin)</div>
                    <div style={{ fontSize: 12, color: '#e6edf3', fontFamily: 'monospace', whiteSpace: 'pre-wrap' as const }}>{s.answer}</div>
                    {s.answer_detail && <div style={{ fontSize: 11, color: '#8b949e', marginTop: 4 }}>{s.answer_detail}</div>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

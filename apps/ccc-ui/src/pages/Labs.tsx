import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

const diffColor: Record<string, string> = { easy: '#3fb950', medium: '#d29922', hard: '#f85149' }

export default function Labs() {
  const [groups, setGroups] = useState<any[]>([])
  const [labs, setLabs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedCourse, setSelectedCourse] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'non-ai' | 'ai'>('all')
  // 문제 풀이 상태
  const [activeLab, setActiveLab] = useState<any>(null)
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [result, setResult] = useState<any>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    api('/api/education/courses')
      .then(d => setGroups(d.groups || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const selectCourse = async (courseId: string) => {
    setSelectedCourse(courseId)
    setActiveLab(null)
    setResult(null)
    try {
      const d = await api(`/api/labs/catalog?course=${courseId}`)
      setLabs(d.labs || [])
    } catch (e: any) { setError(e.message) }
  }

  const startLab = async (labId: string) => {
    setResult(null)
    setAnswers({})
    try {
      const d = await api(`/api/labs/catalog/${labId}`)
      setActiveLab(d)
    } catch (e: any) { alert('Failed: ' + e.message) }
  }

  const submitAnswers = async () => {
    if (!activeLab) return
    setSubmitting(true)
    // 학생 답변을 evidence로 변환
    const submissions = activeLab.steps.map((s: any) => {
      const ans = answers[s.order] || ''
      return { stdout: ans, user_answer: ans }
    })
    try {
      const d = await api(`/api/labs/evaluate?lab_id=${activeLab.lab_id}&student_id=current`, {
        method: 'POST',
        body: JSON.stringify(submissions),
      })
      setResult(d)
    } catch (e: any) { alert('Submit failed: ' + e.message) }
    setSubmitting(false)
  }

  const filtered = filter === 'all' ? labs : labs.filter(l => l.version === filter)

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
  if (error) return <div style={{ color: '#f85149', padding: 40, textAlign: 'center' }}>Error: {error}</div>

  // ── 교과목 선택 전: 그룹별 카드 ──
  if (!selectedCourse) {
    return (
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, color: '#e6edf3' }}>Labs</h2>
        <p style={{ fontSize: 13, color: '#8b949e', marginBottom: 24 }}>실습 문제를 풀고 제출하면 자동 채점됩니다.</p>
        {groups.map(g => (
          <div key={g.group} style={{ marginBottom: 32 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
              <div style={{ width: 4, height: 24, borderRadius: 2, background: g.color }} />
              <h3 style={{ fontSize: 18, fontWeight: 700, color: g.color }}>{g.group}</h3>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 14 }}>
              {g.courses.map((c: any) => (
                <div key={c.course_id} onClick={() => selectCourse(c.course_id)} style={{
                  background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 20, cursor: 'pointer',
                  borderLeft: `4px solid ${g.color}`, transition: 'transform 0.1s',
                }} onMouseOver={e => { e.currentTarget.style.transform = 'translateY(-2px)' }}
                   onMouseOut={e => { e.currentTarget.style.transform = 'none' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                    <span style={{ fontSize: 24 }}>{c.icon}</span>
                    <div style={{ fontSize: 16, fontWeight: 700, color: '#e6edf3' }}>{c.title}</div>
                  </div>
                  <div style={{ fontSize: 13, color: '#8b949e', marginBottom: 12, lineHeight: 1.5 }}>{c.description}</div>
                  <div style={{ display: 'flex', gap: 6, fontSize: 11 }}>
                    {c.labs_nonai > 0 && <span style={{ padding: '2px 8px', borderRadius: 10, background: 'rgba(88,166,255,0.12)', color: '#58a6ff' }}>Non-AI {c.labs_nonai}</span>}
                    {c.labs_ai > 0 && <span style={{ padding: '2px 8px', borderRadius: 10, background: 'rgba(249,115,22,0.12)', color: '#f97316' }}>AI {c.labs_ai}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  // ── 문제 풀이 중 ──
  if (activeLab) {
    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <button onClick={() => { setActiveLab(null); setResult(null) }} style={backBtn}>Back</button>
            <span style={{ fontSize: 18, fontWeight: 700, color: '#e6edf3', marginLeft: 12 }}>{activeLab.title}</span>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: '#8b949e' }}>{activeLab.steps?.length} 문제</span>
            <span style={{ fontSize: 14, color: '#f97316', fontWeight: 700 }}>{activeLab.total_points}pts</span>
          </div>
        </div>

        {activeLab.description && (
          <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 14, marginBottom: 16, fontSize: 13, color: '#8b949e' }}>{activeLab.description}</div>
        )}

        {/* 문제 목록 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {activeLab.steps?.map((s: any) => {
            const stepResult = result?.step_results?.find((r: any) => r.order === s.order)
            return (
              <div key={s.order} style={{
                background: '#161b22', borderRadius: 8, padding: 18,
                border: stepResult ? `1px solid ${stepResult.passed ? '#238636' : '#da3633'}` : '1px solid #30363d',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span style={{
                      background: stepResult ? (stepResult.passed ? '#238636' : '#da3633') : '#21262d',
                      borderRadius: '50%', width: 26, height: 26,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 12, color: '#fff', fontWeight: 700,
                    }}>{stepResult ? (stepResult.passed ? '✓' : '✗') : s.order}</span>
                    {s.category && <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10, background: '#21262d', color: '#8b949e' }}>{s.category}</span>}
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {stepResult && <span style={{ fontSize: 12, color: stepResult.passed ? '#3fb950' : '#f85149' }}>{stepResult.points_earned}/{s.points}pts</span>}
                    {!stepResult && <span style={{ fontSize: 12, color: '#f97316' }}>{s.points}pts</span>}
                  </div>
                </div>

                <div style={{ fontSize: 14, color: '#e6edf3', marginBottom: 10, lineHeight: 1.5 }}>
                  <strong>Q{s.order}.</strong> {s.instruction}
                </div>

                {s.hint && <div style={{ fontSize: 12, color: '#58a6ff', marginBottom: 8 }}>Hint: {s.hint}</div>}

                {/* 답변 입력 */}
                <textarea
                  value={answers[s.order] || ''}
                  onChange={e => setAnswers({ ...answers, [s.order]: e.target.value })}
                  placeholder="명령어 또는 결과를 입력하세요..."
                  disabled={!!result}
                  style={{
                    width: '100%', minHeight: 60, resize: 'vertical',
                    background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d',
                    borderRadius: 6, padding: '10px 12px', fontSize: 13,
                    fontFamily: 'Consolas, Monaco, monospace',
                  }}
                />

                {/* 채점 결과 */}
                {stepResult && (
                  <div style={{ marginTop: 8, fontSize: 12, color: stepResult.passed ? '#3fb950' : '#f85149' }}>
                    {stepResult.message}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* 제출 버튼 + 결과 */}
        <div style={{ marginTop: 20, display: 'flex', gap: 16, alignItems: 'center' }}>
          {!result ? (
            <button onClick={submitAnswers} disabled={submitting} style={{
              padding: '12px 32px', borderRadius: 8, border: 'none', fontSize: 15, fontWeight: 700, cursor: 'pointer',
              background: '#f97316', color: '#fff',
            }}>{submitting ? 'Grading...' : 'Submit'}</button>
          ) : (
            <div style={{
              flex: 1, padding: 16, borderRadius: 8,
              background: result.passed ? '#0d1f0d' : '#1f0d0d',
              border: `1px solid ${result.passed ? '#238636' : '#da3633'}`,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 700, color: result.passed ? '#3fb950' : '#f85149' }}>
                  {result.passed ? 'PASSED' : 'FAILED'}
                </div>
                <div style={{ fontSize: 13, color: '#8b949e' }}>
                  {result.earned_points}/{result.total_points}pts ({Math.round(result.earned_points / result.total_points * 100)}%)
                </div>
              </div>
              <button onClick={() => { setResult(null); setAnswers({}) }} style={{
                padding: '8px 20px', borderRadius: 6, border: '1px solid #30363d',
                background: '#21262d', color: '#e6edf3', cursor: 'pointer', fontSize: 13,
              }}>Retry</button>
            </div>
          )}
        </div>
      </div>
    )
  }

  // ── 과목 선택 후: 주차별 실습 목록 ──
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <button onClick={() => { setSelectedCourse(null); setLabs([]) }} style={backBtn}>Back</button>
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

      {filtered.length === 0 ? (
        <div style={{ color: '#8b949e', background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 40, textAlign: 'center' }}>No labs found</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 12 }}>
          {filtered.map(lab => (
            <div key={lab.lab_id} onClick={() => startLab(lab.lab_id)} style={{
              background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 18, cursor: 'pointer',
              borderLeft: `3px solid ${lab.version === 'ai' ? '#f97316' : '#58a6ff'}`,
              transition: 'transform 0.1s',
            }} onMouseOver={e => { e.currentTarget.style.transform = 'translateY(-1px)' }}
               onMouseOut={e => { e.currentTarget.style.transform = 'none' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: 11, color: '#8b949e' }}>Week {lab.week}</span>
                <span style={{
                  fontSize: 10, padding: '1px 6px', borderRadius: 10, fontWeight: 600,
                  background: lab.version === 'ai' ? 'rgba(249,115,22,0.15)' : 'rgba(88,166,255,0.15)',
                  color: lab.version === 'ai' ? '#f97316' : '#58a6ff',
                }}>{lab.version === 'ai' ? 'AI' : 'Non-AI'}</span>
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#e6edf3', marginBottom: 8 }}>{lab.title}</div>
              <div style={{ display: 'flex', gap: 8, fontSize: 11 }}>
                <span style={{ color: diffColor[lab.difficulty] || '#8b949e' }}>{lab.difficulty}</span>
                <span style={{ color: '#484f58' }}>{lab.steps} questions</span>
                <span style={{ color: '#f97316', fontWeight: 600, marginLeft: 'auto' }}>{lab.total_points}pts</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const backBtn: React.CSSProperties = {
  background: '#21262d', color: '#8b949e', border: '1px solid #30363d',
  borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 12,
}

import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'
import { getUser, isAdmin } from '../auth.ts'

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
      // admin/instructor는 정답 포함해서 받기
      const qs = isAdmin() ? '?admin=1' : ''
      const d = await api(`/api/labs/catalog/${labId}${qs}`)
      setActiveLab(d)
    } catch (e: any) { alert('Failed: ' + e.message) }
  }

  // 스텝 그룹 (5개씩)
  const getStepGroups = () => {
    if (!activeLab?.steps) return []
    const steps = activeLab.steps
    const groups = []
    for (let i = 0; i < steps.length; i += 5) {
      groups.push({ start: i, end: Math.min(i + 5, steps.length), steps: steps.slice(i, i + 5) })
    }
    return groups
  }

  const submitGroup = async (groupIdx: number) => {
    if (!activeLab) return
    setSubmitting(true)
    const groups = getStepGroups()
    const group = groups[groupIdx]
    const submissions = activeLab.steps.map((s: any) => {
      const ans = answers[s.order] || ''
      return { stdout: ans, user_answer: ans }
    })
    try {
      const user = getUser()
      const d = await api(`/api/labs/evaluate?lab_id=${activeLab.lab_id}&student_id=${user?.id || 'anonymous'}`, {
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
        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, color: '#e6edf3' }}>Cyber Range</h2>
        <p style={{ fontSize: 15, color: '#8b949e', marginBottom: 24 }}>사이버 레인지: 실습 문제를 풀고 제출하면 자동 채점됩니다. 스텝 그룹별로 제출하세요.</p>
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
                  <div style={{ fontSize: 15, color: '#8b949e', marginBottom: 12, lineHeight: 1.5 }}>{c.description}</div>
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
            <span style={{ fontSize: 14, color: '#8b949e' }}>{activeLab.steps?.length} 문제</span>
            <span style={{ fontSize: 14, color: '#f97316', fontWeight: 700 }}>{activeLab.total_points}pts</span>
          </div>
        </div>

        {activeLab.description && (
          <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 14, marginBottom: 16, fontSize: 15, color: '#8b949e' }}>{activeLab.description}</div>
        )}

        {/* AI 버전: bastion 사용 안내 (1회) */}
        {activeLab.version === 'ai' && (
          <div style={{ background: '#0d1f0d', border: '1px solid #238636', borderRadius: 8, padding: '10px 16px', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 16 }}>🤖</span>
            <div style={{ fontSize: 14, color: '#3fb950' }}>
              <strong>AI 실습:</strong> 각 문제의 <strong>bastion에 입력하세요</strong> 박스의 문장을 bastion 채팅에 입력하거나,{' '}
              <code style={{ background: '#0d1117', padding: '1px 6px', borderRadius: 4 }}>POST http://localhost:8003/ask</code>로 요청하세요.
            </div>
          </div>
        )}

        {/* 문제 목록 (그룹별) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {getStepGroups().map((group, gi) => (
          <div key={gi}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <h4 style={{ fontSize: 16, color: '#e6edf3' }}>Part {gi + 1} (Q{group.start + 1}~Q{group.end})</h4>
              {!result && (
                <button onClick={() => submitGroup(gi)} disabled={submitting} style={{
                  padding: '6px 16px', borderRadius: 6, border: 'none',
                  background: '#f97316', color: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 600,
                }}>{submitting ? '...' : `Part ${gi + 1} Submit`}</button>
              )}
            </div>
          {group.steps.map((s: any) => {
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
                      fontSize: 14, color: '#fff', fontWeight: 700,
                    }}>{stepResult ? (stepResult.passed ? '✓' : '✗') : s.order}</span>
                    {s.category && <span style={{ fontSize: 14, padding: '2px 8px', borderRadius: 10, background: '#21262d', color: '#8b949e' }}>{s.category}</span>}
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {stepResult && <span style={{ fontSize: 14, color: stepResult.passed ? '#3fb950' : '#f85149' }}>{stepResult.points_earned}/{s.points}pts</span>}
                    {!stepResult && <span style={{ fontSize: 14, color: '#f97316' }}>{s.points}pts</span>}
                  </div>
                </div>

                <div style={{ fontSize: 14, color: '#e6edf3', marginBottom: 10, lineHeight: 1.5, whiteSpace: 'pre-wrap' as const }}>
                  <strong>Q{s.order}.</strong> {s.instruction}
                </div>

                {/* AI 버전: bastion 자연어 요청 */}
                {s.bastion_prompt && (
                  <div style={{ background: '#0d1f0d', border: '1px solid #238636', borderRadius: 6, padding: '10px 14px', marginBottom: 10 }}>
                    <div style={{ fontSize: 12, color: '#3fb950', fontWeight: 700, marginBottom: 4 }}>🤖 bastion에 입력하세요</div>
                    <div style={{ fontSize: 14, color: '#e6edf3', whiteSpace: 'pre-wrap' as const }}>{s.bastion_prompt}</div>
                  </div>
                )}

                {s.hint && (
                  <div style={{ fontSize: 14, color: '#58a6ff', background: '#0d1f3c', borderRadius: 6, padding: '8px 12px', marginBottom: 8, whiteSpace: 'pre-wrap' as const }}>
                    Hint: {s.hint}
                  </div>
                )}

                {/* 답변 입력 */}
                <textarea
                  value={answers[s.order] || ''}
                  onChange={e => setAnswers({ ...answers, [s.order]: e.target.value })}
                  placeholder={s.bastion_prompt ? 'bastion의 답변 또는 확인된 결과를 입력하세요...' : '명령어 또는 결과를 입력하세요...'}
                  disabled={!!result}
                  style={{
                    width: '100%', minHeight: 60, resize: 'vertical',
                    background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d',
                    borderRadius: 6, padding: '10px 12px', fontSize: 15,
                    fontFamily: 'Consolas, Monaco, monospace',
                  }}
                />

                {/* Admin 정답 */}
                {isAdmin() && (s.answer || s.answer_detail) && (
                  <div style={{ marginTop: 8, background: '#1a0a0a', border: '1px solid #f8514966', borderRadius: 6, padding: '10px 12px' }}>
                    <div style={{ fontSize: 13, color: '#f85149', fontWeight: 700, marginBottom: 4 }}>정답 (Admin)</div>
                    {s.answer && <div style={{ fontSize: 14, color: '#e6edf3', fontFamily: 'Consolas,Monaco,monospace', whiteSpace: 'pre-wrap' as const }}>{s.answer}</div>}
                    {s.answer_detail && <div style={{ fontSize: 13, color: '#8b949e', marginTop: 6, whiteSpace: 'pre-wrap' as const }}>{s.answer_detail}</div>}
                  </div>
                )}

                {/* 채점 결과 */}
                {stepResult && (
                  <div style={{ marginTop: 8, fontSize: 14, color: stepResult.passed ? '#3fb950' : '#f85149' }}>
                    {stepResult.message}
                  </div>
                )}
              </div>
            )
          })}
          </div>
          ))}
        </div>

        {/* 결과 */}
        {result && (
          <div style={{ marginTop: 20, padding: 16, borderRadius: 8,
            background: result.passed ? '#0d1f0d' : '#1f0d0d',
            border: `1px solid ${result.passed ? '#238636' : '#da3633'}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 700, color: result.passed ? '#3fb950' : '#f85149' }}>
                {result.passed ? 'PASSED' : 'FAILED'}
              </div>
              <div style={{ fontSize: 15, color: '#8b949e' }}>
                {result.earned_points}/{result.total_points}pts ({Math.round(result.earned_points / result.total_points * 100)}%)
              </div>
            </div>
            <button onClick={() => { setResult(null); setAnswers({}) }} style={{
              padding: '8px 20px', borderRadius: 6, border: '1px solid #30363d',
              background: '#21262d', color: '#e6edf3', cursor: 'pointer', fontSize: 15,
            }}>Retry</button>
          </div>
        )}
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
              padding: '5px 12px', borderRadius: 6, fontSize: 15, cursor: 'pointer', border: '1px solid #30363d',
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
                <span style={{ fontSize: 15, color: '#8b949e' }}>Week {lab.week}</span>
                <span style={{
                  fontSize: 14, padding: '1px 6px', borderRadius: 10, fontWeight: 600,
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
  borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 14,
}

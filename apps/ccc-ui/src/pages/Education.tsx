import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

export default function Education() {
  const [courses, setCourses] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedCourse, setSelectedCourse] = useState<any>(null)
  const [weeks, setWeeks] = useState<any[]>([])
  const [weeksLoading, setWeeksLoading] = useState(false)
  const [lecture, setLecture] = useState<string | null>(null)
  const [lectureTitle, setLectureTitle] = useState('')
  const [labDetail, setLabDetail] = useState<any>(null)
  const [showAnswers, setShowAnswers] = useState(false)

  useEffect(() => {
    api('/api/education/courses')
      .then(d => setCourses(d.courses || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const selectCourse = async (course: any) => {
    setSelectedCourse(course)
    setLecture(null)
    setLabDetail(null)
    setWeeksLoading(true)
    try {
      const d = await api(`/api/education/courses/${course.course_id}/weeks`)
      setWeeks(d.weeks || [])
    } catch (e: any) { setError(e.message) }
    setWeeksLoading(false)
  }

  const openLecture = async (courseId: string, week: number, title: string) => {
    setLabDetail(null)
    setLectureTitle(`Week ${week}: ${title}`)
    try {
      const d = await api(`/api/education/lecture/${courseId}/${week}`)
      setLecture(d.content)
    } catch { setLecture('교안을 로드할 수 없습니다.') }
  }

  const openLab = async (labId: string, admin = false) => {
    setLecture(null)
    try {
      const d = await api(`/api/labs/catalog/${labId}${admin ? '?admin=true' : ''}`)
      setLabDetail(d)
    } catch { setLabDetail(null) }
  }

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading courses...</div>
  if (error) return <div style={{ color: '#f85149', padding: 40, textAlign: 'center' }}>Error: {error}</div>

  // ── 교과목 선택 전: 카드 그리드 ──
  if (!selectedCourse) {
    return (
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, color: '#e6edf3' }}>Education</h2>
        <p style={{ fontSize: 13, color: '#8b949e', marginBottom: 24 }}>교과목을 선택하면 주차별 교안과 실습을 확인할 수 있습니다.</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {courses.map(c => (
            <div key={c.course_id} onClick={() => selectCourse(c)} style={{
              background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 24, cursor: 'pointer',
              transition: 'border-color 0.2s, transform 0.1s',
            }} onMouseOver={e => { e.currentTarget.style.borderColor = '#f97316'; e.currentTarget.style.transform = 'translateY(-2px)' }}
               onMouseOut={e => { e.currentTarget.style.borderColor = '#30363d'; e.currentTarget.style.transform = 'none' }}>
              <div style={{ fontSize: 28, marginBottom: 12 }}>{c.icon}</div>
              <div style={{ fontSize: 17, fontWeight: 700, color: '#e6edf3', marginBottom: 6 }}>{c.title}</div>
              <div style={{ fontSize: 13, color: '#8b949e', marginBottom: 14, lineHeight: 1.5 }}>{c.description}</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', fontSize: 11 }}>
                <span style={{ padding: '3px 10px', borderRadius: 10, background: '#21262d', color: '#8b949e' }}>{c.weeks}주</span>
                {c.labs_nonai > 0 && <span style={{ padding: '3px 10px', borderRadius: 10, background: 'rgba(88,166,255,0.15)', color: '#58a6ff' }}>Non-AI {c.labs_nonai}</span>}
                {c.labs_ai > 0 && <span style={{ padding: '3px 10px', borderRadius: 10, background: 'rgba(249,115,22,0.15)', color: '#f97316' }}>AI {c.labs_ai}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // ── 교과목 선택 후: 주차별 교안 + 실습 ──
  return (
    <div style={{ display: 'flex', gap: 24 }}>
      {/* Left: 주차 목록 */}
      <div style={{ width: (lecture || labDetail) ? 340 : '100%', flexShrink: 0, transition: 'width 0.2s' }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 20 }}>
          <button onClick={() => { setSelectedCourse(null); setLecture(null); setLabDetail(null) }} style={{
            background: '#21262d', color: '#8b949e', border: '1px solid #30363d', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 12,
          }}>Back</button>
          <div>
            <span style={{ fontSize: 20, marginRight: 8 }}>{selectedCourse.icon}</span>
            <span style={{ fontSize: 20, fontWeight: 700, color: '#e6edf3' }}>{selectedCourse.title}</span>
          </div>
        </div>

        {weeksLoading ? (
          <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading weeks...</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {weeks.map(w => (
              <div key={w.week} style={{
                background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 14,
              }}>
                <div style={{ fontSize: 11, color: '#8b949e', marginBottom: 4 }}>Week {w.week}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#e6edf3', marginBottom: 10 }}>{w.title || `Week ${w.week}`}</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {w.has_lecture && (
                    <button onClick={() => openLecture(selectedCourse.course_id, w.week, w.title)} style={{
                      padding: '4px 12px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                      background: lecture && lectureTitle.includes(`Week ${w.week}`) ? '#f97316' : '#21262d',
                      color: lecture && lectureTitle.includes(`Week ${w.week}`) ? '#fff' : '#e6edf3',
                      border: '1px solid #30363d',
                    }}>📖 교안</button>
                  )}
                  <button onClick={() => openLab(w.lab_nonai_id)} style={{
                    padding: '4px 12px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                    background: labDetail?.lab_id === w.lab_nonai_id ? '#58a6ff' : '#21262d',
                    color: labDetail?.lab_id === w.lab_nonai_id ? '#fff' : '#58a6ff',
                    border: '1px solid #30363d',
                  }}>📝 Non-AI</button>
                  <button onClick={() => openLab(w.lab_ai_id)} style={{
                    padding: '4px 12px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                    background: labDetail?.lab_id === w.lab_ai_id ? '#f97316' : '#21262d',
                    color: labDetail?.lab_id === w.lab_ai_id ? '#fff' : '#f97316',
                    border: '1px solid #30363d',
                  }}>🤖 AI</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right: 교안 또는 실습 상세 */}
      {(lecture || labDetail) && (
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* 교안 보기 */}
          {lecture && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ fontSize: 18, fontWeight: 700, color: '#e6edf3' }}>{lectureTitle}</h3>
                <button onClick={() => setLecture(null)} style={{
                  background: '#21262d', color: '#8b949e', border: '1px solid #30363d', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 11,
                }}>Close</button>
              </div>
              <div style={{
                background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 24,
                fontSize: 14, color: '#e6edf3', lineHeight: 1.8, maxHeight: 'calc(100vh - 150px)', overflowY: 'auto',
                whiteSpace: 'pre-wrap',
              }} dangerouslySetInnerHTML={{ __html: markdownToHtml(lecture) }} />
            </div>
          )}

          {/* 실습 상세 */}
          {labDetail && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 12, color: '#8b949e', marginBottom: 4 }}>{labDetail.course} / Week {labDetail.week}</div>
                  <h3 style={{ fontSize: 18, fontWeight: 700, color: '#e6edf3' }}>{labDetail.title}</h3>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  {labDetail.has_answers && (
                    <button onClick={() => { setShowAnswers(!showAnswers); openLab(labDetail.lab_id, !showAnswers) }} style={{
                      background: showAnswers ? '#f85149' : '#21262d', color: showAnswers ? '#fff' : '#8b949e',
                      border: '1px solid #30363d', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 11,
                    }}>{showAnswers ? 'Hide Answers' : 'Answers (Admin)'}</button>
                  )}
                  <button onClick={() => { setLabDetail(null); setShowAnswers(false) }} style={{
                    background: '#21262d', color: '#8b949e', border: '1px solid #30363d', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 11,
                  }}>Close</button>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, marginBottom: 12, flexWrap: 'wrap', fontSize: 12 }}>
                <span style={{ padding: '3px 10px', borderRadius: 10, background: labDetail.version === 'ai' ? 'rgba(249,115,22,0.15)' : 'rgba(88,166,255,0.15)', color: labDetail.version === 'ai' ? '#f97316' : '#58a6ff', fontWeight: 600 }}>{labDetail.version === 'ai' ? 'AI' : 'Non-AI'}</span>
                <span style={{ color: '#8b949e' }}>{labDetail.duration_minutes}min</span>
                <span style={{ color: '#f97316', fontWeight: 600 }}>{labDetail.total_points}pts</span>
                <span style={{ color: '#8b949e' }}>Pass: {Math.round(labDetail.pass_threshold * 100)}%</span>
              </div>

              {labDetail.description && (
                <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 14, marginBottom: 12, fontSize: 13, color: '#8b949e', lineHeight: 1.6 }}>{labDetail.description}</div>
              )}

              <div style={{ maxHeight: 'calc(100vh - 280px)', overflowY: 'auto' }}>
                {labDetail.steps?.map((s: any, i: number) => (
                  <div key={i} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 14, marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                        <span style={{ background: '#21262d', borderRadius: '50%', width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, color: '#f97316', fontWeight: 700 }}>{s.order}</span>
                        {s.category && <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 10, background: '#21262d', color: '#8b949e' }}>{s.category}</span>}
                      </div>
                      <span style={{ fontSize: 11, color: '#f97316', fontWeight: 600 }}>{s.points}pts</span>
                    </div>
                    <div style={{ fontSize: 13, color: '#e6edf3', marginBottom: 6, lineHeight: 1.5 }}>{s.instruction}</div>
                    {s.hint && <div style={{ fontSize: 12, color: '#58a6ff', background: '#0d1f3c', borderRadius: 6, padding: '6px 10px', marginBottom: 6 }}>Hint: {s.hint}</div>}
                    {s.script && <div style={{ fontSize: 12, fontFamily: 'monospace', color: '#3fb950', background: '#0d1f0d', borderRadius: 6, padding: '6px 10px', marginBottom: 6, whiteSpace: 'pre-wrap' as const }}>$ {s.script}</div>}
                    {s.verify && <div style={{ fontSize: 11, color: '#8b949e' }}>Verify: <code style={{ color: '#d29922' }}>{s.verify.type}</code> <code style={{ color: '#bc8cff' }}>"{s.verify.expect}"</code></div>}
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
      )}
    </div>
  )
}

// 간이 markdown → HTML (제목, 코드, 굵기, 리스트)
function markdownToHtml(md: string): string {
  return md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3 style="font-size:16px;color:#e6edf3;margin:20px 0 8px">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="font-size:18px;color:#e6edf3;margin:24px 0 10px;border-bottom:1px solid #30363d;padding-bottom:6px">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="font-size:22px;color:#f97316;margin:0 0 16px">$1</h1>')
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre style="background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:12px;font-size:12px;overflow-x:auto;color:#3fb950">$2</pre>')
    .replace(/`([^`]+)`/g, '<code style="background:#21262d;padding:2px 6px;border-radius:3px;font-size:12px;color:#f0883e">$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#e6edf3">$1</strong>')
    .replace(/^\- (.+)$/gm, '<div style="padding:2px 0 2px 16px">• $1</div>')
    .replace(/^\| (.+)$/gm, (_, row) => {
      const cells = row.split('|').map((c: string) => c.trim()).filter(Boolean)
      return '<div style="display:flex;border-bottom:1px solid #21262d">' + cells.map((c: string) => `<span style="flex:1;padding:4px 8px;font-size:12px">${c}</span>`).join('') + '</div>'
    })
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>')
}

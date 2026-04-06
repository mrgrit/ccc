import React, { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api.ts'
import { isAdmin } from '../auth.ts'

export default function Education() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [groups, setGroups] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [weeks, setWeeks] = useState<any[]>([])
  const [weeksLoading, setWeeksLoading] = useState(false)
  const [lecture, setLecture] = useState<string | null>(null)
  const [labDetail, setLabDetail] = useState<any>(null)
  const [showAnswers, setShowAnswers] = useState(false)

  // URL 파라미터에서 네비게이션 상태 파생
  const courseId = searchParams.get('course')
  const viewParam = searchParams.get('view') as 'lecture' | 'lab' | null
  const weekParam = searchParams.get('week')
  const labIdParam = searchParams.get('lab')
  const viewMode = viewParam || 'none'

  const selectedCourse = courseId
    ? groups.flatMap(g => g.courses).find((c: any) => c.course_id === courseId) || null
    : null

  useEffect(() => {
    api('/api/training/courses')
      .then(d => setGroups(d.groups || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  // 코스 선택 시 주차 데이터 로드
  useEffect(() => {
    if (!courseId) { setWeeks([]); return }
    setWeeksLoading(true)
    api(`/api/training/courses/${courseId}/weeks`)
      .then(d => setWeeks(d.weeks || []))
      .catch(e => setError(e.message))
      .finally(() => setWeeksLoading(false))
  }, [courseId])

  // 교안 로드
  useEffect(() => {
    if (viewParam === 'lecture' && courseId && weekParam) {
      api(`/api/training/lecture/${courseId}/${weekParam}`)
        .then(d => setLecture(d.content))
        .catch(() => setLecture('교안을 로드할 수 없습니다.'))
    } else {
      setLecture(null)
    }
  }, [viewParam, courseId, weekParam])

  // 실습 로드
  useEffect(() => {
    if (viewParam === 'lab' && labIdParam) {
      api(`/api/labs/catalog/${labIdParam}`)
        .then(d => setLabDetail(d))
        .catch(() => setLabDetail(null))
    } else {
      setLabDetail(null)
    }
  }, [viewParam, labIdParam])

  const selectCourse = (course: any) => {
    setSearchParams({ course: course.course_id })
  }

  const openLecture = (courseId: string, week: number) => {
    setSearchParams({ course: courseId, view: 'lecture', week: String(week) })
  }

  const openLab = (labId: string, admin = false) => {
    const params: Record<string, string> = { course: courseId!, view: 'lab', lab: labId }
    if (admin) params.admin = '1'
    setSearchParams(params)
  }

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center', fontSize: 15 }}>Loading courses...</div>
  if (error) return <div style={{ color: '#f85149', padding: 40, textAlign: 'center', fontSize: 15 }}>Error: {error}</div>

  // ── 교과목 선택 전: 그룹별 카드 ──
  if (!selectedCourse) {
    return (
      <div>
        <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 8, color: '#e6edf3' }}>Training</h2>
        <p style={{ fontSize: 15, color: '#8b949e', marginBottom: 28 }}>교과목을 선택하면 주차별 교안과 실습을 확인할 수 있습니다.</p>
        {groups.map(g => (
          <div key={g.group} style={{ marginBottom: 36 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <div style={{ width: 4, height: 28, borderRadius: 2, background: g.color }} />
              <h3 style={{ fontSize: 20, fontWeight: 700, color: g.color }}>{g.group}</h3>
              <span style={{ fontSize: 14, color: '#8b949e' }}>{g.courses.length}개 과목</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
              {g.courses.map((c: any) => (
                <div key={c.course_id} onClick={() => selectCourse(c)} style={{
                  background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 22, cursor: 'pointer',
                  borderLeft: `4px solid ${g.color}`, transition: 'transform 0.1s',
                }} onMouseOver={e => { e.currentTarget.style.transform = 'translateY(-2px)' }}
                   onMouseOut={e => { e.currentTarget.style.transform = 'none' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                    <span style={{ fontSize: 28 }}>{c.icon}</span>
                    <div style={{ fontSize: 17, fontWeight: 700, color: '#e6edf3' }}>{c.title}</div>
                    {c.min_rank && c.min_rank !== 'rookie' && (
                      <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 10, background: 'rgba(249,115,22,0.12)', color: '#f97316', fontWeight: 600, textTransform: 'uppercase' as const }}>{c.min_rank}+</span>
                    )}
                  </div>
                  <div style={{ fontSize: 14, color: '#8b949e', marginBottom: 14, lineHeight: 1.6 }}>{c.description}</div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', fontSize: 12 }}>
                    <span style={{ padding: '3px 10px', borderRadius: 10, background: '#21262d', color: '#8b949e' }}>{c.weeks}주</span>
                    {c.labs_nonai > 0 && <span style={{ padding: '3px 10px', borderRadius: 10, background: 'rgba(88,166,255,0.12)', color: '#58a6ff' }}>Non-AI {c.labs_nonai}</span>}
                    {c.labs_ai > 0 && <span style={{ padding: '3px 10px', borderRadius: 10, background: 'rgba(249,115,22,0.12)', color: '#f97316' }}>AI {c.labs_ai}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  // ── 교과목 선택 후 ──
  // 콘텐츠가 열렸으면 전체를 콘텐츠로 표시 (주차 목록은 상단 탭)
  if (viewMode !== 'none') {
    return (
      <div>
        {/* 상단 네비 */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 16 }}>
          <button onClick={() => setSearchParams({ course: courseId! })} style={backBtn}>주차 목록</button>
          <button onClick={() => setSearchParams({})} style={backBtn}>과목 목록</button>
          <span style={{ fontSize: 14, color: '#8b949e' }}>{selectedCourse?.icon} {selectedCourse?.title}</span>
          <span style={{ fontSize: 16, fontWeight: 700, color: '#e6edf3', marginLeft: 8 }}>
            {viewMode === 'lecture' && weekParam ? `Week ${weekParam}: ${weeks.find(w => w.week === Number(weekParam))?.title || ''}` : labDetail?.title}
          </span>
          {labDetail?.has_answers && viewMode === 'lab' && isAdmin() && (
            <button onClick={() => { setShowAnswers(!showAnswers); openLab(labDetail.lab_id, !showAnswers) }} style={{
              marginLeft: 'auto', background: showAnswers ? '#f85149' : '#21262d', color: showAnswers ? '#fff' : '#8b949e',
              border: '1px solid #30363d', borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 14,
            }}>{showAnswers ? 'Hide Answers' : 'Answers (Admin)'}</button>
          )}
        </div>

        {/* 교안 전체 화면 */}
        {viewMode === 'lecture' && lecture && (
          <div style={{
            background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: '32px 36px',
            fontSize: 16, color: '#c9d1d9', lineHeight: 1.7,
          }} dangerouslySetInnerHTML={{ __html: markdownToHtml(lecture) }} />
        )}

        {/* 실습 전체 화면 */}
        {viewMode === 'lab' && labDetail && (
          <div>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap', fontSize: 13 }}>
              <span style={{ padding: '4px 12px', borderRadius: 10, background: labDetail.version === 'ai' ? 'rgba(249,115,22,0.15)' : 'rgba(88,166,255,0.15)', color: labDetail.version === 'ai' ? '#f97316' : '#58a6ff', fontWeight: 600 }}>{labDetail.version === 'ai' ? 'AI' : 'Non-AI'}</span>
              <span style={{ color: '#8b949e' }}>{labDetail.duration_minutes}min</span>
              <span style={{ color: '#f97316', fontWeight: 600 }}>{labDetail.total_points}pts</span>
            </div>
            {labDetail.description && (
              <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16, marginBottom: 16, fontSize: 14, color: '#8b949e', lineHeight: 1.6 }}>{labDetail.description}</div>
            )}
            {labDetail.objectives?.length > 0 && (
              <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16, marginBottom: 16 }}>
                <h4 style={{ fontSize: 15, color: '#e6edf3', marginBottom: 8 }}>Objectives</h4>
                {labDetail.objectives.map((o: string, i: number) => (
                  <div key={i} style={{ fontSize: 14, color: '#8b949e', padding: '3px 0' }}>- {o}</div>
                ))}
              </div>
            )}
            {labDetail.steps?.map((s: any, i: number) => (
              <div key={i} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 18, marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span style={{ background: '#21262d', borderRadius: '50%', width: 26, height: 26, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15, color: '#f97316', fontWeight: 700 }}>{s.order}</span>
                    {s.category && <span style={{ fontSize: 15, padding: '2px 8px', borderRadius: 10, background: '#21262d', color: '#8b949e' }}>{s.category}</span>}
                  </div>
                  <span style={{ fontSize: 15, color: '#f97316', fontWeight: 600 }}>{s.points}pts</span>
                </div>
                <div style={{ fontSize: 15, color: '#e6edf3', marginBottom: 8, lineHeight: 1.6 }}>{s.instruction}</div>
                {s.hint && <div style={{ fontSize: 14, color: '#58a6ff', background: '#0d1f3c', borderRadius: 6, padding: '8px 12px', marginBottom: 8 }}>Hint: {s.hint}</div>}
                {s.script && <div style={{ fontSize: 14, fontFamily: 'Consolas,Monaco,monospace', color: '#3fb950', background: '#0d1f0d', borderRadius: 6, padding: '8px 12px', marginBottom: 8, whiteSpace: 'pre-wrap' as const }}>$ {s.script}</div>}
                {s.verify && <div style={{ fontSize: 15, color: '#8b949e' }}>Verify: <code style={{ color: '#d29922' }}>{s.verify.type}</code> <code style={{ color: '#bc8cff' }}>"{s.verify.expect}"</code></div>}
                {s.answer && (
                  <div style={{ marginTop: 8, background: '#1a0a0a', border: '1px solid #f8514966', borderRadius: 6, padding: '10px 12px' }}>
                    <div style={{ fontSize: 15, color: '#f85149', fontWeight: 600, marginBottom: 4 }}>Answer (Admin)</div>
                    <div style={{ fontSize: 14, color: '#e6edf3', fontFamily: 'Consolas,Monaco,monospace', whiteSpace: 'pre-wrap' as const }}>{s.answer}</div>
                    {s.answer_detail && <div style={{ fontSize: 15, color: '#8b949e', marginTop: 6 }}>{s.answer_detail}</div>}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // ── 주차 목록 ──
  return (
    <div>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 24 }}>
        <button onClick={() => setSearchParams({})} style={backBtn}>Back</button>
        <span style={{ fontSize: 24 }}>{selectedCourse.icon}</span>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: '#e6edf3' }}>{selectedCourse.title}</h2>
      </div>

      {weeksLoading ? (
        <div style={{ color: '#8b949e', padding: 40, textAlign: 'center', fontSize: 15 }}>Loading...</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {weeks.map(w => (
            <div key={w.week} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 18 }}>
              <div style={{ fontSize: 14, color: '#8b949e', marginBottom: 4 }}>Week {w.week}</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3', marginBottom: 12 }}>{w.title || `Week ${w.week}`}</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {w.has_lecture && (
                  <button onClick={() => openLecture(selectedCourse.course_id, w.week)} style={{ ...actionBtn, background: '#21262d', color: '#e6edf3' }}>📖 교안</button>
                )}
                <button onClick={() => openLab(w.lab_nonai_id)} style={{ ...actionBtn, color: '#58a6ff' }}>📝 Non-AI 실습</button>
                <button onClick={() => openLab(w.lab_ai_id)} style={{ ...actionBtn, color: '#f97316' }}>🤖 AI 실습</button>
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
  borderRadius: 6, padding: '7px 14px', cursor: 'pointer', fontSize: 15,
}
const actionBtn: React.CSSProperties = {
  padding: '6px 16px', borderRadius: 6, fontSize: 15, cursor: 'pointer',
  background: '#21262d', border: '1px solid #30363d',
}

// ── Markdown → HTML ──
function markdownToHtml(md: string): string {
  return md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    // 코드블록 — monospace, pre 유지 (도형/선 보존)
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre style="background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:16px 20px;font-size:15px;line-height:1.5;overflow-x:auto;color:#3fb950;margin:12px 0;font-family:\'D2Coding\',\'Nanum Gothic Coding\',Consolas,Monaco,\'Courier New\',monospace;white-space:pre;tab-size:4;letter-spacing:0">$2</pre>')
    // 제목
    .replace(/^#### (.+)$/gm, '<h4 style="font-size:17px;color:#c9d1d9;margin:18px 0 8px;font-weight:600">$1</h4>')
    .replace(/^### (.+)$/gm, '<h3 style="font-size:19px;color:#e6edf3;margin:22px 0 10px;font-weight:600">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="font-size:21px;color:#e6edf3;margin:28px 0 12px;border-bottom:1px solid #30363d;padding-bottom:8px;font-weight:700">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="font-size:24px;color:#f0883e;margin:0 0 16px;font-weight:700">$1</h1>')
    // 인라인 코드
    .replace(/`([^`]+)`/g, '<code style="background:#21262d;padding:2px 7px;border-radius:4px;font-size:15px;color:#d2a8ff;font-family:Consolas,Monaco,monospace">$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#e6edf3">$1</strong>')
    // 블록쿼트
    .replace(/^&gt; (.+)$/gm, '<div style="border-left:3px solid #30363d;padding:6px 14px;margin:6px 0;color:#8b949e;font-size:15px">$1</div>')
    // 리스트
    .replace(/^\- (.+)$/gm, '<div style="padding:2px 0 2px 20px;font-size:16px">• $1</div>')
    .replace(/^\d+\. (.+)$/gm, '<div style="padding:2px 0 2px 20px;font-size:16px">$1</div>')
    // 테이블 구분선 제거
    .replace(/^\|[\s\-:|]+\|$/gm, '')
    // 테이블 행
    .replace(/^\|(.+)\|$/gm, (_, row) => {
      const cells = row.split('|').map((c: string) => c.trim()).filter(Boolean)
      return '<div style="display:flex;border-bottom:1px solid #21262d">' + cells.map((c: string) => `<span style="flex:1;padding:6px 12px;font-size:15px">${c}</span>`).join('') + '</div>'
    })
    // 줄바꿈
    .replace(/\n\n/g, '<div style="height:10px"></div>')
    .replace(/\n/g, '<br/>')
}

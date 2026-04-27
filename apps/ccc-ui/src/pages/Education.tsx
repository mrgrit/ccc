import React, { useEffect, useState, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api.ts'
import { isAdmin } from '../auth.ts'
import mermaid from 'mermaid'

mermaid.initialize({ startOnLoad: false, theme: 'dark', themeVariables: {
  primaryColor: '#21262d', primaryTextColor: '#e6edf3', lineColor: '#30363d',
  secondaryColor: '#161b22', tertiaryColor: '#0d1117',
}})

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
  const lectureRef = useRef<HTMLDivElement>(null)

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

  // Mermaid 렌더링 — lecture 변경 시 mermaid.run()
  useEffect(() => {
    if (lectureRef.current) {
      const els = lectureRef.current.querySelectorAll('.mermaid')
      if (els.length > 0) {
        mermaid.run({ nodes: els as any }).catch(() => {})
      }
    }
  }, [lecture])

  // 실습 로드 — admin일 때는 ?admin=1을 붙여 서버에서 answer 포함해서 받기
  const adminParam = searchParams.get('admin')
  useEffect(() => {
    if (viewParam === 'lab' && labIdParam) {
      const qs = isAdmin() ? '?admin=1' : ''
      api(`/api/labs/catalog/${labIdParam}${qs}`)
        .then(d => setLabDetail(d))
        .catch(() => setLabDetail(null))
    } else {
      setLabDetail(null)
    }
  }, [viewParam, labIdParam, adminParam])

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
          <>
            <style>{`
              .lecture-content table { border-collapse: collapse; width: auto; max-width: 100%; margin: 16px 0; font-size: 14px; }
              .lecture-content th, .lecture-content td { border: 1px solid #30363d; padding: 8px 14px; text-align: left; vertical-align: top; }
              .lecture-content th { background: #21262d; color: #e6edf3; font-weight: 600; white-space: nowrap; }
              .lecture-content td { color: #c9d1d9; }
              .lecture-content td code { white-space: normal; word-break: break-word; }
              .lecture-content tr:hover td { background: #1c2128; }
              .lecture-content pre { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 16px 20px; overflow-x: auto; font-size: 14px; line-height: 1.55; }
              .lecture-content code { background: #21262d; padding: 2px 7px; border-radius: 4px; font-size: 0.92em; color: #f97316; font-family: 'D2Coding',Consolas,Monaco,monospace; }
              .lecture-content pre code { background: none; padding: 0; color: inherit; font-size: 14px; }
              .lecture-content h1 { font-size: 26px; border-bottom: 2px solid #f97316; padding-bottom: 10px; margin: 0 0 18px; color: #e6edf3; font-weight: 700; }
              .lecture-content h2 { font-size: 22px; border-bottom: 1px solid #30363d; padding-bottom: 8px; margin-top: 32px; color: #e6edf3; font-weight: 700; }
              .lecture-content h3 { font-size: 19px; margin-top: 24px; color: #e6edf3; font-weight: 600; }
              .lecture-content h4 { font-size: 17px; margin-top: 20px; color: #c9d1d9; font-weight: 600; }
              .lecture-content blockquote { border-left: 3px solid #f97316; padding: 10px 16px; margin: 14px 0; background: #161b22; color: #c9d1d9; border-radius: 0 6px 6px 0; }
              .lecture-content strong { color: #e6edf3; font-weight: 700; }
              .lecture-content img { max-width: 100%; border-radius: 8px; }
              .lecture-content ul, .lecture-content ol { padding-left: 24px; }
              .lecture-content li { margin-bottom: 4px; }
              .lecture-content hr { border: none; border-top: 1px solid #30363d; margin: 28px 0; }
              .lecture-content a { color: #58a6ff; text-decoration: none; }
              .lecture-content a:hover { text-decoration: underline; }
              .lecture-content .mermaid { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin: 14px 0; text-align: center; }
            `}</style>
            <div className="lecture-content" ref={lectureRef} style={{
              background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: '32px 36px',
              fontSize: 16, color: '#c9d1d9', lineHeight: 1.7, maxWidth: 900,
            }} dangerouslySetInnerHTML={{ __html: markdownToHtml(lecture) }} />
          </>
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
                <div style={{ fontSize: 15, color: '#e6edf3', marginBottom: 8, lineHeight: 1.6, whiteSpace: 'pre-wrap' as const }}>{s.instruction}</div>
                {s.bastion_prompt && (
                  <div style={{ background: '#0d1f0d', border: '1px solid #238636', borderRadius: 6, padding: '10px 14px', marginBottom: 8 }}>
                    <div style={{ fontSize: 12, color: '#3fb950', fontWeight: 700, marginBottom: 4 }}>🤖 bastion에 입력하세요</div>
                    <div style={{ fontSize: 14, color: '#e6edf3', whiteSpace: 'pre-wrap' as const }}>{s.bastion_prompt}</div>
                  </div>
                )}
                {s.learning && (s.learning.intent || s.learning.success_criteria?.length > 0 || s.learning.primary_method || s.learning.negative_signs?.length > 0) && (
                  <div style={{ background: '#0d1117', borderLeft: '3px solid #bc8cff', borderRadius: 6, padding: '10px 14px', marginBottom: 8 }}>
                    <div style={{ fontSize: 13, color: '#bc8cff', fontWeight: 700, marginBottom: 6 }}>📖 학습 포인트</div>
                    {s.learning.intent && <div style={{ fontSize: 14, color: '#e6edf3', lineHeight: 1.5, marginBottom: 8, whiteSpace: 'pre-wrap' as const }}>{s.learning.intent}</div>}
                    {s.learning.success_criteria?.length > 0 && (
                      <div style={{ marginTop: 6 }}>
                        <div style={{ fontSize: 13, color: '#3fb950', fontWeight: 600, marginBottom: 2 }}>✅ 합격 조건</div>
                        <ul style={{ margin: '2px 0 0 0', paddingLeft: 22, fontSize: 13, color: '#e6edf3' }}>{s.learning.success_criteria.map((c: string, i: number) => <li key={i}>{c}</li>)}</ul>
                      </div>
                    )}
                    {s.learning.primary_method && <div style={{ marginTop: 6, fontSize: 13, color: '#d29922' }}>💡 추천 방법: <code style={{ background: '#0d1117', padding: '1px 6px', borderRadius: 4, color: '#e6edf3', border: '1px solid #30363d', fontFamily: 'Consolas,Monaco,monospace' }}>{s.learning.primary_method}</code></div>}
                    {s.learning.negative_signs?.length > 0 && (
                      <div style={{ marginTop: 6 }}>
                        <div style={{ fontSize: 13, color: '#f85149', fontWeight: 600, marginBottom: 2 }}>⚠️ 피해야 할 패턴</div>
                        <ul style={{ margin: '2px 0 0 0', paddingLeft: 22, fontSize: 13, color: '#e6edf3' }}>{s.learning.negative_signs.map((n: string, i: number) => <li key={i}>{n}</li>)}</ul>
                      </div>
                    )}
                  </div>
                )}
                {s.hint && <div style={{ fontSize: 14, color: '#58a6ff', background: '#0d1f3c', borderRadius: 6, padding: '8px 12px', marginBottom: 8, whiteSpace: 'pre-wrap' as const }}>Hint: {s.hint}</div>}
                {s.script && <div style={{ fontSize: 14, fontFamily: 'Consolas,Monaco,monospace', color: '#3fb950', background: '#0d1f0d', borderRadius: 6, padding: '8px 12px', marginBottom: 8, whiteSpace: 'pre-wrap' as const }}>$ {s.script}</div>}
                {s.verify && <div style={{ fontSize: 15, color: '#8b949e' }}>Verify: <code style={{ color: '#d29922' }}>{s.verify.type}</code> <code style={{ color: '#bc8cff' }}>"{s.verify.expect}"</code></div>}
                {showAnswers && isAdmin() && s.answer && (
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
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                {w.has_lecture && (
                  <button onClick={() => openLecture(selectedCourse.course_id, w.week)} style={{ ...actionBtn, background: '#21262d', color: '#e6edf3' }}>📖 교안</button>
                )}
                {w.mapped_labs && w.mapped_labs.length > 0 ? (
                  // D-B 매핑: lecture 와 의미 매칭된 lab 들 (cross-course 가능)
                  w.mapped_labs.map((lab: any, i: number) => {
                    const isAi = lab.version === 'ai'
                    const roleColor = lab.role === 'primary' ? (isAi ? '#f97316' : '#58a6ff')
                                    : lab.role === 'review' ? '#8b949e' : '#bc8cff'
                    const roleIcon = lab.role === 'primary' ? '⭐' : lab.role === 'review' ? '↻' : '+'
                    const crossCourse = !lab.lab_id.startsWith(`${selectedCourse.course_id}-`)
                    return (
                      <button key={i} onClick={() => openLab(lab.lab_id)}
                        title={`${lab.role}${lab.note ? ' — ' + lab.note : ''}${crossCourse ? '\n(cross-course: ' + lab.course + ')' : ''}`}
                        style={{ ...actionBtn, color: roleColor, border: `1px solid ${roleColor}33`, fontSize: 13 }}>
                        {roleIcon} {isAi ? '🤖' : '📝'} {lab.course} w{lab.week} {isAi ? 'AI' : ''}
                        {crossCourse && <span style={{ marginLeft: 4, fontSize: 11, color: '#bc8cff' }}>↗</span>}
                      </button>
                    )
                  })
                ) : (
                  // fallback: 자동 join (매핑 없는 과목)
                  <>
                    <button onClick={() => openLab(w.lab_nonai_id)} style={{ ...actionBtn, color: '#58a6ff' }}>📝 Non-AI 실습</button>
                    <button onClick={() => openLab(w.lab_ai_id)} style={{ ...actionBtn, color: '#f97316' }}>🤖 AI 실습</button>
                  </>
                )}
              </div>
              {w.mapped_labs && w.mapped_labs.some((l: any) => l.note) && (
                <div style={{ marginTop: 8, fontSize: 12, color: '#8b949e', lineHeight: 1.5 }}>
                  {w.mapped_labs.filter((l: any) => l.note).map((l: any, i: number) => (
                    <div key={i}>
                      <span style={{ color: '#bc8cff' }}>{l.role}</span> · {l.course} w{l.week}: {l.note}
                    </div>
                  ))}
                </div>
              )}
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
// Design tokens (keep in sync with CSS block above):
//   brand-orange   #f97316 — inline code, h1 accent, blockquote border
//   fg-bright      #e6edf3 — headings, strong, code-block default text
//   fg-body        #c9d1d9 — body text
//   fg-dim         #8b949e — secondary text, blockquote body
//   semantic-green #3fb950 — ONLY for bash/sh code blocks (shell/terminal)
//   surface-1      #161b22 — raised block bg
//   surface-2      #21262d — inline chip bg
//   surface-0      #0d1117 — code block bg
//   border         #30363d
function markdownToHtml(md: string): string {
  // 1. Mermaid → placeholder (이스케이프 전에 보존)
  const mermaidBlocks: string[] = []
  md = md.replace(/```mermaid\n([\s\S]*?)```/g, (_, code) => {
    mermaidBlocks.push(code)
    return `__MERMAID_${mermaidBlocks.length - 1}__`
  })

  // 2. 코드블록도 먼저 placeholder화 — 내부의 `**`, `|`, `# ` 오인 방지
  const codeBlocks: { lang: string; body: string }[] = []
  md = md.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, body) => {
    codeBlocks.push({ lang: (lang || '').toLowerCase(), body })
    return `__CODE_${codeBlocks.length - 1}__`
  })

  // 3. HTML escape + 마크다운 치환
  let html = md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    // 제목 (h1은 브랜드 오렌지 액센트, h2~h4는 흰색 계열)
    .replace(/^#### (.+)$/gm, '<h4 style="font-size:17px;color:#c9d1d9;margin:20px 0 8px;font-weight:600">$1</h4>')
    .replace(/^### (.+)$/gm, '<h3 style="font-size:19px;color:#e6edf3;margin:24px 0 10px;font-weight:600">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="font-size:22px;color:#e6edf3;margin:32px 0 14px;border-bottom:1px solid #30363d;padding-bottom:8px;font-weight:700">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="font-size:26px;color:#e6edf3;margin:0 0 18px;padding-bottom:10px;border-bottom:2px solid #f97316;font-weight:700">$1</h1>')
    // 강조 — 흰색 볼드
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#e6edf3;font-weight:700">$1</strong>')
    // 인라인 코드 — 브랜드 오렌지(명령/경로/키 공통)
    .replace(/`([^`]+)`/g, '<code style="background:#21262d;padding:2px 7px;border-radius:4px;font-size:0.92em;color:#f97316;font-family:\'D2Coding\',Consolas,Monaco,monospace">$1</code>')
    // 블록쿼트 — 브랜드 오렌지 왼쪽 테두리
    .replace(/((?:^&gt; .+(?:\n|$))+)/gm, (match) => {
      const body = match.replace(/^&gt; /gm, '').replace(/\n$/, '').replace(/\n/g, '<br/>')
      return `<div style="border-left:3px solid #f97316;padding:10px 16px;margin:14px 0;background:#161b22;color:#c9d1d9;font-size:15px;border-radius:0 6px 6px 0">${body}</div>`
    })
    // 리스트 — 일관된 불릿/번호, 같은 패딩
    .replace(/^- (.+)$/gm, '<div style="padding:3px 0 3px 22px;font-size:16px;position:relative"><span style="position:absolute;left:6px;color:#f97316">•</span>$1</div>')
    .replace(/^(\d+)\. (.+)$/gm, '<div style="padding:3px 0 3px 22px;font-size:16px;position:relative"><span style="position:absolute;left:0;color:#f97316;font-weight:600">$1.</span>$2</div>')
    // 수평선
    .replace(/^---+$/gm, '<hr style="border:none;border-top:1px solid #30363d;margin:28px 0"/>')

  // 4. 테이블 → 실제 <table> (CSS의 .lecture-content table 스타일 적용)
  html = html.replace(/((?:^\|.*\|\s*\n)+)/gm, (block) => {
    const rows = block.trim().split('\n').filter(r => r.trim().startsWith('|'))
    if (rows.length < 2) return block
    // 2번째 줄이 구분선인지 (--- | --- 형태) 확인
    const sep = rows[1]
    const isHeader = /^\|[\s\-:|]+\|$/.test(sep.trim())
    if (!isHeader) return block
    const parseCells = (row: string) => row.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim())
    const headers = parseCells(rows[0])
    const bodyRows = rows.slice(2).map(parseCells)
    const thead = '<thead><tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr></thead>'
    const tbody = '<tbody>' + bodyRows.map(r => '<tr>' + r.map(c => `<td>${c}</td>`).join('') + '</tr>').join('') + '</tbody>'
    return `<table>${thead}${tbody}</table>`
  })

  // 5. 줄바꿈 (테이블·헤더·블록쿼트·리스트로 이미 치환된 라인은 건너뜀)
  html = html
    .replace(/\n{2,}/g, '<div style="height:10px"></div>')
    .replace(/\n/g, '<br/>')

  // 6. 코드블록 복원 — 언어가 bash/sh면 terminal 그린, 그 외는 중립 흰색
  codeBlocks.forEach(({ lang, body }, i) => {
    const escaped = body.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    const isShell = /^(bash|sh|shell|console|terminal|zsh)$/.test(lang)
    const color = isShell ? '#3fb950' : '#e6edf3'
    const label = lang ? `<div style="position:absolute;top:6px;right:10px;font-size:11px;color:#8b949e;font-family:system-ui;text-transform:uppercase;letter-spacing:0.5px">${lang}</div>` : ''
    const pre = `<div style="position:relative;margin:14px 0">${label}<pre style="background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:16px 20px;font-size:14px;line-height:1.55;overflow-x:auto;color:${color};margin:0;font-family:'D2Coding','Nanum Gothic Coding',Consolas,Monaco,'Courier New',monospace;white-space:pre;tab-size:4;letter-spacing:0">${escaped}</pre></div>`
    html = html.replace(`__CODE_${i}__`, pre)
  })

  // 7. Mermaid 복원
  mermaidBlocks.forEach((code, i) => {
    html = html.replace(`__MERMAID_${i}__`, `<div class="mermaid">${code}</div>`)
  })

  return html
}

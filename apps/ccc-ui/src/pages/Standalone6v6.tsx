import React, { useEffect, useState, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api.ts'
import { isAdmin } from '../auth.ts'
import { markdownToHtml } from '../markdown.ts'
import mermaid from 'mermaid'

mermaid.initialize({ startOnLoad: false, theme: 'dark', themeVariables: {
  primaryColor: '#21262d', primaryTextColor: '#e6edf3', lineColor: '#30363d',
  secondaryColor: '#161b22', tertiaryColor: '#0d1117',
}})

type Course = {
  course_id: string
  title: string
  description: string
  icon: string
  color: string
  lecture_weeks: number[]
  lab_weeks: number[]
  max_week: number
  expected_total: number
}

type Week = {
  week: number
  title: string
  has_lecture: boolean
  has_lab: boolean
}

export default function Standalone6v6() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [weeks, setWeeks] = useState<Week[]>([])
  const [content, setContent] = useState<string | null>(null)
  const [labParsed, setLabParsed] = useState<any>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  const courseId = searchParams.get('course')
  const viewParam = searchParams.get('view') as 'lecture' | 'lab' | null
  const weekParam = searchParams.get('week')

  useEffect(() => {
    api('/api/standalone/courses')
      .then(d => setCourses(d.courses || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!courseId) { setWeeks([]); return }
    api(`/api/standalone/${courseId}/weeks`)
      .then(d => setWeeks(d.weeks || []))
      .catch(e => setError(e.message))
  }, [courseId])

  useEffect(() => {
    if (!courseId || !weekParam || !viewParam) {
      setContent(null)
      setLabParsed(null)
      return
    }
    if (viewParam === 'lecture') {
      api(`/api/standalone/${courseId}/lecture/${weekParam}`)
        .then(d => { setContent(d.content); setLabParsed(null) })
        .catch(() => setContent('# 강의안을 로드할 수 없습니다.'))
    } else if (viewParam === 'lab') {
      const qs = isAdmin() ? '?admin=1' : ''
      api(`/api/standalone/${courseId}/lab/${weekParam}${qs}`)
        .then(d => { setContent(d.raw); setLabParsed(d.parsed) })
        .catch(() => { setContent('# 실습 자료를 로드할 수 없습니다.'); setLabParsed(null) })
    }
  }, [courseId, weekParam, viewParam])

  useEffect(() => {
    if (contentRef.current) {
      const els = contentRef.current.querySelectorAll('.mermaid')
      if (els.length > 0) mermaid.run({ nodes: els as any }).catch(() => {})
    }
  }, [content])

  const selectedCourse = courses.find(c => c.course_id === courseId)

  const openCourse = (cid: string) => setSearchParams({ course: cid })
  const openLecture = (w: number) =>
    setSearchParams({ course: courseId!, view: 'lecture', week: String(w) })
  const openLab = (w: number) =>
    setSearchParams({ course: courseId!, view: 'lab', week: String(w) })
  const back = () => {
    if (viewParam) setSearchParams({ course: courseId! })
    else setSearchParams({})
  }

  if (loading) {
    return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center', fontSize: 15 }}>Loading 6v6 Training...</div>
  }
  if (error) {
    return <div style={{ color: '#f85149', padding: 40, textAlign: 'center' }}>{error}</div>
  }

  // ── 강의안 / 실습 본문 ──
  if (viewParam && weekParam && content !== null) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <button onClick={back} style={{
            background: '#21262d', color: '#8b949e', border: '1px solid #30363d',
            borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 13,
          }}>← 주차 목록</button>
          <div style={{ fontSize: 13, color: '#8b949e' }}>
            {selectedCourse?.icon} {selectedCourse?.title} · Week {weekParam} · {viewParam === 'lecture' ? '강의안' : '실습'}
          </div>
        </div>
        {viewParam === 'lecture' ? (
          <div
            ref={contentRef}
            style={{
              background: '#0d1117', border: '1px solid #30363d', borderRadius: 8,
              padding: '32px 36px', color: '#c9d1d9', fontSize: 15, lineHeight: 1.7,
              fontFamily: "'Pretendard',-apple-system,BlinkMacSystemFont,sans-serif",
            }}
            dangerouslySetInnerHTML={{ __html: markdownToHtml(content) }}
          />
        ) : (
          <LabView raw={content} parsed={labParsed} />
        )}
      </div>
    )
  }

  // ── 주차 목록 ──
  if (selectedCourse) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <button onClick={back} style={{
            background: '#21262d', color: '#8b949e', border: '1px solid #30363d',
            borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 13,
          }}>← 과목 목록</button>
        </div>
        <h1 style={{ fontSize: 26, color: '#e6edf3', margin: '0 0 8px', fontWeight: 700 }}>
          <span style={{ color: selectedCourse.color, marginRight: 10 }}>{selectedCourse.icon}</span>
          {selectedCourse.title}
        </h1>
        <p style={{ color: '#8b949e', fontSize: 14, marginBottom: 24 }}>{selectedCourse.description}</p>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12,
        }}>
          {weeks.map(w => (
            <div key={w.week} style={{
              background: '#161b22', border: '1px solid #30363d', borderRadius: 8,
              padding: 16, opacity: (w.has_lecture || w.has_lab) ? 1 : 0.4,
            }}>
              <div style={{ fontSize: 13, color: selectedCourse.color, fontWeight: 700, marginBottom: 4 }}>
                Week {String(w.week).padStart(2, '0')}
              </div>
              <div style={{ fontSize: 14, color: '#e6edf3', marginBottom: 12, minHeight: 38, lineHeight: 1.4 }}>
                {w.title}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  disabled={!w.has_lecture}
                  onClick={() => openLecture(w.week)}
                  style={{
                    flex: 1, padding: '7px 0', borderRadius: 6,
                    background: w.has_lecture ? '#1f6feb' : '#21262d',
                    color: w.has_lecture ? '#fff' : '#484f58',
                    border: 'none', cursor: w.has_lecture ? 'pointer' : 'not-allowed',
                    fontSize: 12, fontWeight: 600,
                  }}>강의안</button>
                <button
                  disabled={!w.has_lab}
                  onClick={() => openLab(w.week)}
                  style={{
                    flex: 1, padding: '7px 0', borderRadius: 6,
                    background: w.has_lab ? selectedCourse.color : '#21262d',
                    color: w.has_lab ? '#fff' : '#484f58',
                    border: 'none', cursor: w.has_lab ? 'pointer' : 'not-allowed',
                    fontSize: 12, fontWeight: 600,
                  }}>실습</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // ── 과목 카드 (랜딩) ──
  return (
    <div>
      <h1 style={{ fontSize: 28, color: '#e6edf3', margin: '0 0 6px', fontWeight: 700 }}>
        🧪 6v6 Training
      </h1>
      <p style={{ color: '#8b949e', fontSize: 14, marginBottom: 8 }}>
        단일 VM Docker 4-tier 인프라 (ext → fw → ips → dmz → int) 위의 standalone 교육 컨텐츠.
        secuops + attack 각 15주차.
      </p>
      <div style={{
        background: '#0d1117', border: '1px solid #30363d', borderRadius: 6,
        padding: '10px 14px', marginBottom: 24, fontSize: 12, color: '#8b949e',
      }}>
        인프라 빠른 접속:
        <code style={{ color: '#f97316', margin: '0 6px' }}>ssh -p 2204 ccc@&lt;VM_IP&gt;</code>(bastion) ·
        <code style={{ color: '#f97316', margin: '0 6px' }}>ssh -p 2202 ccc@&lt;VM_IP&gt;</code>(attacker) ·
        <code style={{ color: '#f97316', margin: '0 6px' }}>http://siem.6v6.lab/</code>(Wazuh) ·
        <code style={{ color: '#f97316', margin: '0 6px' }}>http://portal.6v6.lab/</code>(운영)
      </div>
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 16,
      }}>
        {courses.map(c => (
          <div key={c.course_id}
            onClick={() => openCourse(c.course_id)}
            style={{
              background: '#161b22', border: `1px solid ${c.color}33`, borderRadius: 10,
              padding: 20, cursor: 'pointer', transition: 'all .15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.borderColor = c.color)}
            onMouseLeave={e => (e.currentTarget.style.borderColor = `${c.color}33`)}
          >
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
              <span style={{ fontSize: 28 }}>{c.icon}</span>
              <h2 style={{ fontSize: 18, color: c.color, margin: 0, fontWeight: 700 }}>{c.title}</h2>
            </div>
            <p style={{ color: '#c9d1d9', fontSize: 13, lineHeight: 1.6, margin: '12px 0' }}>
              {c.description}
            </p>
            <div style={{ display: 'flex', gap: 16, marginTop: 10, fontSize: 12, color: '#8b949e' }}>
              <span>📖 강의 {c.lecture_weeks.length}/{c.expected_total}주</span>
              <span>🎯 실습 {c.lab_weeks.length}/{c.expected_total}주</span>
              {c.max_week > 0 && <span style={{ color: c.color }}>최신 W{String(c.max_week).padStart(2, '0')}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function LabView({ raw, parsed }: { raw: string; parsed: any }) {
  const [tab, setTab] = useState<'parsed' | 'raw'>('parsed')
  if (!parsed) {
    return (
      <pre style={{
        background: '#0d1117', border: '1px solid #30363d', borderRadius: 8,
        padding: 20, color: '#c9d1d9', fontSize: 13, lineHeight: 1.5,
        whiteSpace: 'pre-wrap', overflow: 'auto',
        fontFamily: "'D2Coding',Consolas,Monaco,monospace",
      }}>{raw}</pre>
    )
  }
  const steps: any[] = Array.isArray(parsed.steps) ? parsed.steps : []
  return (
    <div>
      <div style={{ marginBottom: 12, display: 'flex', gap: 8 }}>
        <button onClick={() => setTab('parsed')} style={tabStyle(tab === 'parsed')}>구조화 보기</button>
        <button onClick={() => setTab('raw')} style={tabStyle(tab === 'raw')}>Raw YAML</button>
      </div>
      {tab === 'parsed' ? (
        <div style={{
          background: '#0d1117', border: '1px solid #30363d', borderRadius: 8, padding: 24,
        }}>
          <h1 style={{ fontSize: 22, color: '#e6edf3', margin: '0 0 6px', fontWeight: 700 }}>
            {parsed.title || parsed.lab_id}
          </h1>
          {parsed.description && (
            <p style={{ color: '#c9d1d9', fontSize: 14, whiteSpace: 'pre-wrap', lineHeight: 1.6, margin: '0 0 16px' }}>
              {parsed.description}
            </p>
          )}
          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', fontSize: 12, color: '#8b949e', marginBottom: 20 }}>
            <span>난이도: <span style={{ color: '#f97316' }}>{parsed.difficulty || 'easy'}</span></span>
            <span>소요: <span style={{ color: '#3fb950' }}>{parsed.duration_minutes || '-'}분</span></span>
            <span>통과 기준: <span style={{ color: '#1f6feb' }}>{((parsed.pass_threshold ?? 0.7) * 100).toFixed(0)}%</span></span>
            <span>총 {steps.length} 단계</span>
          </div>
          {parsed.objectives?.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <h3 style={{ fontSize: 15, color: '#e6edf3', margin: '0 0 8px', fontWeight: 600 }}>학습 목표</h3>
              <ul style={{ color: '#c9d1d9', fontSize: 13, lineHeight: 1.7, paddingLeft: 22, margin: 0 }}>
                {parsed.objectives.map((o: string, i: number) => <li key={i}>{o}</li>)}
              </ul>
            </div>
          )}
          {steps.map((s, idx) => (
            <div key={idx} style={{
              background: '#161b22', border: '1px solid #30363d', borderRadius: 8,
              padding: 16, marginBottom: 12,
            }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 8 }}>
                <span style={{
                  background: '#1f6feb', color: '#fff', borderRadius: 4,
                  padding: '2px 8px', fontSize: 12, fontWeight: 700,
                }}>STEP {s.order}</span>
                <span style={{ color: '#8b949e', fontSize: 11, textTransform: 'uppercase' }}>
                  {s.category} · {s.points}pt
                </span>
              </div>
              <div style={{ color: '#e6edf3', fontSize: 14, lineHeight: 1.6, whiteSpace: 'pre-wrap', marginBottom: 10 }}>
                {s.instruction}
              </div>
              {s.hint && (
                <div style={{ background: '#0d1117', padding: '8px 12px', borderRadius: 6, fontSize: 12, color: '#3fb950', fontFamily: 'monospace', marginBottom: 8 }}>
                  💡 힌트: {s.hint}
                </div>
              )}
              {s.answer && (
                <details style={{ marginTop: 8 }}>
                  <summary style={{ cursor: 'pointer', color: '#f97316', fontSize: 12 }}>모범 답안 보기</summary>
                  <pre style={{
                    background: '#0d1117', padding: 12, borderRadius: 6, fontSize: 12,
                    color: '#c9d1d9', whiteSpace: 'pre-wrap', overflow: 'auto',
                    fontFamily: "'D2Coding',Consolas,Monaco,monospace", margin: '6px 0 0',
                  }}>{s.answer}</pre>
                </details>
              )}
              {s.verify?.semantic?.acceptable_methods?.length > 0 && (
                <details style={{ marginTop: 8 }}>
                  <summary style={{ cursor: 'pointer', color: '#bc8cff', fontSize: 12 }}>
                    수용 가능한 방법 ({s.verify.semantic.acceptable_methods.length}건)
                  </summary>
                  <div style={{ marginTop: 8 }}>
                    {s.verify.semantic.acceptable_methods.map((m: any, mi: number) => (
                      <pre key={mi} style={{
                        background: '#0d1117', padding: 10, borderRadius: 6, fontSize: 11,
                        color: '#c9d1d9', whiteSpace: 'pre-wrap', overflow: 'auto',
                        fontFamily: "'D2Coding',Consolas,Monaco,monospace", margin: '6px 0',
                        border: '1px solid #21262d',
                      }}>{typeof m === 'string' ? m : JSON.stringify(m, null, 2)}</pre>
                    ))}
                  </div>
                </details>
              )}
            </div>
          ))}
        </div>
      ) : (
        <pre style={{
          background: '#0d1117', border: '1px solid #30363d', borderRadius: 8,
          padding: 20, color: '#c9d1d9', fontSize: 12, lineHeight: 1.5,
          whiteSpace: 'pre-wrap', overflow: 'auto', maxHeight: '70vh',
          fontFamily: "'D2Coding',Consolas,Monaco,monospace",
        }}>{raw}</pre>
      )}
    </div>
  )
}

function tabStyle(active: boolean): React.CSSProperties {
  return {
    padding: '6px 14px', borderRadius: 6,
    background: active ? '#f97316' : '#21262d',
    color: active ? '#fff' : '#8b949e',
    border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600,
  }
}

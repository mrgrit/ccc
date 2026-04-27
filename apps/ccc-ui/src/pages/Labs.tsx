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
  // P14 — Lab session 흐름 (SubAgent 감시 기반)
  const [activeSession, setActiveSession] = useState<any>(null)   // {session: {id, started_at, ...}, capture_mode}
  const [transcriptText, setTranscriptText] = useState('')        // 학생이 paste 한 명령 transcript (B 사이클까지 임시)
  const [sessionResult, setSessionResult] = useState<any>(null)   // /sessions/{id}/end 응답
  const [elapsed, setElapsed] = useState(0)                       // 경과 초

  // 활성 세션 elapsed 타이머
  useEffect(() => {
    if (!activeSession) return
    const t0 = new Date(activeSession.session?.started_at || Date.now()).getTime()
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - t0) / 1000)), 1000)
    return () => clearInterval(id)
  }, [activeSession])

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
    setActiveSession(null)
    setSessionResult(null)
    setTranscriptText('')
    setElapsed(0)
    try {
      // admin/instructor는 정답 포함해서 받기
      const qs = isAdmin() ? '?admin=1' : ''
      const d = await api(`/api/labs/catalog/${labId}${qs}`)
      setActiveLab(d)
    } catch (e: any) { alert('Failed: ' + e.message) }
  }

  // P14 — Lab session 시작.
  // vm_ip 인자 있으면 SubAgent audit 모드 (자동 캡처). 없으면 manual_paste 모드.
  const startSession = async (vmIp: string = '') => {
    if (!activeLab) return
    try {
      const user = getUser()
      const d = await api('/api/labs/sessions/start', {
        method: 'POST',
        body: JSON.stringify({
          lab_id: activeLab.lab_id,
          student_id: user?.id || 'anonymous',
          vm_ip: vmIp,
        }),
      })
      setActiveSession(d)
      setSessionResult(null)
      setTranscriptText('')
    } catch (e: any) { alert('Session start failed: ' + e.message) }
  }

  // P14 B — audit 모드에서 학생이 [Run] 누를 때마다 SubAgent 에 명령 실행 위임
  const [cmdInput, setCmdInput] = useState('')
  const [cmdRunning, setCmdRunning] = useState(false)
  const runCommand = async () => {
    if (!activeSession || !cmdInput.trim()) return
    if (activeSession.capture_mode !== 'subagent_audit') {
      alert('Audit 모드 아님 — manual paste 사용'); return
    }
    setCmdRunning(true)
    try {
      const sid = activeSession.session?.id
      const d = await api(`/api/labs/sessions/${sid}/run`, {
        method: 'POST',
        body: JSON.stringify({ script: cmdInput, timeout: 30 }),
      })
      // transcriptText 에 자동 누적 (학생 시각화)
      const append = `$ ${cmdInput}\n${(d.stdout || '') + (d.stderr ? '\n[stderr] ' + d.stderr : '')}\n`
      setTranscriptText(prev => prev + append)
      setCmdInput('')
    } catch (e: any) { alert('Run failed: ' + e.message) }
    setCmdRunning(false)
  }

  // P14 — Lab 완료 → transcript + answers 채점 요청
  const endSession = async () => {
    if (!activeSession) return
    setSubmitting(true)
    try {
      // transcript paste 파싱: 줄별 — 첫 토큰이 $ 면 cmd, 그 외는 stdout
      const commands: any[] = []
      let curCmd: any = null
      for (const line of transcriptText.split('\n')) {
        const m = line.match(/^\s*\$\s+(.+)$/)
        if (m) {
          if (curCmd) commands.push(curCmd)
          curCmd = { ts: new Date().toISOString(), cmd: m[1], stdout: '', exit: 0 }
        } else if (curCmd) {
          curCmd.stdout = (curCmd.stdout || '') + (curCmd.stdout ? '\n' : '') + line
        }
      }
      if (curCmd) commands.push(curCmd)

      // step 별 텍스트 답변 (text 모드)
      const answersStr: Record<string, string> = {}
      for (const [k, v] of Object.entries(answers)) {
        if ((v || '').trim()) answersStr[String(k)] = v
      }

      const sid = activeSession.session?.id
      const d = await api(`/api/labs/sessions/${sid}/end`, {
        method: 'POST',
        body: JSON.stringify({
          transcript: { capture_mode: 'manual_paste', commands },
          answers: answersStr,
        }),
      })
      setSessionResult(d)
      setActiveSession(null)
    } catch (e: any) { alert('Session end failed: ' + e.message) }
    setSubmitting(false)
  }

  const retrySession = () => {
    setSessionResult(null)
    setAnswers({})
    setTranscriptText('')
    setElapsed(0)
  }

  const fmtElapsed = (s: number) => {
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60
    return h > 0 ? `${h}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}` : `${m}:${String(sec).padStart(2,'0')}`
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
    const sessionActive = !!activeSession && !sessionResult
    const sessionDone = !!sessionResult
    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <button onClick={() => { setActiveLab(null); setResult(null); setActiveSession(null); setSessionResult(null) }} style={backBtn}>Back</button>
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

        {/* P14: Lab 세션 컨트롤 — [시작] / 활성중 (경과시간) / 완료 / 재시도 */}
        <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: 8, padding: '12px 16px', marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {!activeSession && !sessionResult && (
              <>
                <button onClick={() => startSession('')} style={{ padding: '8px 18px', borderRadius: 6, border: 'none', background: '#238636', color: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 700 }}>▶ Lab 시작</button>
                <button onClick={() => {
                  const ip = window.prompt('SubAgent 감시 모드 — 학생 VM IP 입력 (예: 10.20.30.50)')
                  if (ip && ip.trim()) startSession(ip.trim())
                }} style={{ padding: '8px 14px', borderRadius: 6, border: '1px solid #238636', background: 'transparent', color: '#3fb950', cursor: 'pointer', fontSize: 13, fontWeight: 600 }}>
                  🟢 + SubAgent 감시
                </button>
                <span style={{ fontSize: 13, color: '#8b949e' }}>학생이 직접 명령 실행 / 메모 작성 후 [완료] 누르면 채점</span>
              </>
            )}
            {sessionActive && (
              <>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 10px', borderRadius: 12, background: '#0d1f0d', color: '#3fb950', fontSize: 13, fontWeight: 600 }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#3fb950', animation: 'pulse 1.5s infinite' }} />
                  세션 활성 — {fmtElapsed(elapsed)}
                </span>
                <span style={{ fontSize: 12, color: '#8b949e' }}>session: {activeSession.session?.id?.slice(0, 16)}…</span>
              </>
            )}
            {sessionDone && (
              <span style={{ padding: '4px 12px', borderRadius: 12, background: sessionResult.passed ? '#0d1f0d' : '#1f0d0d', color: sessionResult.passed ? '#3fb950' : '#f85149', fontSize: 14, fontWeight: 700 }}>
                {sessionResult.passed ? '✓ PASSED' : '✗ FAILED'} — {sessionResult.score}/{sessionResult.total_score}pts
              </span>
            )}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {sessionActive && (
              <button onClick={endSession} disabled={submitting} style={{ padding: '8px 18px', borderRadius: 6, border: 'none', background: '#f97316', color: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 700 }}>
                {submitting ? '채점 중…' : '⏹ Lab 완료'}
              </button>
            )}
            {sessionDone && (
              <button onClick={() => { retrySession(); startSession() }} style={{ padding: '8px 18px', borderRadius: 6, border: '1px solid #30363d', background: '#21262d', color: '#e6edf3', cursor: 'pointer', fontSize: 14 }}>↻ 재시도</button>
            )}
          </div>
        </div>

        {/* P14: transcript 영역 — audit 모드 (실시간 명령 실행) vs paste 모드 */}
        {sessionActive && activeSession?.capture_mode === 'subagent_audit' && (
          <div style={{ background: '#0d1117', border: '1px solid #238636', borderRadius: 8, padding: 12, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
              <span style={{ fontSize: 13, color: '#3fb950', fontWeight: 600 }}>🟢 SubAgent 감시 모드 — 실시간 명령 실행</span>
              <span style={{ fontSize: 12, color: '#8b949e' }}>vm_ip: {activeSession.session?.vm_ip}</span>
            </div>
            <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
              <input
                type="text"
                value={cmdInput}
                onChange={e => setCmdInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') runCommand() }}
                placeholder="실행할 명령 (예: nmap -sV 10.20.30.100)"
                disabled={cmdRunning}
                style={{ flex: 1, background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d', borderRadius: 6, padding: '8px 10px', fontSize: 13, fontFamily: 'Consolas,Monaco,monospace' }}
              />
              <button onClick={runCommand} disabled={cmdRunning || !cmdInput.trim()} style={{ padding: '8px 14px', borderRadius: 6, border: 'none', background: '#238636', color: '#fff', cursor: 'pointer', fontSize: 13, fontWeight: 700 }}>
                {cmdRunning ? '...' : '▶ Run'}
              </button>
            </div>
            <pre style={{ margin: 0, background: '#0d1117', color: '#c9d1d9', border: '1px solid #21262d', borderRadius: 6, padding: '8px 10px', fontSize: 12, fontFamily: 'Consolas,Monaco,monospace', maxHeight: 240, overflow: 'auto', whiteSpace: 'pre-wrap' }}>
              {transcriptText || '(명령 실행 결과가 여기에 누적됩니다)'}
            </pre>
          </div>
        )}
        {sessionActive && activeSession?.capture_mode !== 'subagent_audit' && (
          <div style={{ background: '#0d1117', border: '1px dashed #30363d', borderRadius: 8, padding: 12, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
              <span style={{ fontSize: 13, color: '#bc8cff', fontWeight: 600 }}>📋 명령 transcript (paste 모드)</span>
              <span style={{ fontSize: 12, color: '#8b949e' }}>형식: <code style={{ background: '#161b22', padding: '0 4px', borderRadius: 3 }}>$ cmd</code> 줄 + 다음 줄들에 출력</span>
            </div>
            <textarea
              value={transcriptText}
              onChange={e => setTranscriptText(e.target.value)}
              placeholder={'$ hostname\nbastion\n$ ip -4 addr show\ninet 10.20.30.201/24'}
              style={{ width: '100%', minHeight: 90, resize: 'vertical', background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d', borderRadius: 6, padding: '8px 10px', fontSize: 13, fontFamily: 'Consolas,Monaco,monospace' }}
            />
            <div style={{ marginTop: 4, fontSize: 12, color: '#484f58' }}>
              vm_ip 미지정 → SubAgent 자동 캡처 비활성. SSH 등에서 실행 후 결과 paste.
              vm_ip 모드로 시작하려면 [Lab 시작] 옆 vm_ip 입력 필요 (admin/instructor).
            </div>
          </div>
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

        {/* 문제 목록 — 모든 step 한 번에 (Part 그룹 폐기) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {(activeLab.steps || []).map((s: any) => {
            // 새 흐름: sessionResult.step_results, fallback: result.step_results
            const stepResult = sessionResult?.step_results?.find((r: any) => r.order === s.order)
              || result?.step_results?.find((r: any) => r.order === s.order)
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
                    {s.input_mode && (
                      <span style={{ fontSize: 11, padding: '2px 6px', borderRadius: 4, background: s.input_mode === 'transcript' ? '#1f3a1f' : '#1f1f3a', color: s.input_mode === 'transcript' ? '#3fb950' : '#79c0ff', fontFamily: 'Consolas,Monaco,monospace' }}>
                        {s.input_mode === 'transcript' ? '⌨ transcript' : '✎ text'}
                      </span>
                    )}
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

                {s.learning && (s.learning.intent || s.learning.success_criteria?.length > 0 || s.learning.primary_method || s.learning.negative_signs?.length > 0) && (
                  <div style={{ background: '#0d1117', borderLeft: '3px solid #bc8cff', borderRadius: 6, padding: '10px 14px', marginBottom: 10 }}>
                    <div style={{ fontSize: 13, color: '#bc8cff', fontWeight: 700, marginBottom: 6 }}>📖 학습 포인트</div>
                    {s.learning.intent && (
                      <div style={{ fontSize: 14, color: '#e6edf3', lineHeight: 1.5, marginBottom: 8, whiteSpace: 'pre-wrap' as const }}>{s.learning.intent}</div>
                    )}
                    {s.learning.success_criteria?.length > 0 && (
                      <div style={{ marginTop: 6 }}>
                        <div style={{ fontSize: 13, color: '#3fb950', fontWeight: 600, marginBottom: 2 }}>✅ 합격 조건</div>
                        <ul style={{ margin: '2px 0 0 0', paddingLeft: 22, fontSize: 13, color: '#e6edf3' }}>
                          {s.learning.success_criteria.map((c: string, i: number) => <li key={i}>{c}</li>)}
                        </ul>
                      </div>
                    )}
                    {s.learning.primary_method && (
                      <div style={{ marginTop: 6, fontSize: 13, color: '#d29922' }}>
                        💡 추천 방법: <code style={{ background: '#0d1117', padding: '1px 6px', borderRadius: 4, color: '#e6edf3', border: '1px solid #30363d', fontFamily: 'Consolas,Monaco,monospace' }}>{s.learning.primary_method}</code>
                      </div>
                    )}
                    {s.learning.negative_signs?.length > 0 && (
                      <div style={{ marginTop: 6 }}>
                        <div style={{ fontSize: 13, color: '#f85149', fontWeight: 600, marginBottom: 2 }}>⚠️ 피해야 할 패턴</div>
                        <ul style={{ margin: '2px 0 0 0', paddingLeft: 22, fontSize: 13, color: '#e6edf3' }}>
                          {s.learning.negative_signs.map((n: string, i: number) => <li key={i}>{n}</li>)}
                        </ul>
                      </div>
                    )}
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

        {/* 결과 — 새 흐름 (sessionResult) */}
        {sessionResult && (
          <div style={{ marginTop: 20, padding: 16, borderRadius: 8,
            background: sessionResult.passed ? '#0d1f0d' : '#1f0d0d',
            border: `1px solid ${sessionResult.passed ? '#238636' : '#da3633'}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 700, color: sessionResult.passed ? '#3fb950' : '#f85149' }}>
                  {sessionResult.passed ? '✓ PASSED' : '✗ FAILED'}
                </div>
                <div style={{ fontSize: 15, color: '#8b949e' }}>
                  {sessionResult.score}/{sessionResult.total_score}pts
                  ({sessionResult.total_score > 0 ? Math.round(sessionResult.score / sessionResult.total_score * 100) : 0}%)
                  · {(sessionResult.step_results || []).filter((r: any) => r.passed).length}/{(sessionResult.step_results || []).length} steps passed
                </div>
              </div>
              <button onClick={() => { retrySession(); startSession() }} style={{
                padding: '8px 20px', borderRadius: 6, border: '1px solid #30363d',
                background: '#21262d', color: '#e6edf3', cursor: 'pointer', fontSize: 15,
              }}>↻ 재시도</button>
            </div>
            {/* 미통과 step 의 reason 요약 */}
            {(sessionResult.step_results || []).some((r: any) => !r.passed) && (
              <details style={{ marginTop: 10 }}>
                <summary style={{ cursor: 'pointer', fontSize: 13, color: '#8b949e' }}>미통과 step 사유 보기</summary>
                <ul style={{ margin: '8px 0 0 0', paddingLeft: 22, fontSize: 13, color: '#c9d1d9' }}>
                  {(sessionResult.step_results || []).filter((r: any) => !r.passed).map((r: any) => (
                    <li key={r.order} style={{ marginBottom: 4 }}>
                      <span style={{ color: '#f85149' }}>step {r.order}</span>{' '}
                      <span style={{ color: '#8b949e' }}>[{r.input_mode || '?'}/{r.graded_via || '?'}]</span>{' '}
                      {r.reason}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        )}

        {/* 레거시 결과 — admin /labs/evaluate 흐름 fallback */}
        {result && !sessionResult && (
          <div style={{ marginTop: 20, padding: 16, borderRadius: 8,
            background: result.passed ? '#0d1f0d' : '#1f0d0d',
            border: `1px solid ${result.passed ? '#238636' : '#da3633'}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 700, color: result.passed ? '#3fb950' : '#f85149' }}>
                {result.passed ? 'PASSED' : 'FAILED'} (legacy)
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

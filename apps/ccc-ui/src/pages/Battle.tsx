import React, { useEffect, useState, useRef } from 'react'
import { api } from '../api.ts'
import { getUser, isAdmin } from '../auth.ts'

export default function Battle() {
  const user = getUser()
  const [view, setView] = useState<'lobby' | 'battle'>('lobby')
  const [battles, setBattles] = useState<any[]>([])
  const [scenarios, setScenarios] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeBattle, setActiveBattle] = useState<any>(null)
  const [missions, setMissions] = useState<any[]>([])
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [events, setEvents] = useState<any[]>([])
  const [battleInfo, setBattleInfo] = useState<any>(null)
  const pollRef = useRef<any>(null)

  // 로비 데이터 로드
  const loadLobby = async () => {
    try {
      const [b, s] = await Promise.all([
        api('/api/battles').then(d => d.battles || []),
        api('/api/battles/scenarios').then(d => d.scenarios || []),
      ])
      setBattles(b)
      setScenarios(s)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { loadLobby() }, [])

  // 대전 개설
  const createBattle = async (scenarioId: string) => {
    try {
      const d = await api('/api/battles/create', { method: 'POST', body: JSON.stringify({ scenario_id: scenarioId }) })
      loadLobby()
    } catch (e: any) { alert(e.message) }
  }

  // 참가 (인프라 체크)
  const joinBattle = async (bid: string, team: string) => {
    try {
      // 내 인프라 있는지 확인
      const infras = await api(`/api/infras?student_id=${user?.id}`).then(d => d.infras || []).catch(() => [])
      if (infras.length === 0) {
        alert('인프라가 등록되어 있지 않습니다.\nMy Infra 메뉴에서 먼저 인프라를 등록하세요.')
        return
      }
      await api(`/api/battles/${bid}/join`, { method: 'POST', body: JSON.stringify({ team }) })
      loadLobby()
    } catch (e: any) { alert(e.message) }
  }

  // Ready + 입장
  const readyAndEnter = async (bid: string) => {
    try {
      const d = await api(`/api/battles/${bid}/ready`, { method: 'POST' })
      enterBattle(bid)
    } catch (e: any) { alert(e.message) }
  }

  // 대전 입장
  const enterBattle = async (bid: string) => {
    try {
      const d = await api(`/api/battles/${bid}/my-missions`)
      setBattleInfo(d)
      setMissions(d.missions || [])
      setActiveBattle(bid)
      setView('battle')
      // 이벤트 폴링 시작
      startPolling(bid)
    } catch (e: any) { alert(e.message) }
  }

  // 미션 제출
  const submitMission = async (order: number) => {
    if (!activeBattle || !answers[order]) return
    try {
      const d = await api(`/api/battles/${activeBattle}/submit-mission`, {
        method: 'POST',
        body: JSON.stringify({ mission_order: order, answer: answers[order] }),
      })
      // 새로고침
      const info = await api(`/api/battles/${activeBattle}/my-missions`)
      setBattleInfo(info)
      setMissions(info.missions || [])
    } catch (e: any) { alert(e.message) }
  }

  // 이벤트 폴링
  const startPolling = (bid: string) => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const [info, evts] = await Promise.all([
          api(`/api/battles/${bid}/my-missions`),
          api(`/api/battles/${bid}/events`).then(d => d.events || []).catch(() => []),
        ])
        setBattleInfo(info)
        setMissions(info.missions || [])
        setEvents(evts)
        if (info.status === 'completed' || info.time_remaining <= 0) {
          clearInterval(pollRef.current)
        }
      } catch {}
    }, 3000)
  }

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  // 로비로 돌아가기
  const backToLobby = () => {
    if (pollRef.current) clearInterval(pollRef.current)
    setView('lobby')
    setActiveBattle(null)
    loadLobby()
  }

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>

  // ══════════════════════════════════════
  //  대전 진행 화면
  // ══════════════════════════════════════
  if (view === 'battle' && battleInfo) {
    const isRed = battleInfo.team === 'red'
    const myScore = isRed ? battleInfo.red_score : battleInfo.blue_score
    const opScore = isRed ? battleInfo.blue_score : battleInfo.red_score
    const mins = Math.floor(battleInfo.time_remaining / 60)
    const secs = battleInfo.time_remaining % 60
    const completed = battleInfo.status === 'completed' || battleInfo.time_remaining <= 0

    return (
      <div>
        {/* 상단 바 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, background: '#161b22', borderRadius: 10, padding: '16px 24px', border: '1px solid #30363d' }}>
          <button onClick={backToLobby} style={backBtn}>Lobby</button>
          <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 12, color: '#f85149', fontWeight: 600 }}>RED</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#f85149' }}>{battleInfo.red_score}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: completed ? '#8b949e' : '#e6edf3' }}>
                {completed ? 'FINISHED' : `${mins}:${String(Math.floor(secs)).padStart(2, '0')}`}
              </div>
              <div style={{ fontSize: 11, color: '#8b949e' }}>vs</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 12, color: '#58a6ff', fontWeight: 600 }}>BLUE</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#58a6ff' }}>{battleInfo.blue_score}</div>
            </div>
          </div>
          <div style={{ fontSize: 14, padding: '6px 14px', borderRadius: 8, background: isRed ? '#f8514922' : '#58a6ff22', color: isRed ? '#f85149' : '#58a6ff', fontWeight: 700 }}>
            You: {battleInfo.team.toUpperCase()}
          </div>
        </div>

        {/* 결과 */}
        {completed && (
          <div style={{
            background: myScore > opScore ? '#0d1f0d' : myScore < opScore ? '#1f0d0d' : '#1f1f0d',
            border: `1px solid ${myScore > opScore ? '#238636' : myScore < opScore ? '#da3633' : '#d29922'}`,
            borderRadius: 10, padding: 20, marginBottom: 20, textAlign: 'center',
          }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: myScore > opScore ? '#3fb950' : myScore < opScore ? '#f85149' : '#d29922' }}>
              {myScore > opScore ? 'VICTORY!' : myScore < opScore ? 'DEFEAT' : 'DRAW'}
            </div>
            <div style={{ fontSize: 14, color: '#8b949e', marginTop: 4 }}>
              {myScore}pts vs {opScore}pts
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: 20 }}>
          {/* 미션 */}
          <div style={{ flex: 2 }}>
            <h3 style={{ fontSize: 17, marginBottom: 14, color: '#e6edf3' }}>My Missions ({missions.filter(m => m.status === 'completed').length}/{missions.length})</h3>
            {missions.map(m => (
              <div key={m.mission_order} style={{
                background: '#161b22', borderRadius: 8, padding: 16, marginBottom: 10,
                border: `1px solid ${m.status === 'completed' ? '#238636' : '#30363d'}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span style={{
                      width: 26, height: 26, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 13, fontWeight: 700,
                      background: m.status === 'completed' ? '#238636' : '#21262d',
                      color: m.status === 'completed' ? '#fff' : '#f97316',
                    }}>{m.status === 'completed' ? '✓' : m.mission_order}</span>
                    <span style={{ fontSize: 13, color: '#8b949e' }}>{m.points}pts</span>
                  </div>
                  {m.status === 'completed' && <span style={{ fontSize: 13, color: '#3fb950', fontWeight: 600 }}>+{m.points}pts</span>}
                </div>
                <div style={{ fontSize: 15, color: '#e6edf3', marginBottom: 8, lineHeight: 1.5 }}>{m.instruction}</div>
                {m.hint && <div style={{ fontSize: 13, color: '#58a6ff', marginBottom: 8 }}>Hint: {m.hint}</div>}
                {m.status !== 'completed' && !completed && (
                  <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                    <textarea
                      value={answers[m.mission_order] || ''}
                      onChange={e => setAnswers({ ...answers, [m.mission_order]: e.target.value })}
                      placeholder="답변 입력..."
                      style={{ flex: 1, minHeight: 50, background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d', borderRadius: 6, padding: '8px 12px', fontSize: 14, fontFamily: 'Consolas,Monaco,monospace', resize: 'vertical' }}
                    />
                    <button onClick={() => submitMission(m.mission_order)} style={{
                      padding: '8px 18px', borderRadius: 6, border: 'none', background: '#f97316', color: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 600, alignSelf: 'flex-end',
                    }}>Submit</button>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* 이벤트 피드 */}
          <div style={{ flex: 1 }}>
            <h3 style={{ fontSize: 17, marginBottom: 14, color: '#e6edf3' }}>Live Events</h3>
            <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 14, maxHeight: 500, overflowY: 'auto' }}>
              {events.length === 0 ? (
                <div style={{ color: '#8b949e', textAlign: 'center', padding: 20 }}>Waiting for events...</div>
              ) : events.slice(-20).reverse().map((e, i) => (
                <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #21262d', fontSize: 13 }}>
                  <span style={{ color: e.team === 'red' ? '#f85149' : '#58a6ff', fontWeight: 600, marginRight: 8 }}>
                    {e.team === 'red' ? 'RED' : 'BLUE'}
                  </span>
                  <span style={{ color: '#8b949e' }}>{e.description}</span>
                  {e.points > 0 && <span style={{ color: '#3fb950', marginLeft: 6 }}>+{e.points}</span>}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ══════════════════════════════════════
  //  로비
  // ══════════════════════════════════════
  const waiting = battles.filter(b => b.status === 'waiting')
  const active = battles.filter(b => b.status === 'active')
  const completed = battles.filter(b => b.status === 'completed')

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#e6edf3' }}>Battlefield</h2>

      {/* 시나리오 선택 + 개설 */}
      {scenarios.length > 0 && (
        <div style={{ marginBottom: 28 }}>
          <h3 style={{ fontSize: 16, marginBottom: 16, color: '#8b949e' }}>
            시나리오 ({scenarios.length})
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {scenarios.map(s => {
              const diffColor: Record<string, string> = { easy: '#3fb950', medium: '#d29922', hard: '#f85149' }
              return (
                <div key={s.id} style={{
                  background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: '20px 24px',
                  borderLeft: `4px solid ${diffColor[s.difficulty] || '#8b949e'}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                        <span style={{ fontSize: 18, fontWeight: 700, color: '#e6edf3' }}>{s.title}</span>
                        <span style={{
                          fontSize: 11, padding: '2px 10px', borderRadius: 10, fontWeight: 600,
                          background: `${diffColor[s.difficulty] || '#8b949e'}15`,
                          color: diffColor[s.difficulty] || '#8b949e',
                          textTransform: 'uppercase' as const,
                        }}>{s.difficulty}</span>
                      </div>
                      <div style={{ fontSize: 14, color: '#8b949e', lineHeight: 1.6, marginBottom: 10 }}>
                        {s.description}
                      </div>
                      <div style={{ display: 'flex', gap: 16, fontSize: 13 }}>
                        <span style={{ color: '#8b949e' }}>{Math.floor(s.time_limit / 60)}분</span>
                        <span style={{ color: '#f85149' }}>Red {s.red_missions} missions</span>
                        <span style={{ color: '#58a6ff' }}>Blue {s.blue_missions} missions</span>
                      </div>
                    </div>
                    {isAdmin() && (
                      <button onClick={() => createBattle(s.id)} style={{
                        padding: '10px 24px', borderRadius: 8, border: 'none', whiteSpace: 'nowrap' as const,
                        background: '#f97316', color: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 600,
                      }}>개설</button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 참가 가능한 대전 */}
      <h3 style={{ fontSize: 16, marginBottom: 12 }}>참가 가능 ({waiting.length})</h3>
      {waiting.length === 0 ? (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 30, textAlign: 'center', color: '#8b949e', marginBottom: 24 }}>대전이 없습니다</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
          {waiting.map(b => {
            const amRed = b.red_id === user?.id
            const amBlue = b.blue_id === user?.id
            const amIn = amRed || amBlue
            return (
              <div key={b.id} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3', marginBottom: 4 }}>{b.scenario_id || 'Battle'}</div>
                  <div style={{ fontSize: 13, display: 'flex', gap: 12 }}>
                    <span style={{ color: '#f85149' }}>Red: {b.red_name || (b.red_id ? b.red_id.slice(0, 8) : '(빈자리)')}</span>
                    <span style={{ color: '#58a6ff' }}>Blue: {b.blue_name || (b.blue_id ? b.blue_id.slice(0, 8) : '(빈자리)')}</span>
                    <span style={{ color: '#8b949e' }}>{Math.floor(b.time_limit / 60)}분</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  {!b.red_id && !amIn && <button onClick={() => joinBattle(b.id, 'red')} style={{ ...joinBtn, color: '#f85149', borderColor: '#f85149' }}>Red 참가</button>}
                  {!b.blue_id && !amIn && <button onClick={() => joinBattle(b.id, 'blue')} style={{ ...joinBtn, color: '#58a6ff', borderColor: '#58a6ff' }}>Blue 참가</button>}
                  {amIn && <button onClick={() => readyAndEnter(b.id)} style={{ ...joinBtn, background: '#f97316', color: '#fff', border: 'none' }}>Ready &amp; Enter</button>}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* 진행 중 */}
      <h3 style={{ fontSize: 16, marginBottom: 12 }}>진행 중 ({active.length})</h3>
      {active.length === 0 ? (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 20, textAlign: 'center', color: '#8b949e', marginBottom: 24 }}>없음</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
          {active.map(b => {
            const amIn = b.red_id === user?.id || b.blue_id === user?.id
            return (
              <div key={b.id} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <span style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3' }}>{b.scenario_id}</span>
                  <span style={{ fontSize: 13, color: '#8b949e', marginLeft: 12 }}>
                    <span style={{ color: '#f85149' }}>{b.red_name || '?'} {b.red_score || 0}</span> vs <span style={{ color: '#58a6ff' }}>{b.blue_name || '?'} {b.blue_score || 0}</span>
                  </span>
                </div>
                {amIn && <button onClick={() => enterBattle(b.id)} style={{ ...joinBtn, background: '#238636', color: '#fff', border: 'none' }}>Enter</button>}
                {!amIn && <span style={{ color: '#8b949e', fontSize: 13 }}>관전</span>}
              </div>
            )
          })}
        </div>
      )}

      {/* 완료 */}
      {completed.length > 0 && <>
        <h3 style={{ fontSize: 16, marginBottom: 12 }}>완료 ({completed.length})</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {completed.slice(0, 10).map(b => (
            <div key={b.id} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 14, display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
              <span style={{ color: '#8b949e' }}>{b.scenario_id}</span>
              <span>
                <span style={{ color: '#f85149' }}>{b.red_name || '?'} {b.red_score || 0}</span>
                <span style={{ color: '#484f58', margin: '0 8px' }}>vs</span>
                <span style={{ color: '#58a6ff' }}>{b.blue_name || '?'} {b.blue_score || 0}</span>
              </span>
              <span style={{ color: '#8b949e', fontSize: 12 }}>{b.block_hash ? '⛓' : ''}</span>
            </div>
          ))}
        </div>
      </>}
    </div>
  )
}

const backBtn: React.CSSProperties = { background: '#21262d', color: '#8b949e', border: '1px solid #30363d', borderRadius: 6, padding: '7px 14px', cursor: 'pointer', fontSize: 13 }
const joinBtn: React.CSSProperties = { padding: '8px 16px', borderRadius: 6, border: '1px solid #30363d', background: 'transparent', cursor: 'pointer', fontSize: 14, fontWeight: 600 }

import React, { useEffect, useState, useRef } from 'react'
import { api } from '../api.ts'
import { getUser, isAdmin } from '../auth.ts'

export default function Battle() {
  const user = getUser()
  const [view, setView] = useState<'lobby' | 'battle'>('lobby')
  const [battles, setBattles] = useState<any[]>([])
  const [scenarios, setScenarios] = useState<any[]>([])
  const [vulnSites, setVulnSites] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeBattle, setActiveBattle] = useState<any>(null)
  const [missions, setMissions] = useState<any[]>([])
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [events, setEvents] = useState<any[]>([])
  const [battleInfo, setBattleInfo] = useState<any>(null)
  // P12 UI 개선: claim 제출 진행 / 자동 새로고침 토글 / score history (sparkline)
  const [claimSubmitting, setClaimSubmitting] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [scoreHistory, setScoreHistory] = useState<Record<number, number[]>>({})
  const [showAllIncoming, setShowAllIncoming] = useState(false)
  const [lastRefreshAt, setLastRefreshAt] = useState<Date | null>(null)
  const [endGameResult, setEndGameResult] = useState<any>(null)  // P12 end-game modal

  const showEndGame = async (bid: string) => {
    try {
      const r = await api(`/api/battles/${bid}/auto/finalize`)
      setEndGameResult(r)
    } catch (e: any) { alert(e.message) }
  }
  const [activeTeam, setActiveTeam] = useState<'red' | 'blue'>('red')
  const pollRef = useRef<any>(null)

  // 로비 데이터 로드
  const loadLobby = async () => {
    try {
      const [b, s, vs] = await Promise.all([
        api('/api/battles').then(d => d.battles || []),
        api('/api/battles/scenarios').then(d => d.scenarios || []),
        api('/api/vuln-sites/list').then(d => d.sites || []).catch(() => []),
      ])
      setBattles(b)
      setScenarios(s)
      setVulnSites(vs)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { loadLobby() }, [])

  // 대전 개설
  const createBattle = async (scenarioId: string, autonomous: boolean = false,
                                vulnSiteId: string = '', difficulty: string = 'normal') => {
    try {
      const body: any = { scenario_id: scenarioId }
      if (autonomous) { body.battle_type = 'autonomous'; body.max_teams = 8 }
      if (vulnSiteId) { body.vuln_site_id = vulnSiteId; body.difficulty = difficulty }
      await api('/api/battles/create', { method: 'POST', body: JSON.stringify(body) })
      loadLobby()
    } catch (e: any) { alert(e.message) }
  }
  // 시나리오 카드별 선택 상태 (어떤 site/difficulty 로 개설할지)
  const [siteSel, setSiteSel] = useState<Record<string, { site: string; diff: string }>>({})
  const setSel = (sid: string, k: 'site' | 'diff', v: string) =>
    setSiteSel(prev => ({ ...prev, [sid]: { ...(prev[sid] || { site: '', diff: 'normal' }), [k]: v } }))

  // 자율 공방전 — 역할 없이 자동 team 할당
  const autoJoin = async (bid: string) => {
    try {
      const infras = await api(`/api/infras?student_id=${user?.id}`).then(d => d.infras || []).catch(() => [])
      const attackerIp = infras.find((i: any) => i.role === 'attacker')?.ip || ''
      const defenseIps = infras.filter((i: any) => i.role !== 'attacker').map((i: any) => i.ip)
      await api(`/api/battles/${bid}/auto/join`, {
        method: 'POST',
        body: JSON.stringify({ attacker_ip: attackerIp, defense_ips: defenseIps }),
      })
      loadLobby()
    } catch (e: any) { alert(e.message) }
  }

  const enterAutoBattle = async (bid: string) => {
    try {
      const [parts, targets, defense, board, miss] = await Promise.all([
        api(`/api/battles/${bid}/auto/participants`).then(d => d.participants || []),
        api(`/api/battles/${bid}/auto/my-targets`).catch(() => ({ targets: [] })),
        api(`/api/battles/${bid}/auto/my-defense`).catch(() => ({})),
        api(`/api/battles/${bid}/auto/scoreboard`).catch(() => ({ scoreboard: [] })),
        api(`/api/battles/${bid}/auto/my-missions`).catch(() => ({ missions: { red: [], blue: [] }, summary: {} })),
      ])
      setActiveBattle(bid)
      setView('battle')
      setBattleInfo({ ...board, ...defense, autonomous: true, participants: parts, targets: targets.targets || [], missions: miss.missions, mission_summary: miss.summary })
      // poll — autoRefresh ON 일 때만
      if (pollRef.current) clearInterval(pollRef.current)
      pollRef.current = setInterval(async () => {
        if (!autoRefresh) return  // toggle OFF 시 skip
        try {
          const board = await api(`/api/battles/${bid}/auto/scoreboard`).catch(() => null)
          const def = await api(`/api/battles/${bid}/auto/my-defense`).catch(() => null)
          if (board) {
            setBattleInfo((prev: any) => ({ ...prev, ...board, ...def, autonomous: true }))
            // score history 누적 (최근 30 포인트만)
            setScoreHistory(prev => {
              const next = { ...prev }
              for (const r of (board.scoreboard || [])) {
                const arr = next[r.team_no] || []
                arr.push(r.score)
                next[r.team_no] = arr.slice(-30)
              }
              return next
            })
            setLastRefreshAt(new Date())
          }
        } catch {}
      }, 5000)
    } catch (e: any) { alert(e.message) }
  }

  const submitAutoClaim = async (bid: string, claim_type: string, target_team_no: number | null,
                                   source_team_no: number | null, title: string, evidence: string) => {
    setClaimSubmitting(true)
    try {
      const r = await api(`/api/battles/${bid}/auto/claim`, {
        method: 'POST',
        body: JSON.stringify({ claim_type, target_team_no, source_team_no, title, evidence }),
      })
      alert(`${r.accepted ? '✅ 인정' : '❌ 미인정'} +${r.points_awarded}점\n${r.reason}`)
      enterAutoBattle(bid)
    } catch (e: any) { alert(e.message) }
    finally { setClaimSubmitting(false) }
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

  // 참가 취소
  const leaveBattle = async (bid: string) => {
    try {
      await api(`/api/battles/${bid}/leave`, { method: 'POST' })
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
  const enterBattle = async (bid: string, team?: 'red' | 'blue') => {
    try {
      const q = team ? `?team=${team}` : ''
      const d = await api(`/api/battles/${bid}/my-missions${q}`)
      setBattleInfo(d)
      setMissions(d.missions || [])
      setActiveTeam(d.team as 'red' | 'blue')
      setActiveBattle(bid)
      setView('battle')
      startPolling(bid, d.team)
    } catch (e: any) { alert(e.message) }
  }

  // solo 모드에서 red ↔ blue 시점 전환
  const switchTeam = async (team: 'red' | 'blue') => {
    if (!activeBattle) return
    setActiveTeam(team)
    try {
      const info = await api(`/api/battles/${activeBattle}/my-missions?team=${team}`)
      setBattleInfo(info)
      setMissions(info.missions || [])
      startPolling(activeBattle, team)
    } catch {}
  }

  // 미션 제출
  const submitMission = async (order: number) => {
    if (!activeBattle || !answers[order]) return
    try {
      await api(`/api/battles/${activeBattle}/submit-mission`, {
        method: 'POST',
        body: JSON.stringify({ mission_order: order, answer: answers[order], team: activeTeam }),
      })
      const info = await api(`/api/battles/${activeBattle}/my-missions?team=${activeTeam}`)
      setBattleInfo(info)
      setMissions(info.missions || [])
    } catch (e: any) { alert(e.message) }
  }

  // 이벤트 폴링
  const startPolling = (bid: string, team?: string) => {
    if (pollRef.current) clearInterval(pollRef.current)
    const q = team ? `?team=${team}` : ''
    pollRef.current = setInterval(async () => {
      try {
        const [info, evts] = await Promise.all([
          api(`/api/battles/${bid}/my-missions${q}`),
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
  if (view === 'battle' && battleInfo?.autonomous) {
    // 자율 공방전 view
    const board = battleInfo.scoreboard || []
    const myTeam = board.find((r: any) => r.user_id === user?.id)
    const targets = battleInfo.targets || []
    const incoming = battleInfo.incoming_claims || []
    const submitMission = async (role: string, order: number) => {
      const ans = prompt(`[${role}] 미션 #${order} 답변 입력 (명령+stdout)`)
      if (!ans) return
      try {
        const r = await api(`/api/battles/${activeBattle}/auto/submit-mission`, {
          method: 'POST', body: JSON.stringify({ role, mission_order: order, answer: ans }),
        })
        alert(`${r.passed ? '✅' : '❌'} +${r.points || 0}점\n${r.message}`)
        enterAutoBattle(activeBattle!)
      } catch (e: any) { alert(e.message) }
    }
    const renderMissions = (role: string) => {
      const list = (battleInfo.missions || {})[role] || []
      const color = role === 'red' ? '#f85149' : '#58a6ff'
      return (
        <div style={{ background: '#161b22', border: `1px solid ${color}`, borderRadius: 8, padding: 14 }}>
          <h3 style={{ fontSize: 14, marginBottom: 10, color }}>📋 {role.toUpperCase()} 미션 ({list.filter((m:any)=>m.status==='completed').length}/{list.length})</h3>
          <div style={{ maxHeight: 280, overflowY: 'auto' as const }}>
            {list.map((m: any) => (
              <div key={m.id} style={{ padding: '6px 0', borderBottom: '1px solid #21262d', fontSize: 12 }}>
                <span style={{ color: m.status === 'completed' ? '#3fb950' : '#8b949e' }}>{m.status === 'completed' ? '✓' : '○'}</span>{' '}
                <b>#{m.mission_order}</b> ({m.points}pt) {m.instruction?.slice(0, 80)}
                {m.status !== 'completed' && (
                  <button onClick={() => submitMission(role, m.mission_order)} style={{ ...joinBtn, fontSize: 10, padding: '2px 8px', marginLeft: 6, color, borderColor: color }}>제출</button>
                )}
              </div>
            ))}
          </div>
        </div>
      )
    }
    // mini sparkline SVG (40×16, 30 포인트 max)
    const sparkline = (vals: number[], color = '#3fb950') => {
      if (!vals || vals.length < 2) return null
      const w = 50, h = 16
      const max = Math.max(...vals, 1)
      const min = Math.min(...vals, 0)
      const range = Math.max(max - min, 1)
      const pts = vals.map((v, i) => `${(i / (vals.length - 1)) * w},${h - ((v - min) / range) * h}`).join(' ')
      return <svg width={w} height={h} style={{ display: 'inline-block', verticalAlign: 'middle', marginLeft: 6 }}>
        <polyline points={pts} stroke={color} strokeWidth="1.5" fill="none"/>
      </svg>
    }
    const medal = (i: number) => i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i+1}`

    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, background: '#161b22', borderRadius: 10, padding: '16px 24px', border: '1px solid #bc8cff' }}>
          <button onClick={backToLobby} style={backBtn}>Lobby</button>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#bc8cff' }}>AUTONOMOUS · {board.length} 팀 · {battleInfo.total_claims || 0} claims</div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', fontSize: 13, color: '#e6edf3' }}>
            <span>나: <b style={{ color: '#bc8cff' }}>team-{myTeam?.team_no || '-'}</b> · 점수 <b style={{ color: '#3fb950' }}>{myTeam?.score || 0}</b></span>
            <span>미션 {(battleInfo.mission_summary?.red_done || 0) + (battleInfo.mission_summary?.blue_done || 0)}/{(battleInfo.mission_summary?.red_total || 0) + (battleInfo.mission_summary?.blue_total || 0)}</span>
            <button onClick={() => setAutoRefresh(s => !s)} style={{ ...joinBtn, fontSize: 11, padding: '4px 10px', color: autoRefresh ? '#3fb950' : '#8b949e', borderColor: autoRefresh ? '#3fb950' : '#30363d' }}>
              {autoRefresh ? '🔄 LIVE 5s' : '⏸ 정지'}
            </button>
            <button onClick={() => showEndGame(activeBattle!)} style={{ ...joinBtn, fontSize: 11, padding: '4px 10px', color: '#f9d71c', borderColor: '#f9d71c' }}>
              🏁 End-game 결과
            </button>
            {lastRefreshAt && <span style={{ fontSize: 10, color: '#8b949e' }}>last {Math.floor((Date.now() - lastRefreshAt.getTime())/1000)}s ago</span>}
          </div>
        </div>
        {/* End-game modal */}
        {endGameResult && (
          <div onClick={() => setEndGameResult(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div onClick={e => e.stopPropagation()} style={{ background: '#0d1117', border: '2px solid #f9d71c', borderRadius: 12, padding: 32, maxWidth: 700, maxHeight: '85vh', overflowY: 'auto', boxShadow: '0 8px 32px rgba(0,0,0,0.6)' }}>
              <h2 style={{ fontSize: 24, color: '#f9d71c', textAlign: 'center', marginTop: 0 }}>🏁 BATTLE END</h2>
              {endGameResult.winner && (
                <div style={{ textAlign: 'center', padding: '12px 0', background: '#161b22', borderRadius: 8, marginBottom: 16 }}>
                  <div style={{ fontSize: 14, color: '#8b949e' }}>🥇 Winner</div>
                  <div style={{ fontSize: 28, fontWeight: 700, color: '#f9d71c' }}>team-{endGameResult.winner.team_no}</div>
                  <div style={{ fontSize: 13, color: '#cfd5dd' }}>{endGameResult.winner.name} · <b style={{ color: '#3fb950' }}>{endGameResult.winner.score}점</b></div>
                  {endGameResult.runner_up && (
                    <div style={{ fontSize: 12, color: '#8b949e', marginTop: 6 }}>🥈 team-{endGameResult.runner_up.team_no} ({endGameResult.runner_up.name}, {endGameResult.runner_up.score}점)</div>
                  )}
                </div>
              )}
              {endGameResult.stats && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 16 }}>
                  {Object.entries(endGameResult.stats).map(([k, v]) => (
                    <div key={k} style={{ background: '#161b22', padding: 10, borderRadius: 6, textAlign: 'center' }}>
                      <div style={{ fontSize: 10, color: '#8b949e' }}>{k.replace(/_/g, ' ')}</div>
                      <div style={{ fontSize: 16, fontWeight: 700, color: '#e6edf3' }}>{String(v)}</div>
                    </div>
                  ))}
                </div>
              )}
              <h3 style={{ color: '#bc8cff', fontSize: 14 }}>📜 Timeline (최근 30 claim)</h3>
              <div style={{ maxHeight: 250, overflowY: 'auto', background: '#161b22', padding: 8, borderRadius: 6, fontSize: 11 }}>
                {(endGameResult.timeline || []).map((t: any, i: number) => (
                  <div key={i} style={{ padding: '3px 0', borderBottom: '1px solid #21262d', color: '#cfd5dd' }}>
                    <span style={{ color: '#8b949e' }}>{t.ts.slice(11, 19)}</span>{' '}
                    <span style={{ color: t.type === 'attack' ? '#f85149' : '#58a6ff' }}>{t.type === 'attack' ? '⚔️' : '🛡️'}</span>{' '}
                    <b>{t.claimant}</b> — {t.title} <span style={{ color: t.accepted ? '#3fb950' : '#8b949e' }}>{t.accepted ? `+${t.points}` : '✗'}</span>
                  </div>
                ))}
              </div>
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <button onClick={() => setEndGameResult(null)} style={joinBtn}>닫기</button>
              </div>
            </div>
          </div>
        )}
        {/* 미션 (시나리오 RED+BLUE) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          {renderMissions('red')}
          {renderMissions('blue')}
        </div>
        {/* 자유 공방 (claim) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
          <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 14 }}>
            <h3 style={{ fontSize: 15, marginBottom: 10, color: '#e6edf3' }}>🏆 Scoreboard</h3>
            {board.map((r: any, i: number) => {
              const isMe = r.user_id === user?.id
              const hist = scoreHistory[r.team_no] || []
              return (
                <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #21262d', fontSize: 13, background: isMe ? '#21262d' : 'transparent', borderRadius: isMe ? 4 : 0 }}>
                  <span>
                    <b style={{ color: i < 3 ? '#f9d71c' : '#8b949e' }}>{medal(i)}</b>{' '}
                    team-{r.team_no} · {r.user_name || r.user_id?.slice(0,8)}{isMe ? ' (나)' : ''}
                  </span>
                  <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                    {sparkline(hist, i === 0 ? '#f9d71c' : '#3fb950')}
                    <b style={{ color: '#3fb950', marginLeft: 8 }}>{r.score}점</b>
                  </span>
                </div>
              )
            })}
          </div>
          <div style={{ background: '#161b22', border: '1px solid #f85149', borderRadius: 8, padding: 14 }}>
            <h3 style={{ fontSize: 15, marginBottom: 10, color: '#f85149' }}>⚔️ My Targets ({targets.length})</h3>
            {targets.map((t: any) => (
              <div key={t.team_no} style={{ padding: '6px 0', borderBottom: '1px solid #21262d', fontSize: 13 }}>
                <div><b>team-{t.team_no}</b> (점수 {t.current_score})</div>
                <div style={{ fontSize: 11, color: '#8b949e' }}>defense: {(t.defense_ips || []).join(', ') || '-'}</div>
                <button disabled={claimSubmitting} onClick={() => {
                  const title = prompt('공격 제목 (예: SQLi token exfil)') || ''
                  if (!title) return
                  const ev = prompt('Evidence — 명령 + stdout + 결과')
                  if (!ev) return
                  submitAutoClaim(activeBattle!, 'attack', t.team_no, null, title, ev)
                }} style={{ ...joinBtn, color: '#f85149', borderColor: '#f85149', fontSize: 11, padding: '4px 10px', marginTop: 4, opacity: claimSubmitting ? 0.5 : 1 }}>{claimSubmitting ? '⏳ LLM 채점중...' : '공격 claim 제출'}</button>
              </div>
            ))}
          </div>
          <div style={{ background: '#161b22', border: '1px solid #58a6ff', borderRadius: 8, padding: 14 }}>
            <h3 style={{ fontSize: 15, marginBottom: 10, color: '#58a6ff' }}>🛡️ My Defense</h3>
            <div style={{ fontSize: 12, color: '#8b949e', marginBottom: 8 }}>
              IPs: {(battleInfo.defense_ips || []).join(', ') || '-'}<br/>
              차단 {myTeam?.defenses_blocked || 0} · 침해당함 {myTeam?.own_breaches || 0}
            </div>
            <div style={{ fontSize: 11, color: '#8b949e', marginBottom: 4, display: 'flex', justifyContent: 'space-between' }}>
              <span>Incoming attacks ({incoming.length})</span>
              {incoming.length > 10 && (
                <button onClick={() => setShowAllIncoming(s => !s)} style={{ background: 'none', border: 'none', color: '#58a6ff', fontSize: 10, cursor: 'pointer' }}>
                  {showAllIncoming ? '간략히' : '전체 보기'}
                </button>
              )}
            </div>
            {(showAllIncoming ? incoming : incoming.slice(0, 10)).map((c: any) => (
              <div key={c.id} style={{ padding: '4px 0', borderBottom: '1px solid #21262d', fontSize: 12 }}>
                <span style={{ color: c.accepted ? '#f85149' : '#8b949e' }}>{c.accepted ? '⚠️' : '○'}</span>{' '}
                from team-{c.source_team_no || '?'} · {c.title?.slice(0, 40)}
                {c.points_awarded ? <b style={{ color: '#f85149', marginLeft: 6 }}>+{c.points_awarded}</b> : null}
              </div>
            ))}
            <button disabled={claimSubmitting} onClick={() => {
              const src = parseInt(prompt('차단한 공격의 출처 team_no') || '0')
              if (!src) return
              const title = prompt('차단 제목') || '방어 차단'
              const ev = prompt('Evidence — 적용 룰/명령 + 차단 로그')
              if (!ev) return
              submitAutoClaim(activeBattle!, 'defense', null, src, title, ev)
            }} style={{ ...joinBtn, color: '#58a6ff', borderColor: '#58a6ff', fontSize: 11, padding: '4px 10px', marginTop: 8, opacity: claimSubmitting ? 0.5 : 1 }}>{claimSubmitting ? '⏳ LLM 채점중...' : '방어 claim 제출'}</button>
          </div>
        </div>
      </div>
    )
  }
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
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {battleInfo.is_solo && (
              <div style={{ display: 'flex', gap: 4, background: '#0d1117', padding: 3, borderRadius: 8, border: '1px solid #30363d' }}>
                <button onClick={() => switchTeam('red')} style={{
                  padding: '4px 10px', borderRadius: 5, border: 'none', cursor: 'pointer',
                  fontSize: 12, fontWeight: 700,
                  background: activeTeam === 'red' ? '#f85149' : 'transparent',
                  color: activeTeam === 'red' ? '#fff' : '#f85149',
                }}>RED</button>
                <button onClick={() => switchTeam('blue')} style={{
                  padding: '4px 10px', borderRadius: 5, border: 'none', cursor: 'pointer',
                  fontSize: 12, fontWeight: 700,
                  background: activeTeam === 'blue' ? '#58a6ff' : 'transparent',
                  color: activeTeam === 'blue' ? '#fff' : '#58a6ff',
                }}>BLUE</button>
              </div>
            )}
            <div style={{ fontSize: 14, padding: '6px 14px', borderRadius: 8, background: isRed ? '#f8514922' : '#58a6ff22', color: isRed ? '#f85149' : '#58a6ff', fontWeight: 700 }}>
              {battleInfo.is_solo ? 'SOLO' : 'You'}: {battleInfo.team.toUpperCase()}
            </div>
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
                <div style={{ fontSize: 15, color: '#e6edf3', marginBottom: 8, lineHeight: 1.5, whiteSpace: 'pre-wrap' as const }}>{m.instruction}</div>
                {m.hint && <div style={{ fontSize: 13, color: '#58a6ff', background: '#0d1f3c', borderRadius: 6, padding: '6px 10px', marginBottom: 8, whiteSpace: 'pre-wrap' as const }}>Hint: {m.hint}</div>}
                {isAdmin() && m.verify && (
                  <div style={{ background: '#1a0a0a', border: '1px solid #f8514966', borderRadius: 6, padding: '8px 12px', marginBottom: 8 }}>
                    <div style={{ fontSize: 12, color: '#f85149', fontWeight: 700, marginBottom: 4 }}>채점 기준 (Admin)</div>
                    <div style={{ fontSize: 13, color: '#8b949e' }}>type: <code style={{ color: '#d29922' }}>{m.verify.type}</code></div>
                    {m.verify.expect && <div style={{ fontSize: 13, color: '#8b949e' }}>expect: <code style={{ color: '#bc8cff' }}>"{m.verify.expect}"</code></div>}
                  </div>
                )}
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
                    {isAdmin() && (() => {
                      const sel = siteSel[s.id] || { site: '', diff: 'normal' }
                      const availSites = vulnSites.filter((v: any) => v.status === 'available')
                      const selSite = vulnSites.find((v: any) => v.id === sel.site)
                      const selModes = (selSite?.modes || []).filter((m: any) => m.available)
                      return (
                        <div style={{ display: 'flex', flexDirection: 'column' as const, gap: 4, minWidth: 200 }}>
                          <select value={sel.site} onChange={e => setSel(s.id, 'site', e.target.value)}
                            style={{ background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d', borderRadius: 4, padding: '4px 6px', fontSize: 11 }}>
                            <option value=''>(VulnSite 미선택 — 시나리오 default)</option>
                            {availSites.map((v: any) => (
                              <option key={v.id} value={v.id}>{v.name} · {v.theme}</option>
                            ))}
                          </select>
                          <select value={sel.diff} onChange={e => setSel(s.id, 'diff', e.target.value)} disabled={!sel.site}
                            style={{ background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d', borderRadius: 4, padding: '4px 6px', fontSize: 11 }}>
                            {selModes.length > 0 ? selModes.map((m: any) => (
                              <option key={m.difficulty} value={m.difficulty}>{m.difficulty} · {m.vuln_count}취약점</option>
                            )) : <option value='normal'>normal (default)</option>}
                          </select>
                          <button onClick={() => createBattle(s.id, false, sel.site, sel.diff)} style={{
                            padding: '6px 14px', borderRadius: 6, border: 'none', whiteSpace: 'nowrap' as const,
                            background: '#f97316', color: '#fff', cursor: 'pointer', fontSize: 12, fontWeight: 600,
                          }}>1v1 개설</button>
                          <button onClick={() => createBattle(s.id, true, sel.site, sel.diff)} style={{
                            padding: '6px 14px', borderRadius: 6, border: '1px solid #bc8cff', whiteSpace: 'nowrap' as const,
                            background: '#bc8cff22', color: '#bc8cff', cursor: 'pointer', fontSize: 12, fontWeight: 600,
                          }}>자율 (max 8팀)</button>
                        </div>
                      )
                    })()}
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
            const isAuto = b.battle_type === 'autonomous'
            const amRed = b.red_id === user?.id
            const amBlue = b.blue_id === user?.id
            const amIn = amRed || amBlue
            if (isAuto) {
              return (
                <div key={b.id} style={{ background: '#161b22', border: '1px solid #bc8cff', borderRadius: 8, padding: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3', marginBottom: 4 }}>
                      <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 10, background: '#bc8cff22', color: '#bc8cff', fontWeight: 700, marginRight: 8 }}>AUTO</span>
                      {b.scenario_id}
                    </div>
                    <div style={{ fontSize: 13, color: '#8b949e' }}>
                      max teams: {b.rules?.max_teams || '-'} · {Math.floor(b.time_limit / 60)}분
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button onClick={() => autoJoin(b.id)} style={{ ...joinBtn, color: '#bc8cff', borderColor: '#bc8cff' }}>자율 참가</button>
                    <button onClick={() => enterAutoBattle(b.id)} style={{ ...joinBtn, background: '#238636', color: '#fff', border: 'none' }}>입장</button>
                  </div>
                </div>
              )
            }
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
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  {amRed && amBlue && <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 10, background: '#bc8cff22', color: '#bc8cff', fontWeight: 700 }}>SOLO</span>}
                  {!b.red_id && !amRed && <button onClick={() => joinBattle(b.id, 'red')} style={{ ...joinBtn, color: '#f85149', borderColor: '#f85149' }}>Red 참가</button>}
                  {!b.blue_id && !amBlue && <button onClick={() => joinBattle(b.id, 'blue')} style={{ ...joinBtn, color: '#58a6ff', borderColor: '#58a6ff' }}>Blue 참가</button>}
                  {amIn && <>
                    <button onClick={() => readyAndEnter(b.id)} style={{ ...joinBtn, background: '#f97316', color: '#fff', border: 'none' }}>Ready &amp; Enter</button>
                    <button onClick={() => leaveBattle(b.id)} style={{ ...joinBtn, color: '#8b949e', borderColor: '#30363d' }}>취소</button>
                  </>}
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

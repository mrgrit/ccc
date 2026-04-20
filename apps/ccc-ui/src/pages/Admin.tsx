import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

const tabs = ['Groups', 'Students', 'Promotions', 'Lab Verify', 'Auto-Generated', 'News & Issue'] as const
type Tab = typeof tabs[number]

export default function Admin() {
  const [tab, setTab] = useState<Tab>('Groups')
  const [groups, setGroups] = useState<any[]>([])
  const [students, setStudents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const loadGroups = () => api('/api/groups').then(d => setGroups(d.groups || []))
  const loadStudents = () => api('/api/students').then(d => setStudents(d.students || []))
  const load = () => {
    setLoading(true)
    Promise.all([loadGroups(), loadStudents()]).finally(() => setLoading(false))
  }
  useEffect(load, [])

  // Group creation
  const [newGroup, setNewGroup] = useState({ name: '', display_name: '', description: '' })
  const createGroup = async () => {
    if (!newGroup.name) return
    await api('/api/groups', { method: 'POST', body: JSON.stringify(newGroup) })
    setNewGroup({ name: '', display_name: '', description: '' })
    loadGroups()
  }

  // Assign student to group
  const assignGroup = async (studentId: string, groupId: string) => {
    await api('/api/groups/assign', { method: 'POST', body: JSON.stringify({ student_id: studentId, group_id: groupId || null }) })
    loadStudents()
  }

  // Promotion
  const [rankCheck, setRankCheck] = useState<Record<string, any>>({})
  const checkRank = async (studentId: string) => {
    const d = await api(`/api/rank/check/${studentId}`)
    setRankCheck(prev => ({ ...prev, [studentId]: d }))
  }
  const promote = async (studentId: string) => {
    await api(`/api/rank/promote/${studentId}`, { method: 'POST' })
    setRankCheck(prev => ({ ...prev, [studentId]: null }))
    loadStudents()
  }

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#e6edf3' }}>Admin</h2>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24 }}>
        {tabs.map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '8px 20px', borderRadius: 6, border: 'none', cursor: 'pointer',
            background: tab === t ? '#f97316' : '#21262d', color: tab === t ? '#fff' : '#8b949e',
            fontSize: 14, fontWeight: 600,
          }}>{t}</button>
        ))}
      </div>

      {/* Groups Tab */}
      {tab === 'Groups' && (
        <div>
          <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 20, marginBottom: 20 }}>
            <h3 style={{ fontSize: 16, color: '#e6edf3', marginBottom: 12 }}>Create Group</h3>
            <div style={{ display: 'flex', gap: 8 }}>
              <input placeholder="ID (slug)" value={newGroup.name} onChange={e => setNewGroup({ ...newGroup, name: e.target.value })} style={inputStyle} />
              <input placeholder="Display Name" value={newGroup.display_name} onChange={e => setNewGroup({ ...newGroup, display_name: e.target.value })} style={inputStyle} />
              <input placeholder="Description" value={newGroup.description} onChange={e => setNewGroup({ ...newGroup, description: e.target.value })} style={{ ...inputStyle, flex: 2 }} />
              <button onClick={createGroup} style={btnStyle}>Create</button>
            </div>
          </div>
          <div style={{ display: 'grid', gap: 12 }}>
            {groups.map(g => (
              <div key={g.id} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3' }}>{g.display_name || g.name}</div>
                  <div style={{ fontSize: 13, color: '#8b949e' }}>{g.description} | Members: {g.member_count || 0}</div>
                </div>
                <div style={{ fontSize: 12, color: '#58a6ff' }}>
                  {(g.courses || []).length > 0 ? `${g.courses.length} courses` : 'All courses'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Students Tab */}
      {tab === 'Students' && (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr style={{ borderBottom: '1px solid #30363d' }}>
              {['Name', 'ID', 'Role', 'Rank', 'Blocks', 'Group', ''].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '10px 14px', fontSize: 12, color: '#8b949e' }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {students.map(s => (
                <tr key={s.id} style={{ borderBottom: '1px solid #21262d' }}>
                  <td style={{ padding: '10px 14px', color: '#e6edf3', fontWeight: 600 }}>{s.name}</td>
                  <td style={{ padding: '10px 14px', fontSize: 13, color: '#8b949e' }}>{s.student_id}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 10, background: s.role === 'admin' ? '#f9731615' : '#21262d', color: s.role === 'admin' ? '#f97316' : '#8b949e', fontWeight: 600 }}>{s.role}</span>
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 10, background: '#58a6ff15', color: '#58a6ff', fontWeight: 600, textTransform: 'uppercase' as const }}>{s.rank || 'rookie'}</span>
                  </td>
                  <td style={{ padding: '10px 14px', color: '#3fb950', fontWeight: 600 }}>{s.total_blocks || 0}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <select value={s.group_id || ''} onChange={e => assignGroup(s.id, e.target.value)}
                      style={{ background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d', borderRadius: 4, padding: '4px 8px', fontSize: 12 }}>
                      <option value="">No Group</option>
                      {groups.map(g => <option key={g.id} value={g.id}>{g.display_name || g.name}</option>)}
                    </select>
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <button onClick={() => checkRank(s.id)} style={{ ...smallBtn, fontSize: 11 }}>Check</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Promotions Tab */}
      {tab === 'Promotions' && (
        <div style={{ display: 'grid', gap: 12 }}>
          {students.filter(s => s.role !== 'admin').map(s => {
            const rc = rankCheck[s.id]
            return (
              <div key={s.id} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <div>
                    <span style={{ fontSize: 15, fontWeight: 600, color: '#e6edf3' }}>{s.name}</span>
                    <span style={{ fontSize: 12, color: '#58a6ff', marginLeft: 8, textTransform: 'uppercase' as const }}>{s.rank || 'rookie'}</span>
                    <span style={{ fontSize: 12, color: '#3fb950', marginLeft: 8 }}>{s.total_blocks || 0} blocks</span>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={() => checkRank(s.id)} style={smallBtn}>Check Rank</button>
                    {rc?.can_promote && (
                      <button onClick={() => promote(s.id)} style={{ ...smallBtn, background: '#f97316', color: '#fff' }}>
                        Promote to {rc.next_rank}
                      </button>
                    )}
                  </div>
                </div>
                {rc && (
                  <div style={{ fontSize: 12, color: '#8b949e', marginTop: 4 }}>
                    {rc.can_promote
                      ? <span style={{ color: '#3fb950' }}>Ready to promote to {rc.next_rank}</span>
                      : rc.next_rank === null
                        ? <span>Max rank reached</span>
                        : <span>Next: {rc.next_rank} | Met: {JSON.stringify(rc.met)}</span>
                    }
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Lab Verify Tab */}
      {tab === 'Lab Verify' && <LabVerifyPanel />}

      {/* Auto-Generated Tab */}
      {tab === 'Auto-Generated' && <AutoGeneratedPanel />}

      {/* News & Issue Tab */}
      {tab === 'News & Issue' && <NewsIssuePanel />}
    </div>
  )
}

function NewsIssuePanel() {
  const [news, setNews] = useState<any[]>([])
  const [features, setFeatures] = useState<any[]>([])
  const [filter, setFilter] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<any>(null)

  const load = () => {
    setLoading(true)
    const q = filter ? `?category=${filter}` : ''
    Promise.all([
      api('/api/news/recent' + q + (filter?'&':'?') + 'limit=50').catch(() => []),
      api('/api/trending/features').catch(() => []),
    ]).then(([n, f]) => {
      setNews(Array.isArray(n) ? n : [])
      setFeatures(Array.isArray(f) ? f : [])
    }).finally(() => setLoading(false))
  }
  useEffect(load, [filter])

  const catColor: Record<string, string> = {
    ai_agent_attack: '#f85149',
    ai_under_attack: '#f97316',
    attack_technique: '#d29922',
    general: '#8b949e',
  }
  const catLabel: Record<string, string> = {
    ai_agent_attack: '🤖 AI 에이전트 공격',
    ai_under_attack: '🎯 AI 피격',
    attack_technique: '⚠️ 공격 기법',
    general: '📰 일반',
  }

  if (loading) return <div style={{color:'#8b949e', padding:20}}>Loading news…</div>

  return (
    <div>
      {/* 특집 (trending) */}
      {features.length > 0 && (
        <div style={{marginBottom:24}}>
          <h3 style={{fontSize:17, color:'#e6edf3', marginBottom:12}}>🔥 특집 (지속 화제 토픽)</h3>
          <div style={{display:'grid', gap:8}}>
            {features.map((f, i) => (
              <div key={i} style={{background:'#161b22', border:'1px solid #f97316', borderRadius:8, padding:'12px 16px', cursor:'pointer'}}
                onClick={async () => {
                  const d = await api(`/api/trending/features/${encodeURIComponent(f.topic)}`)
                  setSelected({type:'feature', ...d})
                }}>
                <div style={{display:'flex', gap:10, alignItems:'center'}}>
                  <strong style={{color:'#f97316'}}>{f.topic}</strong>
                  <span style={{fontSize:12, color:'#8b949e'}}>
                    {f.article_count}건 · {f.day_span}일 ({f.first_seen} ~ {f.last_seen})
                  </span>
                  <span style={{marginLeft:'auto', fontSize:11, color:'#58a6ff'}}>avg priority {f.avg_priority}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 필터 */}
      <div style={{display:'flex', gap:8, marginBottom:16, flexWrap:'wrap'}}>
        {['', 'ai_agent_attack', 'ai_under_attack', 'attack_technique', 'general'].map(c => (
          <button key={c || 'all'} onClick={() => setFilter(c)} style={{
            padding:'6px 12px', borderRadius:6, border:'1px solid #30363d',
            background: filter === c ? '#f97316' : '#21262d',
            color: filter === c ? '#fff' : '#8b949e', cursor:'pointer', fontSize:12,
          }}>
            {c ? catLabel[c] : '전체'} {c && `(${news.filter(n => n.category === c).length})`}
          </button>
        ))}
        <button onClick={load} style={smallBtn}>🔄 새로고침</button>
      </div>

      {/* 뉴스 리스트 */}
      <div style={{display:'grid', gap:8}}>
        {news.map((n, i) => (
          <div key={i} style={{
            background:'#0d1117', border:'1px solid #21262d',
            borderLeft:`3px solid ${catColor[n.category] || '#8b949e'}`,
            borderRadius:6, padding:'12px 16px',
          }}>
            <div style={{display:'flex', gap:10, alignItems:'center', marginBottom:6, flexWrap:'wrap'}}>
              <span style={{fontSize:11, color:catColor[n.category], fontWeight:600}}>
                {catLabel[n.category] || '?'}
              </span>
              <span style={{fontSize:11, color:'#8b949e'}}>[{n.source}]</span>
              <span style={{fontSize:11, color:'#58a6ff'}}>priority {n.priority}</span>
              {n.severity && <span style={{fontSize:10, padding:'1px 6px', borderRadius:3, background:'#21262d', color:'#f97316'}}>{n.severity}</span>}
              <span style={{marginLeft:'auto', fontSize:11, color:'#8b949e'}}>{(n.published || '').slice(0,10)}</span>
            </div>
            <div style={{fontSize:14, color:'#e6edf3', marginBottom:4, fontWeight:600}}>
              <a href={n.link} target="_blank" rel="noreferrer" style={{color:'#e6edf3', textDecoration:'none'}}>{n.title}</a>
            </div>
            {n.summary && <div style={{fontSize:12, color:'#8b949e', marginBottom:4, lineHeight:1.5}}>{n.summary}</div>}
            {n.tags?.length > 0 && (
              <div style={{fontSize:10, color:'#8b949e'}}>
                {n.tags.slice(0,5).map((t:string, j:number) => (
                  <span key={j} style={{marginRight:8}}>#{t}</span>
                ))}
              </div>
            )}
            {n.has_deep && (
              <div style={{marginTop:4, fontSize:11, color:'#3fb950'}}>📖 상세 분석 있음</div>
            )}
          </div>
        ))}
      </div>

      {/* 특집 상세 모달 */}
      {selected?.type === 'feature' && (
        <div onClick={() => setSelected(null)} style={{
          position:'fixed', inset:0, background:'rgba(0,0,0,0.8)', zIndex:100,
          display:'flex', justifyContent:'center', alignItems:'center', padding:20,
        }}>
          <div onClick={e => e.stopPropagation()} style={{
            background:'#0d1117', border:'1px solid #f97316', borderRadius:10,
            maxWidth:900, maxHeight:'85vh', overflow:'auto', padding:24,
          }}>
            <div style={{display:'flex', gap:10, marginBottom:16}}>
              <h2 style={{margin:0, color:'#f97316'}}>🔥 특집: {selected.topic}</h2>
              <button onClick={() => setSelected(null)} style={{marginLeft:'auto', ...smallBtn}}>✕</button>
            </div>
            <pre style={{color:'#e6edf3', fontSize:13, lineHeight:1.6, whiteSpace:'pre-wrap', fontFamily:'inherit'}}>{selected.content}</pre>
            {selected.sources?.length > 0 && (
              <div style={{marginTop:20, paddingTop:16, borderTop:'1px solid #30363d'}}>
                <h4 style={{color:'#8b949e'}}>출처 ({selected.sources.length})</h4>
                {selected.sources.slice(0,10).map((s:any, j:number) => (
                  <div key={j} style={{fontSize:12, marginBottom:4}}>
                    <a href={s.link} target="_blank" rel="noreferrer" style={{color:'#58a6ff'}}>
                      [{s._day || '?'}] {s.title}
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function AutoGeneratedPanel() {
  const [data, setData] = useState<{threats: any[], battles: any[], rules: any[]}>({threats:[], battles:[], rules:[]})
  const [loading, setLoading] = useState(true)
  const [section, setSection] = useState<'threats'|'battles'|'rules'>('threats')

  const load = () => {
    setLoading(true)
    api('/api/admin/auto-content').then(setData).catch(() => {}).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const setStatus = async (key: string, action: 'approve'|'reject'|'pending') => {
    try {
      await api('/api/admin/auto-content/approve', {method:'POST', body: JSON.stringify({key, action})})
      load()
    } catch (e: any) {
      alert('실패: ' + (e.message || e))
    }
  }

  if (loading) return <div style={{color:'#8b949e', padding:20}}>Loading auto-generated content…</div>

  const sevColor: Record<string,string> = {CRITICAL:'#f85149', HIGH:'#f97316', MEDIUM:'#d29922', LOW:'#3fb950'}
  const statusBadge = (s: string) => {
    const colors: Record<string,string> = {approve:'#3fb950', reject:'#f85149', pending:'#8b949e'}
    return <span style={{padding:'2px 8px', borderRadius:10, fontSize:11, background:colors[s]+'20', color:colors[s], fontWeight:600}}>{s}</span>
  }
  const deploy = async (key: string, dryRun: boolean) => {
    try {
      const r = await api('/api/admin/auto-content/deploy', {method:'POST', body: JSON.stringify({key, dry_run: dryRun})})
      const tag = dryRun ? '[DRY]' : '[APPLY]'
      alert(`${tag} ${key}\nsyntax_ok: ${r.syntax_ok}\napplied: ${r.applied}\n${(r.test_output || r.apply_output || '').slice(0, 400)}`)
    } catch (e: any) {
      try { alert('실패: ' + (JSON.parse(e.message)?.detail || e.message)) } catch { alert('실패: ' + e.message) }
    }
  }

  const regenerateSpecial = async (cveId: string) => {
    if (!confirm(`${cveId}에 대해 관련 과목별 '최신 보안이슈' 특강(강의+실습)을 재생성합니다.\n수 분 소요됩니다.`)) return
    try {
      const r = await api('/api/admin/auto-content/regenerate-special', {method:'POST', body: JSON.stringify({cve_id: cveId})})
      const summary = (r.results || []).map((x:any) => `${x.course}: ${x.ok ? 'OK '+(x.lab ? `(lecture+lab ${x.lab_steps||0}steps)` : '(lecture)') : 'FAIL '+x.error}`).join('\n')
      alert(`재생성 완료\n${summary}`)
    } catch (e: any) {
      try { alert('실패: ' + (JSON.parse(e.message)?.detail || e.message)) } catch { alert('실패: ' + e.message) }
    }
  }

  const actions = (key: string, status: string) => (
    <div style={{display:'flex', gap:6, flexWrap:'wrap'}}>
      {status !== 'approve' && <button onClick={() => setStatus(key, 'approve')} style={{...smallBtn, background:'#1f3a2b', borderColor:'#3fb950', color:'#3fb950'}}>✓ 승인</button>}
      {status !== 'reject' && <button onClick={() => setStatus(key, 'reject')} style={{...smallBtn, background:'#3a1f1f', borderColor:'#f85149', color:'#f85149'}}>✗ 거부</button>}
      {status !== 'pending' && <button onClick={() => setStatus(key, 'pending')} style={smallBtn}>대기</button>}
      {status === 'approve' && (key.startsWith('rule:') || key.startsWith('battle:')) && (
        <>
          <button onClick={() => deploy(key, true)} style={{...smallBtn, borderColor:'#58a6ff', color:'#58a6ff'}}>🔍 dry-run</button>
          <button onClick={() => confirm('실제 인프라에 배포합니다. 계속?') && deploy(key, false)} style={{...smallBtn, background:'#1f2a3a', borderColor:'#58a6ff', color:'#58a6ff'}}>🚀 배포</button>
        </>
      )}
      {status === 'approve' && key.startsWith('threat:') && (
        <button onClick={() => regenerateSpecial(key.slice('threat:'.length))}
          style={{...smallBtn, borderColor:'#f97316', color:'#f97316'}}>📚 특강 재생성</button>
      )}
    </div>
  )

  return (
    <div>
      <div style={{display:'flex', gap:8, marginBottom:16}}>
        {(['threats','battles','rules'] as const).map(s => (
          <button key={s} onClick={() => setSection(s)} style={{
            padding:'8px 16px', borderRadius:6, border:'1px solid #30363d',
            background: section === s ? '#f97316' : '#21262d',
            color: section === s ? '#fff' : '#8b949e', cursor:'pointer', fontSize:13,
          }}>
            {s === 'threats' ? `🛡️ Threats (${data.threats.length})` :
             s === 'battles' ? `⚔️ Battles (${data.battles.length})` :
             `🔒 Rules (${data.rules.length})`}
          </button>
        ))}
      </div>

      {section === 'threats' && (
        <div style={{display:'grid', gap:10}}>
          {data.threats.map((t, i) => {
            const key = `threat:${t.id}`
            return (
              <div key={i} style={{background:'#0d1117', border:'1px solid #21262d', borderLeft:`3px solid ${sevColor[t.severity] || '#8b949e'}`, borderRadius:6, padding:'12px 16px'}}>
                <div style={{display:'flex', gap:10, alignItems:'center', marginBottom:6}}>
                  <code style={{color:'#58a6ff', fontSize:12, background:'#21262d', padding:'1px 6px', borderRadius:3}}>{t.id}</code>
                  <span style={{fontSize:11, color:sevColor[t.severity], fontWeight:600}}>{t.severity} ({t.cvss_score})</span>
                  {statusBadge(t.status)}
                  <div style={{marginLeft:'auto'}}>{actions(key, t.status)}</div>
                </div>
                <div style={{fontSize:13, color:'#e6edf3', marginBottom:4}}>{t.summary}</div>
                {t.courses?.length > 0 && <div style={{fontSize:11, color:'#f97316'}}>과목: {t.courses.join(' · ')}</div>}
              </div>
            )
          })}
        </div>
      )}

      {section === 'battles' && (
        <div style={{display:'grid', gap:10}}>
          {data.battles.map((b, i) => {
            const key = `battle:${b.file}`
            return (
              <div key={i} style={{background:'#0d1117', border:'1px solid #21262d', borderRadius:6, padding:'12px 16px'}}>
                <div style={{display:'flex', gap:10, alignItems:'center', marginBottom:6}}>
                  <code style={{color:'#58a6ff', fontSize:12, background:'#21262d', padding:'1px 6px', borderRadius:3}}>{b.lab_id}</code>
                  <span style={{fontSize:11, color:'#8b949e'}}>{b.difficulty} · {b.steps} steps</span>
                  {statusBadge(b.status)}
                  <div style={{marginLeft:'auto'}}>{actions(key, b.status)}</div>
                </div>
                <div style={{fontSize:13, color:'#e6edf3'}}>{b.title}</div>
              </div>
            )
          })}
        </div>
      )}

      {section === 'rules' && (
        <div style={{display:'grid', gap:10}}>
          {data.rules.map((r, i) => {
            const key = `rule:${r.type}:${r.file}`
            return (
              <div key={i} style={{background:'#0d1117', border:'1px solid #21262d', borderRadius:6, padding:'12px 16px'}}>
                <div style={{display:'flex', gap:10, alignItems:'center', marginBottom:6}}>
                  <span style={{fontSize:11, padding:'2px 6px', borderRadius:3, background:r.type==='suricata'?'rgba(249,115,22,0.15)':'rgba(88,166,255,0.15)', color:r.type==='suricata'?'#f97316':'#58a6ff', fontWeight:600}}>{r.type}</span>
                  <code style={{color:'#e6edf3', fontSize:12}}>{r.file}</code>
                  <span style={{fontSize:11, color:'#8b949e'}}>{r.lines} lines</span>
                  {statusBadge(r.status)}
                  <div style={{marginLeft:'auto'}}>{actions(key, r.status)}</div>
                </div>
                <pre style={{fontSize:11, color:'#8b949e', overflow:'auto', margin:0, padding:'6px 0 0', whiteSpace:'pre-wrap', maxHeight:120}}>{r.preview}</pre>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function LabVerifyPanel() {
  const [verifyLog, setVerifyLog] = useState<any[]>([])
  const [running, setRunning] = useState(false)
  const [sampleWeeks, setSampleWeeks] = useState('1,8,15')

  const runVerify = async () => {
    setRunning(true)
    setVerifyLog([])
    const weeks = sampleWeeks.split(',').map(w => parseInt(w.trim())).filter(w => !isNaN(w))
    try {
      const token = localStorage.getItem('ccc_token') || ''
      const resp = await fetch('/api/labs/verify-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': 'ccc-api-key-2026', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ sample_weeks: weeks }),
      })
      const reader = resp.body?.getReader()
      const decoder = new TextDecoder()
      if (reader) {
        let buf = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buf += decoder.decode(value, { stream: true })
          const lines = buf.split('\n')
          buf = lines.pop() || ''
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try { setVerifyLog(prev => [...prev, JSON.parse(line.slice(6))]) } catch {}
            }
          }
        }
      }
    } catch (e: any) {
      setVerifyLog(prev => [...prev, { event: 'error', detail: e.message }])
    }
    setRunning(false)
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 20 }}>
        <input value={sampleWeeks} onChange={e => setSampleWeeks(e.target.value)}
          placeholder="Sample weeks (e.g., 1,8,15)" style={{ ...inputStyle, flex: 'none', width: 200 }} />
        <button onClick={runVerify} disabled={running} style={{
          ...btnStyle, background: running ? '#21262d' : '#58a6ff',
        }}>{running ? 'Testing...' : 'Run Lab Verify'}</button>
        <span style={{ fontSize: 12, color: '#8b949e' }}>
          비어있으면 전체 주차 테스트 (오래 걸림)
        </span>
      </div>

      {verifyLog.length > 0 && (
        <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: 8, padding: 16, fontFamily: 'Consolas,monospace', fontSize: 12, maxHeight: 500, overflowY: 'auto' }}>
          {verifyLog.map((evt, i) => {
            if (evt.event === 'lab_start') return (
              <div key={i} style={{ padding: '4px 0', color: '#58a6ff', fontWeight: 600, borderTop: i > 0 ? '1px solid #21262d' : 'none', marginTop: i > 0 ? 4 : 0 }}>
                {evt.lab_id} — {evt.title} ({evt.total_steps} steps)
              </div>
            )
            if (evt.event === 'lab_step') return (
              <div key={i} style={{ padding: '1px 0 1px 16px', color: evt.passed ? '#3fb950' : '#f85149' }}>
                {evt.passed ? 'P' : 'F'} step{evt.step}({evt.target_vm}) {evt.instruction}
              </div>
            )
            if (evt.event === 'lab_done') return (
              <div key={i} style={{ padding: '2px 0 2px 16px', fontWeight: 600, color: evt.pct >= 80 ? '#3fb950' : evt.pct >= 50 ? '#d29922' : '#f85149' }}>
                {evt.passed}/{evt.total} ({evt.pct}%)
              </div>
            )
            if (evt.event === 'verify_complete') return (
              <div key={i} style={{ padding: '8px 0', fontWeight: 700, borderTop: '1px solid #30363d', marginTop: 8, color: evt.pct >= 80 ? '#3fb950' : '#f97316' }}>
                TOTAL: {evt.total_passed}/{evt.total_steps} ({evt.pct}%) — {evt.labs_tested} labs tested
              </div>
            )
            return null
          })}
        </div>
      )}
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d',
  borderRadius: 6, padding: '8px 12px', fontSize: 13, flex: 1,
}
const btnStyle: React.CSSProperties = {
  padding: '8px 20px', borderRadius: 6, border: 'none',
  background: '#f97316', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer',
}
const smallBtn: React.CSSProperties = {
  padding: '5px 12px', borderRadius: 6, border: '1px solid #30363d',
  background: '#21262d', color: '#e6edf3', cursor: 'pointer', fontSize: 12,
}

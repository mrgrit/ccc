import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

const tabs = ['Groups', 'Students', 'Promotions', 'Lab Verify'] as const
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

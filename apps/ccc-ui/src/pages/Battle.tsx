import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

export default function Battle() {
  const [active, setActive] = useState<any[]>([])
  const [completed, setCompleted] = useState<any[]>([])
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api('/api/battles?status=active').then(d => d.battles || []).catch(() => []),
      api('/api/battles?status=completed').then(d => d.battles || []).catch(() => []),
      api('/api/battles/events/recent').catch(() => []),
    ]).then(([a, c, e]) => {
      setActive(a)
      setCompleted(c)
      setEvents(Array.isArray(e) ? e : [])
    }).catch(e => setError(e.message)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
  if (error) return <div style={{ color: '#f85149', padding: 40, textAlign: 'center' }}>Error: {error}</div>

  const statusColor: Record<string, string> = { active: '#3fb950', completed: '#8b949e', pending: '#d29922' }

  const renderBattle = (b: any) => (
    <div key={b.id} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16, marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 10, background: `${statusColor[b.status] || '#484f58'}22`, color: statusColor[b.status] || '#8b949e', fontWeight: 600 }}>{b.status}</span>
        <span style={{ fontSize: 11, color: '#484f58', marginLeft: 8 }}>{b.mode} / {b.battle_type}</span>
        <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
          <code style={{ color: '#e6edf3' }}>{b.challenger_id?.slice(0, 8)}</code>
          <span style={{ color: '#f97316', fontWeight: 700 }}>vs</span>
          <code style={{ color: '#e6edf3' }}>{b.defender_id?.slice(0, 8) || '?'}</code>
        </div>
      </div>
      {b.status === 'active' && <button style={{ padding: '6px 16px', borderRadius: 6, border: '1px solid #f97316', background: 'transparent', color: '#f97316', cursor: 'pointer', fontSize: 13 }}>Watch</button>}
    </div>
  )

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#e6edf3' }}>Battle Arena</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div>
          <h3 style={{ fontSize: 16, marginBottom: 12 }}>Active ({active.length})</h3>
          {active.length === 0 ? (
            <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 30, textAlign: 'center', color: '#8b949e' }}>No active battles</div>
          ) : active.map(renderBattle)}

          <h3 style={{ fontSize: 16, marginTop: 24, marginBottom: 12 }}>Completed ({completed.length})</h3>
          {completed.length === 0 ? (
            <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 30, textAlign: 'center', color: '#8b949e' }}>No completed battles</div>
          ) : completed.map(renderBattle)}
        </div>

        <div>
          <h3 style={{ fontSize: 16, marginBottom: 12 }}>Live Events</h3>
          <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16, maxHeight: 500, overflowY: 'auto' as const }}>
            {events.length === 0 ? (
              <div style={{ color: '#8b949e', textAlign: 'center', padding: 20 }}>No recent events</div>
            ) : events.map((e, i) => (
              <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #21262d', fontSize: 12, display: 'flex', gap: 8 }}>
                <span style={{ color: '#f97316', fontWeight: 600, minWidth: 60 }}>{e.event_type}</span>
                <span style={{ color: '#8b949e' }}>{e.actor?.slice(0, 8)}</span>
                <span style={{ color: '#484f58', flex: 1 }}>{e.description?.slice(0, 40)}</span>
                {e.points > 0 && <span style={{ color: '#3fb950' }}>+{e.points}</span>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

interface BattleRecord {
  id: string
  challenger: string
  defender: string
  score_challenger: number
  score_defender: number
  status: 'active' | 'completed' | 'pending'
  created_at?: string
  winner?: string
}

interface BattleEvent {
  ts: string
  actor: string
  action: string
}

const cardStyle: React.CSSProperties = {
  background: '#161b22',
  border: '1px solid #30363d',
  borderRadius: 8,
  padding: 20,
}

const statusColors: Record<string, string> = {
  active: '#3fb950',
  completed: '#8b949e',
  pending: '#d29922',
}

export default function Battle() {
  const [active, setActive] = useState<BattleRecord[]>([])
  const [completed, setCompleted] = useState<BattleRecord[]>([])
  const [events, setEvents] = useState<BattleEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [challenger, setChallenger] = useState('')
  const [defender, setDefender] = useState('')

  useEffect(() => {
    Promise.all([
      api<BattleRecord[]>('/api/battles?status=active').catch(() => []),
      api<BattleRecord[]>('/api/battles?status=completed').catch(() => []),
      api<BattleEvent[]>('/api/battles/events/recent').catch(() => []),
    ]).then(([a, c, e]) => {
      setActive(a)
      setCompleted(c)
      setEvents(e)
    }).finally(() => setLoading(false))
  }, [])

  const handleCreate = async () => {
    if (!challenger || !defender) return
    try {
      await api('/api/battles', {
        method: 'POST',
        body: JSON.stringify({ challenger, defender }),
      })
      setChallenger('')
      setDefender('')
      setFormOpen(false)
      const a = await api<BattleRecord[]>('/api/battles?status=active').catch(() => [])
      setActive(a)
    } catch {
      // silently fail
    }
  }

  const renderBattle = (b: BattleRecord) => (
    <div key={b.id} style={{
      ...cardStyle,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 12,
    }}>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <span style={{
            fontSize: 11,
            padding: '2px 8px',
            borderRadius: 10,
            background: `${statusColors[b.status]}22`,
            color: statusColors[b.status],
            fontWeight: 600,
          }}>
            {b.status}
          </span>
          {b.created_at && (
            <span style={{ fontSize: 11, color: '#484f58' }}>{b.created_at}</span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 15, fontWeight: 600, color: '#e6edf3' }}>{b.challenger}</span>
          <span style={{ fontSize: 13, color: '#f97316', fontWeight: 700 }}>{b.score_challenger}</span>
          <span style={{ fontSize: 13, color: '#484f58', margin: '0 4px' }}>vs</span>
          <span style={{ fontSize: 13, color: '#f97316', fontWeight: 700 }}>{b.score_defender}</span>
          <span style={{ fontSize: 15, fontWeight: 600, color: '#e6edf3' }}>{b.defender}</span>
        </div>
        {b.winner && (
          <div style={{ fontSize: 12, color: '#3fb950', marginTop: 4 }}>Winner: {b.winner}</div>
        )}
      </div>
      {b.status === 'active' && (
        <button style={{
          padding: '6px 16px',
          borderRadius: 6,
          border: '1px solid #f97316',
          background: 'transparent',
          color: '#f97316',
          cursor: 'pointer',
          fontSize: 13,
          fontWeight: 600,
        }}>
          Watch
        </button>
      )}
    </div>
  )

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, color: '#e6edf3' }}>Battle Arena</h2>
        <button
          onClick={() => setFormOpen(!formOpen)}
          style={{
            padding: '8px 20px',
            borderRadius: 6,
            border: 'none',
            background: '#f97316',
            color: '#fff',
            cursor: 'pointer',
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          + Create Battle
        </button>
      </div>

      {formOpen && (
        <div style={{ ...cardStyle, marginBottom: 24, display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: 12, color: '#8b949e' }}>Challenger</label>
            <input
              value={challenger}
              onChange={e => setChallenger(e.target.value)}
              placeholder="Student name"
              style={{
                padding: '8px 12px', borderRadius: 6, border: '1px solid #30363d',
                background: '#0d1117', color: '#e6edf3', fontSize: 14, width: 200,
              }}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: 12, color: '#8b949e' }}>Defender</label>
            <input
              value={defender}
              onChange={e => setDefender(e.target.value)}
              placeholder="Student name"
              style={{
                padding: '8px 12px', borderRadius: 6, border: '1px solid #30363d',
                background: '#0d1117', color: '#e6edf3', fontSize: 14, width: 200,
              }}
            />
          </div>
          <button
            onClick={handleCreate}
            style={{
              padding: '8px 20px', borderRadius: 6, border: 'none',
              background: '#f97316', color: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 600,
            }}
          >
            Start
          </button>
        </div>
      )}

      {loading ? (
        <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3', marginBottom: 16 }}>
              Active Battles ({active.length})
            </h3>
            {active.length === 0 ? (
              <div style={{ ...cardStyle, color: '#8b949e', textAlign: 'center', fontSize: 13 }}>
                No active battles
              </div>
            ) : (
              active.map(renderBattle)
            )}

            <h3 style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3', marginTop: 32, marginBottom: 16 }}>
              Completed ({completed.length})
            </h3>
            {completed.length === 0 ? (
              <div style={{ ...cardStyle, color: '#8b949e', textAlign: 'center', fontSize: 13 }}>
                No completed battles yet
              </div>
            ) : (
              completed.map(renderBattle)
            )}
          </div>

          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3', marginBottom: 16 }}>
              Live Events
            </h3>
            <div style={{ ...cardStyle, maxHeight: 500, overflowY: 'auto' }}>
              {events.length === 0 ? (
                <div style={{ color: '#8b949e', textAlign: 'center', fontSize: 13 }}>
                  No recent events
                </div>
              ) : (
                events.map((ev, i) => (
                  <div key={i} style={{
                    padding: '8px 0',
                    borderBottom: i < events.length - 1 ? '1px solid #21262d' : 'none',
                    display: 'flex', gap: 12, alignItems: 'center',
                  }}>
                    <span style={{ fontSize: 11, color: '#484f58', whiteSpace: 'nowrap' }}>{ev.ts}</span>
                    <span style={{ fontSize: 13, color: '#f97316', fontWeight: 600 }}>{ev.actor}</span>
                    <span style={{ fontSize: 13, color: '#8b949e' }}>{ev.action}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

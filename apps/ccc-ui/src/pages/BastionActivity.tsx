import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'
import { isAdmin } from '../auth.ts'

type Health = {
  graph_nodes: number; history_anchors: number;
  context_module: boolean; recorder_module: boolean;
  graph_db: boolean; history_db: boolean;
  last_chat_kg_used: boolean; last_chat_kg_recorded: boolean;
  all_modules_loaded: boolean;
}

type Stats = {
  node_counts: Record<string, number>
  edge_counts: Record<string, number>
  total_nodes: number; total_edges: number
}

type Anchor = {
  id: string; kind: string; label: string; created_at: string
}

type Audit = {
  id: number; request_id: string; session_id: string;
  ts_start: string; ts_end: string; duration_ms: number;
  user_prompt: string; final_answer: string;
  course?: string; step_order?: number;
}

type Tab = 'health' | 'audit' | 'anchors' | 'graph'

export default function BastionActivity() {
  const [tab, setTab] = useState<Tab>('health')
  const [health, setHealth] = useState<Health | null>(null)
  const [stats, setStats] = useState<Stats | null>(null)
  const [anchors, setAnchors] = useState<Anchor[]>([])
  const [audit, setAudit] = useState<Audit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedAudit, setSelectedAudit] = useState<Audit | null>(null)

  useEffect(() => {
    if (!isAdmin()) { setLoading(false); return }
    setLoading(true); setError('')
    Promise.all([
      api<Health>('/admin/bastion/kg/health').catch(() => null),
      api<Stats>('/admin/bastion/graph/stats').catch(() => null),
      api<{ anchors: Anchor[] }>('/admin/bastion/kg/anchors/recent?limit=20').then(r => r.anchors || []).catch(() => []),
      api<{ audit: Audit[] }>('/admin/bastion/audit?limit=50').then(r => r.audit || []).catch(() => []),
    ]).then(([h, s, an, ad]) => {
      setHealth(h); setStats(s); setAnchors(an); setAudit(ad)
    }).catch(e => setError(e.message || 'bastion 연결 실패'))
      .finally(() => setLoading(false))
  }, [])

  if (!isAdmin()) {
    return <div style={{ color: '#f85149', padding: 40, fontSize: 15 }}>관리자 전용 페이지입니다.</div>
  }
  if (loading) return <div style={{ color: '#8b949e', padding: 40 }}>Loading…</div>

  return (
    <div style={{ padding: '0 8px' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 20 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: '#e6edf3' }}>🤖 Bastion Activity (Admin)</h2>
        <span style={{ fontSize: 12, color: '#8b949e' }}>
          bastion @ <code style={{ color: '#f97316' }}>192.168.0.110:9100</code>
        </span>
      </div>

      {error && (
        <div style={{ color: '#f85149', marginBottom: 12, fontSize: 13 }}>{error}</div>
      )}

      {/* Top KPI cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 10, marginBottom: 20 }}>
        <Card label="Graph Nodes" value={stats?.total_nodes ?? health?.graph_nodes ?? '?'} />
        <Card label="Total Edges" value={stats?.total_edges ?? '?'} />
        <Card label="Anchors" value={health?.history_anchors ?? '?'} />
        <Card label="Audit Rows" value={audit.length > 0 ? `${audit.length}+` : '?'} />
        <Card label="Modules" value={health?.all_modules_loaded ? '✅ OK' : '⚠️'} />
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 16, borderBottom: '1px solid #30363d' }}>
        {(['health', 'audit', 'anchors', 'graph'] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            background: tab === t ? '#161b22' : 'transparent',
            color: tab === t ? '#f97316' : '#8b949e',
            border: 'none', borderBottom: tab === t ? '2px solid #f97316' : '2px solid transparent',
            padding: '8px 16px', fontSize: 13, cursor: 'pointer', textTransform: 'capitalize',
          }}>{t}</button>
        ))}
      </div>

      {/* Tab: Health */}
      {tab === 'health' && health && (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16 }}>
          <h3 style={{ fontSize: 15, color: '#e6edf3', marginBottom: 12 }}>KG modules</h3>
          <table style={{ width: '100%', fontSize: 13, color: '#c9d1d9' }}>
            <tbody>
              {Object.entries({
                'context_module': health.context_module,
                'recorder_module': health.recorder_module,
                'graph_db': health.graph_db,
                'history_db': health.history_db,
                'last_chat_kg_used': health.last_chat_kg_used,
                'last_chat_kg_recorded': health.last_chat_kg_recorded,
                'all_modules_loaded': health.all_modules_loaded,
              }).map(([k, v]) => (
                <tr key={k} style={{ borderBottom: '1px solid #21262d' }}>
                  <td style={{ padding: '8px 0', color: '#8b949e' }}>{k}</td>
                  <td style={{ padding: '8px 0', color: v ? '#3fb950' : '#f85149' }}>{v ? '✅' : '❌'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab: Audit */}
      {tab === 'audit' && (
        <div>
          <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden' }}>
            <table style={{ width: '100%', fontSize: 12 }}>
              <thead style={{ background: '#0d1117', color: '#8b949e' }}>
                <tr>
                  <th style={{ padding: '8px 12px', textAlign: 'left' }}>id</th>
                  <th style={{ padding: '8px 12px', textAlign: 'left' }}>ts</th>
                  <th style={{ padding: '8px 12px', textAlign: 'right' }}>ms</th>
                  <th style={{ padding: '8px 12px', textAlign: 'left' }}>prompt</th>
                </tr>
              </thead>
              <tbody>
                {audit.map(a => (
                  <tr key={a.id} onClick={() => setSelectedAudit(a)} style={{
                    borderBottom: '1px solid #21262d', cursor: 'pointer',
                  }}>
                    <td style={{ padding: '6px 12px', color: '#f97316' }}>{a.id}</td>
                    <td style={{ padding: '6px 12px', color: '#8b949e' }}>{a.ts_start?.slice(11, 19)}</td>
                    <td style={{ padding: '6px 12px', color: a.duration_ms > 100000 ? '#f85149' : '#c9d1d9', textAlign: 'right' }}>{a.duration_ms}</td>
                    <td style={{ padding: '6px 12px', color: '#c9d1d9', maxWidth: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {a.user_prompt}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {selectedAudit && (
            <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: 8, padding: 16, marginTop: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
                <span style={{ color: '#f97316', fontSize: 13 }}>request_id: {selectedAudit.request_id}</span>
                <button onClick={() => setSelectedAudit(null)} style={{ background: 'transparent', color: '#8b949e', border: 'none', cursor: 'pointer' }}>×</button>
              </div>
              <div style={{ color: '#8b949e', fontSize: 11, marginBottom: 8 }}>
                {selectedAudit.ts_start} → {selectedAudit.ts_end} ({selectedAudit.duration_ms} ms)
              </div>
              <div style={{ color: '#c9d1d9', fontSize: 12, marginBottom: 12, padding: 12, background: '#161b22', borderRadius: 4 }}>
                <b style={{ color: '#3fb950' }}>prompt</b><br />{selectedAudit.user_prompt}
              </div>
              <pre style={{ color: '#c9d1d9', fontSize: 11, background: '#161b22', padding: 12, borderRadius: 4, maxHeight: 400, overflow: 'auto', whiteSpace: 'pre-wrap' }}>
                {selectedAudit.final_answer}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Tab: Anchors */}
      {tab === 'anchors' && (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden' }}>
          {anchors.map(a => (
            <div key={a.id} style={{ padding: '12px 16px', borderBottom: '1px solid #21262d' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
                <code style={{ color: '#f97316', fontSize: 11 }}>{a.id}</code>
                <span style={{ color: '#8b949e', fontSize: 11 }}>{a.created_at}</span>
              </div>
              <div style={{ color: '#c9d1d9', fontSize: 13 }}>{a.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Graph */}
      {tab === 'graph' && stats && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16 }}>
            <h3 style={{ fontSize: 14, color: '#e6edf3', marginBottom: 12 }}>Node Types</h3>
            <table style={{ width: '100%', fontSize: 13 }}>
              <tbody>
                {Object.entries(stats.node_counts).map(([t, c]) => (
                  <tr key={t} style={{ borderBottom: '1px solid #21262d' }}>
                    <td style={{ padding: '6px 0', color: '#c9d1d9' }}>{t}</td>
                    <td style={{ padding: '6px 0', color: '#f97316', textAlign: 'right' }}>{c}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16 }}>
            <h3 style={{ fontSize: 14, color: '#e6edf3', marginBottom: 12 }}>Edge Types</h3>
            <table style={{ width: '100%', fontSize: 13 }}>
              <tbody>
                {Object.entries(stats.edge_counts).map(([t, c]) => (
                  <tr key={t} style={{ borderBottom: '1px solid #21262d' }}>
                    <td style={{ padding: '6px 0', color: '#c9d1d9' }}>{t}</td>
                    <td style={{ padding: '6px 0', color: '#f97316', textAlign: 'right' }}>{c}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function Card({ label, value }: { label: string; value: any }) {
  return (
    <div style={{
      background: '#161b22', border: '1px solid #30363d', borderRadius: 8,
      padding: '14px 16px',
    }}>
      <div style={{ color: '#8b949e', fontSize: 12, marginBottom: 4 }}>{label}</div>
      <div style={{ color: '#f97316', fontSize: 20, fontWeight: 600 }}>{value}</div>
    </div>
  )
}

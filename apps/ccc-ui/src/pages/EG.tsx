import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'
import { isAdmin } from '../auth.ts'

type Stats = {
  node_counts?: Record<string, number>
  edge_counts?: Record<string, number>
  total_nodes?: number
  total_edges?: number
  total_anchors?: number
  experiments?: number
  notes?: number
  alerts?: number
}

const MISSIONS = [
  { code: 'M1', name: '정찰', en: 'Reconnaissance' },
  { code: 'M2', name: '탐지', en: 'Detection' },
  { code: 'M3', name: '방어', en: 'Defense' },
  { code: 'M4', name: '공격', en: 'Offensive' },
  { code: 'M5', name: '사고대응', en: 'Incident Response' },
  { code: 'M6', name: 'AI보안', en: 'AI Security' },
  { code: 'M7', name: '컴플라이언스', en: 'Compliance' },
  { code: 'M8', name: '기억운영', en: 'Knowledge Management' },
  { code: 'M9', name: '범용운영', en: 'General Operations' },
]

export default function EG() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isAdmin()) { setLoading(false); return }
    api('/api/eg-portal/api/kg/stats')
      .then((d: Stats) => setStats(d))
      .catch(e => setError(e.message || 'EG 포털 연결 실패'))
      .finally(() => setLoading(false))
  }, [])

  if (!isAdmin()) {
    return <div style={{ color: '#f85149', padding: 40, fontSize: 15 }}>관리자 전용 페이지입니다.</div>
  }
  if (loading) return <div style={{ color: '#8b949e', padding: 40 }}>Loading…</div>
  if (error) return (
    <div style={{ padding: 40 }}>
      <div style={{ color: '#f85149', marginBottom: 12, fontSize: 15 }}>{error}</div>
      <div style={{ color: '#8b949e', fontSize: 13, lineHeight: 1.6 }}>
        EG 포털 (192.168.0.110:8500) 미가동 또는 EG_ADMIN_TOKEN 미설정.<br/>
        deploy: <code style={{ color: '#f97316' }}>scripts/eg/deploy.sh</code>
      </div>
    </div>
  )

  const nodeCounts = stats?.node_counts || {}
  const edgeCounts = stats?.edge_counts || {}
  const focusNodeTypes = ['Mission', 'Skill', 'Concept', 'Plan', 'Playbook', 'Experience', 'Insight', 'Asset']

  return (
    <div style={{ padding: '0 8px' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 20 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: '#e6edf3' }}>🕸️ Experience Graph (Admin)</h2>
        <span style={{ fontSize: 12, color: '#8b949e' }}>
          eg-6v6.db @ <code style={{ color: '#f97316' }}>192.168.0.110:8500</code>
        </span>
      </div>

      {/* 전체 카운트 카드 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 10, marginBottom: 24 }}>
        <Card label="Total Nodes" value={stats?.total_nodes ?? '?'} />
        <Card label="Total Edges" value={stats?.total_edges ?? '?'} />
        <Card label="Anchors" value={stats?.total_anchors ?? '?'} />
        <Card label="Experiments" value={stats?.experiments ?? '?'} />
      </div>

      {/* 9 Mission Dashboard — node count per Mission (스킬+컨셉만, anchor 는 별도 view) */}
      <div style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 16, color: '#e6edf3', marginBottom: 12 }}>9 Mission 카탈로그 노드</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
          {MISSIONS.map(m => (
            <div key={m.code} style={{
              background: '#161b22', border: '1px solid #30363d', borderRadius: 8,
              padding: '12px 14px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ color: '#f97316', fontWeight: 600, fontSize: 13 }}>{m.code}</span>
                <span style={{ color: '#8b949e', fontSize: 11 }}>{m.en}</span>
              </div>
              <div style={{ color: '#e6edf3', fontSize: 15, marginTop: 4 }}>{m.name}</div>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 8, fontSize: 12, color: '#8b949e' }}>
          상세: <a href={`http://192.168.0.110:8500/`} target="_blank" rel="noreferrer" style={{ color: '#f97316' }}>EG 포털 →</a> (별도 로그인 — X-Admin-Token)
        </div>
      </div>

      {/* 노드 type 분포 */}
      <div style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 16, color: '#e6edf3', marginBottom: 12 }}>노드 type 분포</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
          {focusNodeTypes.map(t => (
            <Card key={t} label={t} value={nodeCounts[t] ?? 0} small />
          ))}
        </div>
      </div>

      {/* 엣지 type 분포 (top 8) */}
      <div>
        <h3 style={{ fontSize: 16, color: '#e6edf3', marginBottom: 12 }}>엣지 type 분포 (top 8)</h3>
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 14 }}>
          {Object.entries(edgeCounts)
            .sort((a, b) => b[1] - a[1]).slice(0, 8)
            .map(([t, n]) => (
              <div key={t} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 13 }}>
                <span style={{ color: '#c9d1d9' }}>{t}</span>
                <span style={{ color: '#f97316' }}>{n}</span>
              </div>
            ))}
        </div>
      </div>
    </div>
  )
}

function Card({ label, value, small }: { label: string; value: number | string; small?: boolean }) {
  return (
    <div style={{
      background: '#161b22', border: '1px solid #30363d', borderRadius: 8,
      padding: small ? '10px 14px' : '14px 18px',
    }}>
      <div style={{ color: '#8b949e', fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5 }}>{label}</div>
      <div style={{ color: '#e6edf3', fontSize: small ? 18 : 22, fontWeight: 600, marginTop: 4 }}>{value}</div>
    </div>
  )
}

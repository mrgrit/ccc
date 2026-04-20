import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'
import { getUser } from '../auth.ts'

export default function Dashboard() {
  const user = getUser()
  const [stats, setStats] = useState<any>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [fbLoading, setFbLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [threats, setThreats] = useState<any[]>([])

  useEffect(() => {
    api('/api/user/stats').then(setStats).catch(() => {}).finally(() => setLoading(false))
    api('/api/threats/recent?limit=5').then(setThreats).catch(() => {})
  }, [])

  const getFeedback = async () => {
    setFbLoading(true)
    try {
      const d = await api('/api/user/ai-feedback')
      setFeedback(d.feedback)
    } catch { setFeedback('피드백을 불러올 수 없습니다.') }
    setFbLoading(false)
  }

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>

  const s = stats
  return (
    <div>
      {/* 프로필 헤더 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: '#e6edf3', marginBottom: 4 }}>
            Welcome, {s?.student?.name || user?.name || 'User'}
          </h2>
          <div style={{ fontSize: 15, color: '#8b949e' }}>
            <span style={{ color: '#f97316', fontWeight: 600, textTransform: 'uppercase' }}>{s?.student?.rank || 'rookie'}</span>
            <span style={{ margin: '0 8px' }}>·</span>
            <span>{s?.student?.total_blocks || 0} blocks</span>
          </div>
        </div>
        <button onClick={getFeedback} disabled={fbLoading} style={{
          padding: '10px 20px', borderRadius: 8, border: 'none',
          background: '#f97316', color: '#fff', cursor: 'pointer', fontSize: 15, fontWeight: 600,
        }}>{fbLoading ? 'AI 분석 중...' : '🤖 AI 피드백 받기'}</button>
      </div>

      {/* 통계 카드 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 14, marginBottom: 24 }}>
        {[
          { label: 'Labs 완료', value: `${s?.labs?.completed || 0}/${s?.labs?.total || 0}`, color: '#3fb950' },
          { label: 'CTF 해결', value: `${s?.ctf?.solved || 0} (${s?.ctf?.points || 0}pts)`, color: '#58a6ff' },
          { label: '대전', value: `${s?.battles?.wins || 0}승/${s?.battles?.total || 0}`, color: '#f97316' },
          { label: '승률', value: `${s?.battles?.win_rate || 0}%`, color: '#d29922' },
          { label: '총 블록', value: s?.student?.total_blocks || 0, color: '#bc8cff' },
        ].map(c => (
          <div key={c.label} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 20 }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: 14, color: '#8b949e', marginTop: 4 }}>{c.label}</div>
          </div>
        ))}
      </div>

      {/* AI 피드백 */}
      {feedback && (
        <div style={{ background: '#161b22', border: '1px solid #f97316', borderRadius: 10, padding: 24, marginBottom: 24 }}>
          <h3 style={{ fontSize: 17, color: '#f97316', marginBottom: 12 }}>🤖 AI 학습 피드백</h3>
          <div style={{ fontSize: 15, color: '#c9d1d9', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{feedback}</div>
        </div>
      )}

      {/* 과목별 진도 */}
      {s?.course_progress?.length > 0 && (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 20, marginBottom: 24 }}>
          <h3 style={{ fontSize: 17, marginBottom: 14, color: '#e6edf3' }}>과목별 진도</h3>
          {s.course_progress.map((cp: any) => (
            <div key={cp.course} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <span style={{ minWidth: 180, fontSize: 14, color: '#8b949e' }}>{cp.course}</span>
              <div style={{ flex: 1, height: 8, background: '#21262d', borderRadius: 4 }}>
                <div style={{ width: `${Math.min(100, cp.done / 15 * 100)}%`, height: '100%', background: '#3fb950', borderRadius: 4 }} />
              </div>
              <span style={{ fontSize: 13, color: '#3fb950', minWidth: 40 }}>{cp.done}/15</span>
            </div>
          ))}
        </div>
      )}

      {/* 오늘의 위협 (CTI) */}
      {threats.length > 0 && (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 20, marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <h3 style={{ fontSize: 17, color: '#e6edf3', margin: 0 }}>🛡️ 오늘의 위협 (CTI)</h3>
            <span style={{ fontSize: 12, color: '#8b949e' }}>SubAgent(gemma3:4b) 수집·요약</span>
          </div>
          <div style={{ display: 'grid', gap: 10 }}>
            {threats.map((t: any, i: number) => {
              const sevColor: Record<string, string> = {
                CRITICAL: '#f85149', HIGH: '#f97316',
                MEDIUM: '#d29922', LOW: '#3fb950', UNKNOWN: '#8b949e',
              }
              return (
                <div key={i} style={{
                  background: '#0d1117', border: '1px solid #21262d', borderLeft: `3px solid ${sevColor[t.severity] || '#8b949e'}`,
                  borderRadius: 6, padding: '10px 14px', fontSize: 13,
                }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                    <code style={{ color: '#58a6ff', fontSize: 12, background: '#21262d', padding: '1px 6px', borderRadius: 3 }}>{t.id}</code>
                    <span style={{ fontSize: 11, color: sevColor[t.severity], fontWeight: 600 }}>
                      {t.severity} {t.cvss_score ? `· ${t.cvss_score}` : ''}
                    </span>
                    {(t.courses || []).slice(0, 3).map((c: string, j: number) => (
                      <span key={j} style={{ fontSize: 10, background: 'rgba(249,115,22,0.15)', color: '#f97316', padding: '1px 6px', borderRadius: 3 }}>{c}</span>
                    ))}
                  </div>
                  <div style={{ color: '#e6edf3', fontSize: 13, lineHeight: 1.4 }}>{t.summary}</div>
                  {t.tags?.length > 0 && (
                    <div style={{ marginTop: 4, fontSize: 11, color: '#8b949e' }}>
                      {t.tags.slice(0, 5).join(' · ')}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 최근 Labs */}
      {s?.labs?.recent?.length > 0 && (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 20 }}>
          <h3 style={{ fontSize: 17, marginBottom: 14, color: '#e6edf3' }}>최근 활동</h3>
          {s.labs.recent.map((l: any, i: number) => (
            <div key={i} style={{ display: 'flex', gap: 10, padding: '6px 0', borderBottom: '1px solid #21262d', fontSize: 14 }}>
              <span style={{ color: l.status === 'completed' ? '#3fb950' : '#d29922' }}>{l.status === 'completed' ? '✓' : '◌'}</span>
              <span style={{ color: '#e6edf3' }}>{l.lab_id}</span>
              <span style={{ color: '#8b949e', marginLeft: 'auto', fontSize: 13 }}>
                {l.completed_at ? new Date(l.completed_at).toLocaleDateString('ko') : '진행 중'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

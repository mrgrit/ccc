import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

export default function Profile() {
  const [profile, setProfile] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api('/api/profile')
      .then(setProfile)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>
  if (!profile) return <div style={{ color: '#f85149', padding: 40 }}>프로필을 불러올 수 없습니다.</div>

  const s = profile.student || {}
  const creds = profile.credentials || {}
  const infras = profile.infras || []
  const rankHist = profile.rank_history || []

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24, color: '#e6edf3' }}>My Profile</h2>

      {/* 기본 정보 */}
      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 24, marginBottom: 20 }}>
        <h3 style={{ fontSize: 18, color: '#e6edf3', marginBottom: 16 }}>기본 정보</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px 24px', fontSize: 14 }}>
          <div><span style={{ color: '#8b949e' }}>이름:</span> <span style={{ color: '#e6edf3', fontWeight: 600 }}>{s.name}</span></div>
          <div><span style={{ color: '#8b949e' }}>ID:</span> <span style={{ color: '#e6edf3' }}>{s.student_id}</span></div>
          <div><span style={{ color: '#8b949e' }}>역할:</span> <span style={{ color: s.role === 'admin' ? '#f97316' : '#58a6ff', fontWeight: 600 }}>{s.role}</span></div>
          <div><span style={{ color: '#8b949e' }}>랭크:</span> <span style={{ color: '#f97316', fontWeight: 600, textTransform: 'uppercase' as const }}>{s.rank || 'rookie'}</span></div>
          <div><span style={{ color: '#8b949e' }}>블록:</span> <span style={{ color: '#3fb950', fontWeight: 600 }}>{s.total_blocks || 0}</span></div>
          <div><span style={{ color: '#8b949e' }}>그룹:</span> <span style={{ color: '#e6edf3' }}>{s.grp || s.group_id || '-'}</span></div>
          <div><span style={{ color: '#8b949e' }}>가입일:</span> <span style={{ color: '#e6edf3' }}>{s.created_at ? new Date(s.created_at).toLocaleDateString('ko') : '-'}</span></div>
        </div>
      </div>

      {/* 계정 정보 (Credentials) */}
      <div style={{ background: '#161b22', border: `1px solid ${Object.keys(creds).length > 0 ? '#f97316' : '#30363d'}`, borderRadius: 10, padding: 24, marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <h3 style={{ fontSize: 18, color: Object.keys(creds).length > 0 ? '#f97316' : '#e6edf3', margin: 0 }}>서비스 계정 정보</h3>
          <button onClick={async () => {
            try {
              const r = await api('/api/profile/credentials/refresh', { method: 'POST', body: '{}' })
              alert(`재수집 완료: ${(r.refreshed || []).join(', ')}${r.wazuh_pw_found ? '' : ' (Wazuh 비밀번호 추출 실패 — siem VM 확인)'}`)
              location.reload()
            } catch (e: any) {
              try { alert('실패: ' + (JSON.parse(e.message)?.detail || e.message)) } catch { alert('실패: ' + e.message) }
            }
          }} style={{
            background: '#21262d', color: '#58a6ff', border: '1px solid #30363d', borderRadius: 6,
            padding: '6px 14px', fontSize: 13, cursor: 'pointer'
          }}>🔄 재수집</button>
        </div>
        {Object.keys(creds).length === 0 ? (
          <div style={{ fontSize: 13, color: '#8b949e' }}>
            아직 수집된 계정이 없습니다. siem VM 온보딩 후 위 "재수집" 버튼을 눌러주세요.
          </div>
        ) : (
        <>
          <div style={{ fontSize: 13, color: '#8b949e', marginBottom: 12 }}>
            온보딩 시 자동 생성된 계정입니다. 본인과 관리자만 볼 수 있습니다.
          </div>
          <div style={{ display: 'grid', gap: 12 }}>
            {Object.entries(creds).map(([name, cred]: [string, any]) => (
              <div key={name} style={{ background: '#0d1117', border: '1px solid #21262d', borderRadius: 8, padding: 16 }}>
                <div style={{ fontSize: 15, fontWeight: 600, color: '#e6edf3', marginBottom: 8 }}>
                  {name === 'wazuh_dashboard' ? 'Wazuh Dashboard' :
                   name === 'opencti' ? 'OpenCTI' :
                   name === 'wazuh_api' ? 'Wazuh API' : name}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: '4px 12px', fontSize: 13 }}>
                  {cred.url && <><span style={{ color: '#8b949e' }}>URL</span><code style={{ color: '#58a6ff', background: '#21262d', padding: '2px 6px', borderRadius: 4 }}>{cred.url}</code></>}
                  {cred.user && <><span style={{ color: '#8b949e' }}>계정</span><code style={{ color: '#e6edf3', background: '#21262d', padding: '2px 6px', borderRadius: 4 }}>{cred.user}</code></>}
                  {cred.password && <><span style={{ color: '#8b949e' }}>비밀번호</span><PasswordField value={cred.password} /></>}
                </div>
              </div>
            ))}
          </div>
        </>
        )}
      </div>

      {/* 인프라 */}
      {infras.length > 0 && (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 24, marginBottom: 20 }}>
          <h3 style={{ fontSize: 18, color: '#e6edf3', marginBottom: 16 }}>내 인프라</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 10 }}>
            {infras.map((inf: any) => {
              const cfg = inf.vm_config || {}
              const statusColor: Record<string,string> = { healthy: '#3fb950', error: '#f85149', registered: '#d29922' }
              return (
                <div key={inf.id} style={{ background: '#0d1117', border: '1px solid #21262d', borderRadius: 8, padding: 14,
                  borderLeft: `3px solid ${statusColor[inf.status] || '#8b949e'}` }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#e6edf3' }}>{cfg.role || inf.infra_name}</div>
                  <div style={{ fontSize: 12, color: '#8b949e', marginTop: 4 }}>IP: {inf.ip}</div>
                  <div style={{ fontSize: 12, color: statusColor[inf.status] || '#8b949e' }}>{inf.status}</div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 승급 이력 */}
      {rankHist.length > 0 && (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 24 }}>
          <h3 style={{ fontSize: 18, color: '#e6edf3', marginBottom: 16 }}>승급 이력</h3>
          {rankHist.map((h: any, i: number) => (
            <div key={i} style={{ display: 'flex', gap: 12, padding: '6px 0', borderBottom: '1px solid #21262d', fontSize: 13 }}>
              <span style={{ color: '#8b949e', minWidth: 100 }}>{h.created_at ? new Date(h.created_at).toLocaleDateString('ko') : ''}</span>
              <span style={{ color: '#d29922' }}>{h.old_rank}</span>
              <span style={{ color: '#8b949e' }}>→</span>
              <span style={{ color: '#3fb950', fontWeight: 600 }}>{h.new_rank}</span>
              <span style={{ color: '#8b949e', marginLeft: 'auto' }}>{h.reason}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function PasswordField({ value }: { value: string }) {
  const [show, setShow] = useState(false)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <code style={{ color: '#e6edf3', background: '#21262d', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace' }}>
        {show ? value : '••••••••••••'}
      </code>
      <button onClick={() => setShow(!show)} style={{
        background: 'none', border: '1px solid #30363d', borderRadius: 4, color: '#8b949e',
        cursor: 'pointer', fontSize: 11, padding: '2px 8px',
      }}>{show ? '숨기기' : '보기'}</button>
      <button onClick={() => { navigator.clipboard.writeText(value) }} style={{
        background: 'none', border: '1px solid #30363d', borderRadius: 4, color: '#8b949e',
        cursor: 'pointer', fontSize: 11, padding: '2px 8px',
      }}>복사</button>
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'
import { getUser } from '../auth.ts'

export default function MyInfra() {
  const user = getUser()
  const [infras, setInfras] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ infra_name: '', ip: '', subagent_port: '8002' })
  const [checking, setChecking] = useState<string | null>(null)

  const load = () => {
    api(`/api/infras?student_id=${user?.id}`)
      .then(d => setInfras(d.infras || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const addInfra = async () => {
    if (!form.infra_name || !form.ip) return
    try {
      await api('/api/infras', {
        method: 'POST',
        body: JSON.stringify({
          student_id: user?.id,
          infra_name: form.infra_name,
          ip: form.ip,
          subagent_port: parseInt(form.subagent_port) || 8002,
        }),
      })
      setForm({ infra_name: '', ip: '', subagent_port: '8002' })
      setShowAdd(false)
      load()
    } catch (e: any) { alert(e.message) }
  }

  const checkHealth = async (iid: string) => {
    setChecking(iid)
    try {
      const d = await api(`/api/infras/${iid}/health`)
      alert(d.healthy ? 'SubAgent 정상 (healthy)' : 'SubAgent 미응답 (unreachable)')
      load()
    } catch (e: any) { alert('Error: ' + e.message) }
    setChecking(null)
  }

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, color: '#e6edf3' }}>My Infrastructure</h2>
        <button onClick={() => setShowAdd(!showAdd)} style={{
          padding: '8px 20px', borderRadius: 6, border: 'none',
          background: '#f97316', color: '#fff', cursor: 'pointer', fontSize: 15, fontWeight: 600,
        }}>{showAdd ? 'Cancel' : '+ Add Infra'}</button>
      </div>

      {/* 등록 폼 */}
      {showAdd && (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 24, marginBottom: 24 }}>
          <h3 style={{ fontSize: 17, marginBottom: 16, color: '#e6edf3' }}>인프라 등록</h3>
          <p style={{ fontSize: 14, color: '#8b949e', marginBottom: 16 }}>
            실습/대전에 사용할 VM 또는 서버를 등록합니다. SubAgent가 설치되어 있어야 합니다.
          </p>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <input placeholder="인프라 이름 (예: my-kali)" value={form.infra_name}
              onChange={e => setForm({ ...form, infra_name: e.target.value })} style={inputStyle} />
            <input placeholder="IP 주소 (예: 192.168.0.100)" value={form.ip}
              onChange={e => setForm({ ...form, ip: e.target.value })} style={inputStyle} />
            <input placeholder="SubAgent 포트 (기본: 8002)" value={form.subagent_port}
              onChange={e => setForm({ ...form, subagent_port: e.target.value })} style={{ ...inputStyle, width: 160 }} />
            <button onClick={addInfra} style={{
              padding: '12px 24px', borderRadius: 8, border: 'none',
              background: '#238636', color: '#fff', cursor: 'pointer', fontSize: 15, fontWeight: 600,
            }}>Register</button>
          </div>
        </div>
      )}

      {/* 인프라 목록 */}
      {infras.length === 0 ? (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 40, textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 16 }}>🖥️</div>
          <div style={{ fontSize: 17, color: '#e6edf3', marginBottom: 8 }}>등록된 인프라가 없습니다</div>
          <div style={{ fontSize: 14, color: '#8b949e', marginBottom: 16 }}>
            실습과 대전에 참가하려면 먼저 인프라를 등록하세요.<br />
            VM에 SubAgent를 설치하고 IP를 등록하면 됩니다.
          </div>
          <button onClick={() => setShowAdd(true)} style={{
            padding: '10px 24px', borderRadius: 8, border: 'none',
            background: '#f97316', color: '#fff', cursor: 'pointer', fontSize: 15, fontWeight: 600,
          }}>+ 인프라 등록</button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {infras.map(infra => (
            <div key={infra.id} style={{
              background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 20,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <div>
                <div style={{ fontSize: 17, fontWeight: 600, color: '#e6edf3', marginBottom: 4 }}>{infra.infra_name}</div>
                <div style={{ fontSize: 14, color: '#8b949e' }}>
                  <code>{infra.ip}</code> — SubAgent: <code>{infra.subagent_url}</code>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <span style={{
                  padding: '4px 12px', borderRadius: 10, fontSize: 13, fontWeight: 600,
                  background: infra.status === 'healthy' ? '#0d1f0d' : infra.status === 'unreachable' ? '#1f0d0d' : '#1f1a0d',
                  color: infra.status === 'healthy' ? '#3fb950' : infra.status === 'unreachable' ? '#f85149' : '#d29922',
                }}>{infra.status}</span>
                <button onClick={() => checkHealth(infra.id)} disabled={checking === infra.id} style={{
                  padding: '8px 16px', borderRadius: 6, border: '1px solid #30363d',
                  background: '#21262d', color: '#e6edf3', cursor: 'pointer', fontSize: 14,
                }}>{checking === infra.id ? '...' : 'Health Check'}</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 안내 */}
      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 20, marginTop: 24 }}>
        <h3 style={{ fontSize: 16, color: '#e6edf3', marginBottom: 10 }}>SubAgent 설치 방법</h3>
        <div style={{ fontSize: 14, color: '#8b949e', lineHeight: 1.7 }}>
          1. VM에 Python 3.11+ 설치<br />
          2. <code style={{ background: '#21262d', padding: '2px 6px', borderRadius: 4, color: '#d2a8ff' }}>pip install fastapi uvicorn httpx</code><br />
          3. SubAgent 바이너리 다운로드 또는 <code style={{ background: '#21262d', padding: '2px 6px', borderRadius: 4, color: '#d2a8ff' }}>student-setup.sh</code> 실행<br />
          4. <code style={{ background: '#21262d', padding: '2px 6px', borderRadius: 4, color: '#d2a8ff' }}>uvicorn main:app --host 0.0.0.0 --port 8002</code><br />
          5. 위에서 IP와 포트를 등록하면 완료
        </div>
      </div>
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d',
  borderRadius: 8, padding: '12px 16px', fontSize: 15, flex: '1 1 200px',
}

import React, { useState } from 'react'
import { api } from '../api.ts'
import { setAuth } from '../auth.ts'

export default function Login({ onLogin }: { onLogin: () => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [studentId, setStudentId] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [group, setGroup] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        const d = await api('/auth/login', {
          method: 'POST',
          body: JSON.stringify({ student_id: studentId, password }),
        })
        setAuth(d.token, d.user)
        onLogin()
      } else {
        if (!name) { setError('이름을 입력하세요'); setLoading(false); return }
        const d = await api('/auth/register', {
          method: 'POST',
          body: JSON.stringify({ student_id: studentId, password, name, email, group }),
        })
        setAuth(d.token, d.user)
        onLogin()
      }
    } catch (e: any) {
      try { setError(JSON.parse(e.message)?.detail || e.message) } catch { setError(e.message) }
    }
    setLoading(false)
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#0d1117' }}>
      <div style={{ width: 400, background: '#161b22', border: '1px solid #30363d', borderRadius: 12, padding: 36 }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f97316', marginBottom: 6 }}>CCC</h1>
          <div style={{ fontSize: 14, color: '#8b949e' }}>Cyber Combat Commander</div>
        </div>

        <div style={{ display: 'flex', marginBottom: 24, borderRadius: 8, overflow: 'hidden', border: '1px solid #30363d' }}>
          <button onClick={() => setMode('login')} style={{
            flex: 1, padding: '10px 0', border: 'none', cursor: 'pointer', fontSize: 15,
            background: mode === 'login' ? '#f97316' : '#21262d', color: mode === 'login' ? '#fff' : '#8b949e',
          }}>Login</button>
          <button onClick={() => setMode('register')} style={{
            flex: 1, padding: '10px 0', border: 'none', cursor: 'pointer', fontSize: 15,
            background: mode === 'register' ? '#f97316' : '#21262d', color: mode === 'register' ? '#fff' : '#8b949e',
          }}>Register</button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <input placeholder="학번 (Student ID)" value={studentId} onChange={e => setStudentId(e.target.value)} style={inputStyle} />
          {mode === 'register' && <>
            <input placeholder="이름" value={name} onChange={e => setName(e.target.value)} style={inputStyle} />
            <input placeholder="이메일 (선택)" value={email} onChange={e => setEmail(e.target.value)} style={inputStyle} />
            <input placeholder="반/조 (선택)" value={group} onChange={e => setGroup(e.target.value)} style={inputStyle} />
          </>}
          <input placeholder="비밀번호" type="password" value={password} onChange={e => setPassword(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && submit()} style={inputStyle} />
        </div>

        {error && <div style={{ color: '#f85149', fontSize: 14, marginTop: 12 }}>{error}</div>}

        <button onClick={submit} disabled={loading} style={{
          width: '100%', padding: '12px 0', marginTop: 20, borderRadius: 8,
          border: 'none', background: '#f97316', color: '#fff', fontSize: 16, fontWeight: 700, cursor: 'pointer',
        }}>{loading ? '...' : mode === 'login' ? 'Login' : 'Register'}</button>
      </div>
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d',
  borderRadius: 8, padding: '12px 16px', fontSize: 15,
}

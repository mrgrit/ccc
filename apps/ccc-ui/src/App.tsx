import React, { useState, useRef, useCallback } from 'react'
import { Routes, Route, NavLink, Navigate, useNavigate } from 'react-router-dom'
import { isLoggedIn, getUser, clearAuth, isAdmin } from './auth.ts'
import { api } from './api.ts'
import Login from './pages/Login.tsx'
import Dashboard from './pages/Dashboard.tsx'
import Education from './pages/Education.tsx'
import Labs from './pages/Labs.tsx'
import Battle from './pages/Battle.tsx'
import Leaderboard from './pages/Leaderboard.tsx'
import Blockchain from './pages/Blockchain.tsx'
import MyInfra from './pages/MyInfra.tsx'
import Admin from './pages/Admin.tsx'
import Profile from './pages/Profile.tsx'
import ChatBot from './components/ChatBot.tsx'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/training', label: 'Training', icon: '📚' },
  { to: '/labs', label: 'Cyber Range', icon: '🎯' },
  { to: '/my-infra', label: 'My Infra', icon: '🖥️' },
  { to: '/battle', label: 'Battlefield', icon: '⚔️' },
  { to: '/leaderboard', label: 'Leaderboard', icon: '🏆' },
  { to: '/blockchain', label: 'Blockchain', icon: '⛓️' },
  { to: '/admin', label: 'Admin', icon: '⚙️', adminOnly: true },
]

export default function App() {
  const [loggedIn, setLoggedIn] = useState(isLoggedIn())
  const [showPwChange, setShowPwChange] = useState(false)
  const [pwMsg, setPwMsg] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searchOpen, setSearchOpen] = useState(false)
  const searchTimerRef = useRef<any>(null)

  const doSearch = useCallback((q: string) => {
    if (q.length < 2) { setSearchResults([]); return }
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
    searchTimerRef.current = setTimeout(async () => {
      try {
        const d = await api(`/search?q=${encodeURIComponent(q)}&limit=20`)
        setSearchResults(d.results || [])
      } catch { setSearchResults([]) }
    }, 300)
  }, [])
  const curPwRef = useRef<HTMLInputElement>(null)
  const newPwRef = useRef<HTMLInputElement>(null)
  const user = getUser()

  const changePassword = async () => {
    const cur = curPwRef.current?.value || ''
    const nw = newPwRef.current?.value || ''
    if (!cur || !nw) { setPwMsg('비밀번호를 입력하세요'); return }
    if (nw.length < 4) { setPwMsg('새 비밀번호는 4자 이상'); return }
    try {
      await api('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({ current_password: cur, new_password: nw }),
      })
      setPwMsg('변경 완료')
      setTimeout(() => { setShowPwChange(false); setPwMsg('') }, 1500)
    } catch (e: any) {
      try { setPwMsg(JSON.parse(e.message)?.detail || '변경 실패') } catch { setPwMsg('변경 실패') }
    }
  }

  if (!loggedIn) {
    return <Login onLogin={() => setLoggedIn(true)} />
  }

  const logout = () => { clearAuth(); setLoggedIn(false) }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <nav style={{
        width: 220, background: '#161b22', borderRight: '1px solid #30363d',
        padding: '20px 0', display: 'flex', flexDirection: 'column',
      }}>
        <div style={{ padding: '0 20px 24px', borderBottom: '1px solid #30363d' }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: '#f97316' }}>CCC</h1>
          <div style={{ fontSize: 11, color: '#8b949e', marginTop: 4 }}>Cyber Combat Commander</div>
        </div>
        {/* 검색 */}
        <div style={{ padding: '12px 16px', position: 'relative' }}>
          <input
            type="text"
            placeholder="검색..."
            value={searchQuery}
            onChange={e => { setSearchQuery(e.target.value); doSearch(e.target.value); setSearchOpen(true) }}
            onFocus={() => searchQuery.length >= 2 && setSearchOpen(true)}
            style={{
              width: '100%', background: '#0d1117', color: '#e6edf3',
              border: '1px solid #30363d', borderRadius: 6, padding: '8px 12px',
              fontSize: 13, outline: 'none',
            }}
          />
          {searchOpen && searchResults.length > 0 && (
            <div style={{
              position: 'absolute', left: 8, right: 8, top: 48, zIndex: 100,
              background: '#161b22', border: '1px solid #30363d', borderRadius: 8,
              maxHeight: 400, overflowY: 'auto', boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            }}>
              <div style={{ padding: '8px 12px', fontSize: 11, color: '#8b949e', borderBottom: '1px solid #21262d' }}>
                {searchResults.length}건 검색됨
              </div>
              {searchResults.map((r: any, i: number) => (
                <a key={i} href={r.link} onClick={() => { setSearchOpen(false); setSearchQuery('') }}
                  style={{
                    display: 'block', padding: '8px 12px', textDecoration: 'none',
                    borderBottom: '1px solid #21262d', cursor: 'pointer',
                  }}
                  onMouseOver={e => (e.currentTarget.style.background = '#1f2937')}
                  onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 2 }}>
                    <span style={{
                      fontSize: 10, padding: '1px 6px', borderRadius: 4,
                      background: r.type === 'lecture' ? '#21262d' : r.type === 'lab_ai' ? 'rgba(249,115,22,0.15)' : 'rgba(88,166,255,0.15)',
                      color: r.type === 'lecture' ? '#8b949e' : r.type === 'lab_ai' ? '#f97316' : '#58a6ff',
                    }}>
                      {r.type === 'lecture' ? 'Lecture' : r.type === 'lab_ai' ? 'AI Lab' : 'Non-AI Lab'}
                    </span>
                    <span style={{ fontSize: 11, color: '#8b949e' }}>W{r.week}</span>
                  </div>
                  <div style={{ fontSize: 13, color: '#e6edf3', fontWeight: 600 }}>{r.title}</div>
                  <div style={{ fontSize: 11, color: '#8b949e', marginTop: 2 }}>{r.context}</div>
                </a>
              ))}
            </div>
          )}
        </div>
        <div style={{ flex: 1 }}>
          {navItems.filter(n => !(n as any).adminOnly || isAdmin()).map(n => (
            <NavLink key={n.to} to={n.to} style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 20px', color: isActive ? '#f97316' : '#8b949e',
              background: isActive ? '#1f2937' : 'transparent',
              textDecoration: 'none', fontSize: 14,
              borderLeft: isActive ? '3px solid #f97316' : '3px solid transparent',
            })}>
              <span>{n.icon}</span><span>{n.label}</span>
            </NavLink>
          ))}
        </div>
        {/* 사용자 정보 */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid #30363d' }}>
          <NavLink to="/profile" style={{ fontSize: 14, color: '#e6edf3', fontWeight: 600, textDecoration: 'none' }}>
            {user?.name || 'User'}
          </NavLink>
          <div style={{ fontSize: 12, color: '#8b949e' }}>{user?.student_id} {user?.role === 'admin' && '(Admin)'}</div>
          <button onClick={() => setShowPwChange(!showPwChange)} style={{
            marginTop: 8, width: '100%', padding: '6px 0', borderRadius: 6,
            background: '#21262d', color: '#8b949e', border: '1px solid #30363d',
            cursor: 'pointer', fontSize: 13,
          }}>비밀번호 변경</button>
          {showPwChange && (
            <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
              <input ref={curPwRef} type="password" placeholder="현재 비밀번호" style={{
                background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d',
                borderRadius: 6, padding: '6px 10px', fontSize: 12,
              }} />
              <input ref={newPwRef} type="password" placeholder="새 비밀번호" style={{
                background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d',
                borderRadius: 6, padding: '6px 10px', fontSize: 12,
              }} onKeyDown={e => e.key === 'Enter' && changePassword()} />
              <button onClick={changePassword} style={{
                padding: '5px 0', borderRadius: 6, border: 'none',
                background: '#f97316', color: '#fff', fontSize: 12, cursor: 'pointer',
              }}>변경</button>
              {pwMsg && <div style={{ fontSize: 11, color: pwMsg === '변경 완료' ? '#3fb950' : '#f85149' }}>{pwMsg}</div>}
            </div>
          )}
          <button onClick={logout} style={{
            marginTop: 6, width: '100%', padding: '6px 0', borderRadius: 6,
            background: '#21262d', color: '#8b949e', border: '1px solid #30363d',
            cursor: 'pointer', fontSize: 13,
          }}>Logout</button>
        </div>
      </nav>
      <main style={{ flex: 1, padding: 32, overflow: 'auto' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/training" element={<Education />} />
          <Route path="/labs" element={<Labs />} />
          <Route path="/my-infra" element={<MyInfra />} />
          <Route path="/battle" element={<Battle />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/blockchain" element={<Blockchain />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
        </div>
      </main>
      <ChatBot />
    </div>
  )
}

import React, { useState, useRef } from 'react'
import { Routes, Route, NavLink, Navigate, useLocation } from 'react-router-dom'
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
import Knowledge from './pages/Knowledge.tsx'
import Profile from './pages/Profile.tsx'
import ChatBot from './components/ChatBot.tsx'
import Search from './pages/Search.tsx'
import Papers from './pages/Papers.tsx'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/training', label: 'Training', icon: '📚' },
  { to: '/labs', label: 'Cyber Range', icon: '🎯' },
  { to: '/my-infra', label: 'My Infra', icon: '🖥️' },
  { to: '/battle', label: 'Battlefield', icon: '⚔️' },
  { to: '/leaderboard', label: 'Leaderboard', icon: '🏆' },
  { to: '/blockchain', label: 'Blockchain', icon: '⛓️' },
  { to: '/papers', label: 'Papers', icon: '📚', adminOnly: true },
  { to: '/knowledge', label: 'Knowledge', icon: '🧠', adminOnly: true },
  { to: '/admin', label: 'Admin', icon: '⚙️', adminOnly: true },
]

export default function App() {
  const location = useLocation()
  const isFullscreen = location.pathname.startsWith('/knowledge')  // 풀스크린 페이지 (flex 가변)
  const [loggedIn, setLoggedIn] = useState(isLoggedIn())
  const [showPwChange, setShowPwChange] = useState(false)
  const [pwMsg, setPwMsg] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
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
        {/* 검색 — 클릭/엔터 시 검색 페이지로 이동 */}
        <div style={{ padding: '12px 16px' }}>
          <div style={{ display: 'flex', gap: 4 }}>
            <input
              type="text"
              placeholder="검색..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && searchQuery.length >= 2) { window.location.href = `/app/search?q=${encodeURIComponent(searchQuery)}`; } }}
              style={{
                flex: 1, background: '#0d1117', color: '#e6edf3',
                border: '1px solid #30363d', borderRadius: 6, padding: '8px 10px',
                fontSize: 13, outline: 'none',
              }}
            />
            <button onClick={() => { if (searchQuery.length >= 2) window.location.href = `/app/search?q=${encodeURIComponent(searchQuery)}` }} style={{
              background: '#21262d', border: '1px solid #30363d', borderRadius: 6,
              color: '#8b949e', padding: '4px 8px', cursor: 'pointer', fontSize: 14,
            }}>🔍</button>
          </div>
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
      <main style={{
        flex: 1,
        padding: isFullscreen ? 0 : 32,
        overflow: isFullscreen ? 'hidden' : 'auto',
        display: isFullscreen ? 'flex' : 'block',
        flexDirection: 'column',
        minWidth: 0,
        minHeight: 0,
      }}>
        <div style={isFullscreen
          ? { flex: 1, minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }
          : { maxWidth: 1100, margin: '0 auto' }}>
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
          <Route path="/knowledge" element={<Knowledge />} />
          <Route path="/papers" element={<Papers />} />
          <Route path="/search" element={<Search />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
        </div>
      </main>
      <ChatBot />
    </div>
  )
}

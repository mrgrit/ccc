import React from 'react'
import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard.tsx'
import Education from './pages/Education.tsx'
import Labs from './pages/Labs.tsx'
import Battle from './pages/Battle.tsx'
import Leaderboard from './pages/Leaderboard.tsx'
import Blockchain from './pages/Blockchain.tsx'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/education', label: 'Education', icon: '📚' },
  { to: '/labs', label: 'Labs', icon: '🔬' },
  { to: '/battle', label: 'Battle', icon: '⚔️' },
  { to: '/leaderboard', label: 'Leaderboard', icon: '🏆' },
  { to: '/blockchain', label: 'Blockchain', icon: '⛓️' },
]

export default function App() {
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
        <div style={{ marginTop: 16, flex: 1 }}>
          {navItems.map(n => (
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
        <div style={{ padding: '12px 20px', fontSize: 11, color: '#484f58', borderTop: '1px solid #30363d' }}>
          v0.1.0 — :9100
        </div>
      </nav>
      <main style={{ flex: 1, padding: 32, overflow: 'auto' }}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/education" element={<Education />} />
          <Route path="/labs" element={<Labs />} />
          <Route path="/battle" element={<Battle />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/blockchain" element={<Blockchain />} />
        </Routes>
      </main>
    </div>
  )
}

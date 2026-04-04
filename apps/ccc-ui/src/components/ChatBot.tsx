import React, { useState, useRef, useEffect } from 'react'
import { api } from '../api.ts'
import { getUser } from '../auth.ts'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatBot() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '안녕하세요! CCC AI 튜터입니다. 사용법이나 학습 내용에 대해 질문하세요.' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const user = getUser()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    if (!input.trim() || loading) return
    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)

    try {
      const d = await api('/api/chat', {
        method: 'POST',
        body: JSON.stringify({
          message: userMsg,
          context: { page: window.location.pathname, user_name: user?.name, rank: user?.rank },
        }),
      })
      setMessages(prev => [...prev, { role: 'assistant', content: d.reply || '응답을 생성할 수 없습니다.' }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'AI 서버 연결 실패. 잠시 후 다시 시도하세요.' }])
    }
    setLoading(false)
  }

  return (
    <>
      {/* 플로팅 버튼 */}
      {!open && (
        <button onClick={() => setOpen(true)} style={{
          position: 'fixed', bottom: 24, right: 24, width: 56, height: 56,
          borderRadius: '50%', background: '#f97316', color: '#fff', border: 'none',
          fontSize: 24, cursor: 'pointer', boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>💬</button>
      )}

      {/* 챗 창 */}
      {open && (
        <div style={{
          position: 'fixed', bottom: 24, right: 24, width: 380, height: 520,
          background: '#161b22', border: '1px solid #30363d', borderRadius: 12,
          display: 'flex', flexDirection: 'column', zIndex: 1000,
          boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        }}>
          {/* 헤더 */}
          <div style={{
            padding: '14px 18px', borderBottom: '1px solid #30363d',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div>
              <span style={{ fontSize: 16, fontWeight: 700, color: '#f97316' }}>AI Tutor</span>
              <span style={{ fontSize: 12, color: '#8b949e', marginLeft: 8 }}>CCC</span>
            </div>
            <button onClick={() => setOpen(false)} style={{
              background: 'none', border: 'none', color: '#8b949e', fontSize: 18, cursor: 'pointer',
            }}>✕</button>
          </div>

          {/* 메시지 */}
          <div style={{ flex: 1, overflow: 'auto', padding: '12px 16px' }}>
            {messages.map((m, i) => (
              <div key={i} style={{
                marginBottom: 12, display: 'flex',
                justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
              }}>
                <div style={{
                  maxWidth: '80%', padding: '10px 14px', borderRadius: 12, fontSize: 14, lineHeight: 1.6,
                  background: m.role === 'user' ? '#f97316' : '#21262d',
                  color: m.role === 'user' ? '#fff' : '#e6edf3',
                }}>
                  {m.content}
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 12 }}>
                <div style={{ padding: '10px 14px', borderRadius: 12, background: '#21262d', color: '#8b949e', fontSize: 14 }}>
                  생각 중...
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* 입력 */}
          <div style={{ padding: '12px 16px', borderTop: '1px solid #30363d', display: 'flex', gap: 8 }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send()}
              placeholder="질문을 입력하세요..."
              style={{
                flex: 1, background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d',
                borderRadius: 8, padding: '10px 14px', fontSize: 14,
              }}
            />
            <button onClick={send} disabled={loading} style={{
              padding: '10px 16px', borderRadius: 8, border: 'none',
              background: '#f97316', color: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 600,
            }}>Send</button>
          </div>
        </div>
      )}
    </>
  )
}

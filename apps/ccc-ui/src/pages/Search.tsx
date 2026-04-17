import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api.ts'

const typeStyle: Record<string, { bg: string; color: string; label: string }> = {
  lecture: { bg: '#21262d', color: '#e6edf3', label: 'Lecture' },
  lab_ai: { bg: 'rgba(249,115,22,0.15)', color: '#f97316', label: 'AI Lab' },
  lab_nonai: { bg: 'rgba(88,166,255,0.15)', color: '#58a6ff', label: 'Non-AI Lab' },
}

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams()
  const q = searchParams.get('q') || ''
  const [query, setQuery] = useState(q)
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)

  const doSearch = async (keyword: string) => {
    if (keyword.length < 2) { setResults([]); setTotal(0); return }
    setLoading(true)
    try {
      const d = await api(`/api/search?q=${encodeURIComponent(keyword)}&limit=100`)
      setResults(d.results || [])
      setTotal(d.total || 0)
    } catch { setResults([]) }
    setLoading(false)
  }

  useEffect(() => {
    if (q) { setQuery(q); doSearch(q) }
  }, [q])

  const handleSearch = () => {
    if (query.length >= 2) {
      setSearchParams({ q: query })
      doSearch(query)
    }
  }

  // 결과를 과목별로 그룹핑
  const grouped: Record<string, any[]> = {}
  results.forEach(r => {
    const key = r.course || 'other'
    if (!grouped[key]) grouped[key] = []
    grouped[key].push(r)
  })

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, color: '#e6edf3', marginBottom: 16 }}>콘텐츠 검색</h2>

      {/* 검색 바 */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          placeholder="키워드를 입력하세요 (예: nftables, SQL Injection, Wazuh ...)"
          autoFocus
          style={{
            flex: 1, background: '#0d1117', color: '#e6edf3',
            border: '1px solid #30363d', borderRadius: 8, padding: '12px 16px',
            fontSize: 16, outline: 'none',
          }}
        />
        <button onClick={handleSearch} style={{
          background: '#f97316', color: '#fff', border: 'none', borderRadius: 8,
          padding: '12px 24px', cursor: 'pointer', fontSize: 16, fontWeight: 700,
        }}>검색</button>
      </div>

      {/* 결과 헤더 */}
      {total > 0 && (
        <div style={{ color: '#8b949e', fontSize: 14, marginBottom: 16 }}>
          <strong style={{ color: '#f97316' }}>{total}</strong>건의 결과가 발견되었습니다
          {total > 100 && ' (상위 100건 표시)'}
        </div>
      )}
      {loading && <div style={{ color: '#8b949e', padding: 20 }}>검색 중...</div>}

      {/* 결과 — 과목별 그룹 */}
      {Object.entries(grouped).map(([course, items]) => (
        <div key={course} style={{ marginBottom: 24 }}>
          <div style={{
            fontSize: 15, fontWeight: 700, color: '#8b949e', padding: '8px 0',
            borderBottom: '1px solid #21262d', marginBottom: 8,
          }}>
            {course} ({items.length}건)
          </div>
          {items.map((r: any, i: number) => {
            const ts = typeStyle[r.type] || typeStyle.lecture
            return (
              <a key={i} href={r.link} style={{
                display: 'block', background: '#161b22', border: '1px solid #30363d',
                borderRadius: 8, padding: '14px 18px', marginBottom: 8,
                textDecoration: 'none', transition: 'border-color 0.15s',
              }}
                onMouseOver={e => (e.currentTarget.style.borderColor = '#58a6ff')}
                onMouseOut={e => (e.currentTarget.style.borderColor = '#30363d')}
              >
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                  <span style={{
                    fontSize: 11, padding: '2px 8px', borderRadius: 10,
                    background: ts.bg, color: ts.color, fontWeight: 600,
                  }}>{ts.label}</span>
                  <span style={{ fontSize: 12, color: '#8b949e' }}>Week {r.week}</span>
                </div>
                <div style={{ fontSize: 16, color: '#e6edf3', fontWeight: 600, marginBottom: 4 }}>
                  {r.title}
                </div>
                <div style={{ fontSize: 13, color: '#8b949e', lineHeight: 1.5 }}>
                  {highlightQuery(r.context, query)}
                </div>
              </a>
            )
          })}
        </div>
      ))}

      {/* 결과 없음 */}
      {!loading && query.length >= 2 && results.length === 0 && (
        <div style={{
          textAlign: 'center', padding: 60, color: '#8b949e', fontSize: 15,
        }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🔍</div>
          "{query}"에 대한 검색 결과가 없습니다.
          <div style={{ marginTop: 8, fontSize: 13 }}>
            다른 키워드로 시도해 보세요. (예: Suricata, WAF, 방화벽, 탈옥)
          </div>
        </div>
      )}
    </div>
  )
}

function highlightQuery(text: string, query: string): React.ReactNode {
  if (!query || query.length < 2) return text
  const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'))
  return parts.map((part, i) =>
    part.toLowerCase() === query.toLowerCase()
      ? <mark key={i} style={{ background: '#f9731640', color: '#f97316', padding: '0 2px', borderRadius: 2 }}>{part}</mark>
      : part
  )
}

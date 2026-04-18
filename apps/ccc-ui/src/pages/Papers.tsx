import React, { useEffect, useState, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api.ts'
import { isAdmin } from '../auth.ts'
import { markdownToHtml, MARKDOWN_CSS, MARKDOWN_CLASS } from '../markdown.ts'
import mermaid from 'mermaid'

mermaid.initialize({ startOnLoad: false, theme: 'dark', themeVariables: {
  primaryColor: '#21262d', primaryTextColor: '#e6edf3', lineColor: '#30363d',
  secondaryColor: '#161b22', tertiaryColor: '#0d1117',
}})

type PaperFile = { path: string; size: number; mtime: number }
type Paper = { id: string; files: PaperFile[] }

export default function Papers() {
  const [params, setParams] = useSearchParams()
  const [papers, setPapers] = useState<Paper[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [content, setContent] = useState<string>('')
  const [loadingContent, setLoadingContent] = useState(false)
  const contentRef = useRef<HTMLDivElement>(null)

  const paperId = params.get('paper') || ''
  const filePath = params.get('file') || ''

  useEffect(() => {
    if (!isAdmin()) { setLoading(false); return }
    api('/api/papers')
      .then(d => setPapers(d.papers || []))
      .catch(e => setError(e.message || '로드 실패'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!paperId || !filePath) { setContent(''); return }
    setLoadingContent(true)
    api(`/api/papers/${encodeURIComponent(paperId)}/${filePath.split('/').map(encodeURIComponent).join('/')}`)
      .then(d => setContent(d.content || ''))
      .catch(e => setError(e.message || '파일 로드 실패'))
      .finally(() => setLoadingContent(false))
  }, [paperId, filePath])

  useEffect(() => {
    if (contentRef.current) {
      const els = contentRef.current.querySelectorAll('.mermaid')
      if (els.length > 0) mermaid.run({ nodes: els as any }).catch(() => {})
    }
  }, [content])

  if (!isAdmin()) {
    return <div style={{ color: '#f85149', padding: 40, fontSize: 15 }}>관리자 전용 페이지입니다.</div>
  }
  if (loading) return <div style={{ color: '#8b949e', padding: 40, fontSize: 15 }}>Loading papers…</div>
  if (error) return <div style={{ color: '#f85149', padding: 40 }}>{error}</div>

  const selectedPaper = papers.find(p => p.id === paperId) || null
  const isMarkdown = /\.md$/i.test(filePath)

  // 파일 상세 뷰
  if (selectedPaper && filePath) {
    return (
      <div>
        <style>{MARKDOWN_CSS}</style>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
          <button onClick={() => setParams({ paper: paperId })} style={backBtn}>← 파일 목록</button>
          <button onClick={() => setParams({})} style={backBtn}>← 논문 목록</button>
          <span style={{ fontSize: 14, color: '#8b949e' }}>📄 papers / <span style={{ color: '#f97316' }}>{paperId}</span> / {filePath}</span>
        </div>
        {loadingContent ? (
          <div style={{ color: '#8b949e', padding: 40 }}>Loading…</div>
        ) : isMarkdown ? (
          <div
            className={MARKDOWN_CLASS}
            ref={contentRef}
            style={{
              background: '#161b22', border: '1px solid #30363d', borderRadius: 10,
              padding: '32px 36px', fontSize: 16, color: '#c9d1d9', lineHeight: 1.7, maxWidth: 900,
            }}
            dangerouslySetInnerHTML={{ __html: markdownToHtml(content) }}
          />
        ) : (
          <pre style={{
            background: '#0d1117', border: '1px solid #30363d', borderRadius: 8,
            padding: '16px 20px', color: '#e6edf3', fontSize: 13, lineHeight: 1.55,
            overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            fontFamily: "'D2Coding',Consolas,Monaco,monospace",
          }}>{content}</pre>
        )}
      </div>
    )
  }

  // 특정 논문의 파일 목록
  if (selectedPaper) {
    return (
      <div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 20 }}>
          <button onClick={() => setParams({})} style={backBtn}>← 논문 목록</button>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: '#e6edf3' }}>📄 {selectedPaper.id}</h2>
          <span style={{ fontSize: 13, color: '#8b949e' }}>{selectedPaper.files.length} files</span>
        </div>
        {selectedPaper.files.length === 0 ? (
          <div style={{ color: '#8b949e', fontSize: 14 }}>파일이 없습니다. <code style={{ color: '#f97316' }}>contents/papers/{selectedPaper.id}/</code> 에 마크다운 파일을 추가하세요.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {selectedPaper.files.map(f => (
              <button
                key={f.path}
                onClick={() => setParams({ paper: selectedPaper.id, file: f.path })}
                style={{
                  textAlign: 'left', background: '#161b22', border: '1px solid #30363d',
                  borderRadius: 8, padding: '14px 18px', cursor: 'pointer',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12,
                }}
              >
                <span style={{ color: '#e6edf3', fontSize: 15, fontWeight: 500 }}>
                  <span style={{ color: '#f97316', marginRight: 8 }}>{/\.md$/i.test(f.path) ? '📝' : '📄'}</span>
                  {f.path}
                </span>
                <span style={{ fontSize: 12, color: '#8b949e' }}>
                  {formatSize(f.size)} · {new Date(f.mtime * 1000).toLocaleDateString()}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    )
  }

  // 논문 목록
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 20 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: '#e6edf3' }}>📚 Papers (Admin)</h2>
        <span style={{ fontSize: 12, color: '#8b949e' }}>
          <code style={{ color: '#f97316' }}>contents/papers/</code> · git-ignored
        </span>
      </div>
      {papers.length === 0 ? (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 24, color: '#8b949e', fontSize: 14 }}>
          <div>등록된 논문이 없습니다.</div>
          <div style={{ marginTop: 10, fontSize: 13 }}>
            <code style={{ color: '#f97316' }}>contents/papers/&lt;논문명&gt;/</code> 디렉토리를 만들고 <code style={{ color: '#f97316' }}>.md</code> 파일을 추가하면 여기에 표시됩니다.
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
          {papers.map(p => (
            <button
              key={p.id}
              onClick={() => setParams({ paper: p.id })}
              style={{
                textAlign: 'left', background: '#161b22', border: '1px solid #30363d',
                borderRadius: 10, padding: 18, cursor: 'pointer',
              }}
            >
              <div style={{ fontSize: 17, fontWeight: 600, color: '#f97316', marginBottom: 8 }}>📄 {p.id}</div>
              <div style={{ fontSize: 13, color: '#8b949e' }}>{p.files.length} files</div>
              {p.files.slice(0, 3).map(f => (
                <div key={f.path} style={{ fontSize: 12, color: '#c9d1d9', marginTop: 4 }}>· {f.path}</div>
              ))}
              {p.files.length > 3 && <div style={{ fontSize: 12, color: '#8b949e', marginTop: 4 }}>… +{p.files.length - 3}</div>}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

const backBtn: React.CSSProperties = {
  background: '#21262d', color: '#8b949e', border: '1px solid #30363d',
  borderRadius: 6, padding: '7px 14px', cursor: 'pointer', fontSize: 14,
}

function formatSize(n: number): string {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

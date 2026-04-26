import React, { useEffect, useRef, useState, useMemo } from 'react'
import cytoscape from 'cytoscape'
// @ts-ignore — cose-bilkent 는 .d.ts 없음
import coseBilkent from 'cytoscape-cose-bilkent'
import { api } from '../api.ts'

cytoscape.use(coseBilkent)

const NODE_COLORS: Record<string, string> = {
  // Operational tier
  Playbook:   '#f97316',
  Experience: '#58a6ff',
  Skill:      '#3fb950',
  Error:      '#f85149',
  Recovery:   '#7ee787',
  Concept:    '#bc8cff',
  Insight:    '#d29922',
  // History layer (operational 시계열)
  Narrative:  '#79c0ff',
  Anchor:     '#ffa657',
  // Asset domain
  Asset:        '#8b949e',
  // Work domain — Strategic
  Mission:    '#ff7b72',
  Vision:     '#d29922',
  Goal:       '#a371f7',
  Strategy:   '#bc8cff',
  KPI:        '#3fb950',
  // Work domain — Tactical
  Plan:       '#58a6ff',
  Todo:       '#7ee787',
}

const TYPES_OPERATIONAL = ['Playbook','Experience','Skill','Error','Recovery','Concept','Insight','Narrative','Anchor']
const TYPES_ASSET = ['Asset']
const TYPES_WORK = ['Mission','Vision','Goal','Strategy','KPI','Plan','Todo']
const ALL_TYPES = [...TYPES_OPERATIONAL, ...TYPES_ASSET, ...TYPES_WORK]

const DOMAINS: Record<string, string[]> = {
  '전체': ALL_TYPES,
  'Asset': TYPES_ASSET,
  'Architecture': TYPES_ASSET,  // 같은 노드, edge 종류로 view 차별화
  'Work': TYPES_WORK,
  'Operational (PE-KG-H)': TYPES_OPERATIONAL,
}

type Node = {
  id: string
  type: string
  name: string
  meta?: any
  updated_at?: string
}
type Edge = {
  id: number
  src: string
  dst: string
  type: string
  weight: number
}

export default function Knowledge() {
  const cyContainer = useRef<HTMLDivElement>(null)
  const cyRef = useRef<any>(null)

  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [stats, setStats] = useState<any>({})
  const [loading, setLoading] = useState(true)
  const [enabledTypes, setEnabledTypes] = useState<Set<string>>(new Set(ALL_TYPES))
  const [domain, setDomain] = useState<string>('전체')
  const switchDomain = (d: string) => {
    setDomain(d)
    setEnabledTypes(new Set(DOMAINS[d] || ALL_TYPES))
  }
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<any>(null)
  const [searchQ, setSearchQ] = useState('')
  const [searchResults, setSearchResults] = useState<Node[]>([])
  const [showLeft, setShowLeft] = useState(true)
  const [showDetail, setShowDetail] = useState(true)

  // 패널 토글 시 graph resize/fit
  useEffect(() => {
    const t = setTimeout(() => {
      if (cyRef.current) {
        try { cyRef.current.resize(); cyRef.current.fit(undefined, 40) } catch {}
      }
    }, 50)
    return () => clearTimeout(t)
  }, [showLeft, showDetail])

  // 데이터 로드
  const load = async () => {
    setLoading(true)
    try {
      const [n, e, s, h] = await Promise.all([
        api('/api/graph/nodes?limit=1000').then(d => d.nodes || []),
        api('/api/graph/edges').then(d => d.edges || []),
        api('/api/graph/stats').catch(() => ({})),
        api('/api/history/graph-view?limit=200').catch(() => ({ nodes: [], edges: [] })),
      ])
      const histNodes = h.nodes || []
      const histEdges = (h.edges || []).map((edge: any, i: number) => ({
        ...edge, id: 1_000_000 + i, // KG edge id 와 충돌 방지
      }))
      // History node count 를 stats 에 합산
      const hStats = { ...(s || {}) }
      hStats.node_counts = hStats.node_counts || {}
      hStats.node_counts.Narrative = histNodes.filter((x: any) => x.type === 'Narrative').length
      hStats.node_counts.Anchor    = histNodes.filter((x: any) => x.type === 'Anchor').length
      setNodes([...n, ...histNodes])
      setEdges([...e, ...histEdges])
      setStats(hStats)
    } catch (err: any) {
      alert('Knowledge graph 로드 실패: ' + err.message)
    } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  // Asset / Narrative 선택 시 timeline 추가 로드
  const [timeline, setTimeline] = useState<any>(null)
  useEffect(() => {
    setTimeline(null)
    if (!selectedId || !detail?.node) return
    const t = detail.node.type
    if (t === 'Asset') {
      api(`/api/history/asset-timeline/${encodeURIComponent(detail.node.name || selectedId)}`)
        .then(d => setTimeline(d)).catch(() => setTimeline({ events: [] }))
    } else if (t === 'Narrative') {
      api(`/api/history/events?narrative_id=${encodeURIComponent(selectedId)}&limit=100`)
        .then(d => setTimeline({ events: d.events || [] })).catch(() => setTimeline({ events: [] }))
    }
  }, [selectedId, detail])

  // 그래프 렌더
  const filteredNodes = useMemo(
    () => nodes.filter(n => enabledTypes.has(n.type)),
    [nodes, enabledTypes]
  )
  const filteredEdges = useMemo(() => {
    const ids = new Set(filteredNodes.map(n => n.id))
    return edges.filter(e => ids.has(e.src) && ids.has(e.dst))
  }, [filteredNodes, edges])

  useEffect(() => {
    if (!cyContainer.current) return
    if (cyRef.current) cyRef.current.destroy()

    const elements = [
      ...filteredNodes.map(n => ({
        data: { id: n.id, label: n.name, type: n.type, meta: n.meta || {} }
      })),
      ...filteredEdges.map(e => ({
        data: { id: `e${e.id}`, source: e.src, target: e.dst, type: e.type, weight: e.weight }
      })),
    ]

    const cy = cytoscape({
      container: cyContainer.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (ele: any) => NODE_COLORS[ele.data('type')] || '#8b949e',
            'label': 'data(label)',
            'color': '#e6edf3',
            'font-size': 13,
            'font-weight': 'bold',
            'text-outline-color': '#0d1117',
            'text-outline-width': 3,
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 6,
            // 노드 크기: 25(min) ~ 90(max), degree(연결도) 비례
            'width': (ele: any) => Math.max(25, Math.min(90, 25 + (ele.degree() || 0) * 5)),
            'height': (ele: any) => Math.max(25, Math.min(90, 25 + (ele.degree() || 0) * 5)),
            'border-width': 2,
            'border-color': '#161b22',
            'text-wrap': 'wrap',
            'text-max-width': '160px',
            'min-zoomed-font-size': 8,  // 줌 아웃 시 라벨 자동 숨김
          } as any,
        },
        {
          selector: 'edge',
          style: {
            'width': (ele: any) => Math.max(1.2, Math.min(5, 1 + (ele.data('weight') || 1) * 0.7)),
            'line-color': '#30363d',
            'target-arrow-color': '#30363d',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 1.2,
            'opacity': 0.45,
          } as any,
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#f97316',
            'border-width': 4,
            'font-size': 16,
          } as any,
        },
        {
          selector: 'node.highlighted',
          style: {
            'border-color': '#f97316',
            'border-width': 3,
          } as any,
        },
        {
          selector: 'edge.highlighted',
          style: {
            'line-color': '#f97316',
            'target-arrow-color': '#f97316',
            'opacity': 0.9,
            'width': 3,
          } as any,
        },
        {
          selector: '.faded',
          style: {
            'opacity': 0.08,
            'text-opacity': 0,
          } as any,
        },
      ],
      // Obsidian 스타일 force layout — 둥글게 클러스터링, 한 줄 stretching 방지
      layout: {
        name: 'cose-bilkent',
        animate: 'end',
        animationDuration: 1000,
        randomize: true,                  // 한 줄로 길어지는 현상 방지
        idealEdgeLength: 140,
        nodeRepulsion: 14000,
        edgeElasticity: 0.45,
        nestingFactor: 0.1,
        gravity: 0.5,
        gravityRangeCompound: 1.5,
        gravityCompound: 1.0,
        gravityRange: 3.8,
        numIter: 2500,
        tile: true,
        tilingPaddingVertical: 20,
        tilingPaddingHorizontal: 20,
        packComponents: true,             // 끊긴 component 도 한 화면에 보기 좋게
      } as any,
      wheelSensitivity: 0.3,
      minZoom: 0.1,
      maxZoom: 4,
    })

    // 초기 fit (줌 자동 조정 — 화면 가득 채움)
    cy.ready(() => {
      try {
        cy.fit(undefined, 40)
      } catch {}
    })

    cy.on('tap', 'node', (evt: any) => {
      const id = evt.target.id()
      setSelectedId(id)
      // Obsidian 스타일: 인접만 강조, 나머지는 fade
      cy.elements().removeClass('highlighted')
      cy.elements().addClass('faded')
      const neighborhood = evt.target.closedNeighborhood()
      neighborhood.removeClass('faded')
      neighborhood.addClass('highlighted')
    })
    cy.on('tap', (evt: any) => {
      if (evt.target === cy) {
        cy.elements().removeClass('faded')
        cy.elements().removeClass('highlighted')
        setSelectedId(null)
      }
    })

    cyRef.current = cy
    return () => { try { cy.destroy() } catch {} }
  }, [filteredNodes, filteredEdges])

  // 노드 detail 로드
  useEffect(() => {
    if (!selectedId) { setDetail(null); return }
    api(`/api/graph/node/${encodeURIComponent(selectedId)}`)
      .then(setDetail)
      .catch(e => setDetail({ error: e.message }))
  }, [selectedId])

  // 검색
  const doSearch = async () => {
    if (!searchQ.trim()) { setSearchResults([]); return }
    try {
      const d = await api(`/api/graph/search?q=${encodeURIComponent(searchQ)}&limit=20`)
      setSearchResults(d.results || [])
    } catch (e: any) { alert(e.message) }
  }
  const focusNode = (id: string) => {
    setSelectedId(id)
    if (cyRef.current) {
      const n = cyRef.current.getElementById(id)
      if (n.length) {
        cyRef.current.center(n)
        cyRef.current.animate({ zoom: 1.5, center: { eles: n } }, { duration: 600 })
      }
    }
  }

  const deleteNode = async (id: string) => {
    if (!confirm(`노드 ${id} 삭제? (관련 엣지 cascade)`)) return
    try {
      await api(`/api/graph/node/${encodeURIComponent(id)}`, { method: 'DELETE' })
      setSelectedId(null); setDetail(null); load()
    } catch (e: any) { alert(e.message) }
  }
  const compactPlaybook = async (pbId: string) => {
    if (!confirm(`${pbId} compaction 실행? (LLM 호출 ~30s)`)) return
    try {
      const r = await api(`/api/graph/compact/${encodeURIComponent(pbId)}`, { method: 'POST' })
      alert(`pitfalls +${r.pitfalls_added || 0}, insights +${r.insights_created || 0}, dropped ${r.dropped || 0}`)
      load()
    } catch (e: any) { alert(e.message) }
  }

  const fitGraph = () => {
    if (cyRef.current) {
      try { cyRef.current.fit(undefined, 40) } catch {}
    }
  }
  const relayoutGraph = () => {
    if (cyRef.current) {
      const layout = cyRef.current.layout({
        name: 'cose-bilkent', animate: 'end', animationDuration: 1000,
        randomize: true, idealEdgeLength: 140, nodeRepulsion: 14000,
        gravity: 0.5, numIter: 2500, packComponents: true, tile: true,
      } as any)
      layout.run()
    }
  }

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Knowledge graph 로드 중...</div>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1, minHeight: 0, minWidth: 0, width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 16px 0' }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: '#e6edf3', margin: 0 }}>
          🧠 Knowledge Graph
        </h2>
        <span style={{ fontSize: 13, color: '#8b949e' }}>
          {stats.total_nodes || 0} nodes · {stats.total_edges || 0} edges
        </span>
        {/* Domain toggle — Asset / Architecture / Work / Operational / 전체 */}
        <div style={{ display: 'flex', gap: 4, marginLeft: 16, background: '#0d1117', padding: 3, borderRadius: 6, border: '1px solid #30363d' }}>
          {Object.keys(DOMAINS).map(d => (
            <button key={d} onClick={() => switchDomain(d)} style={{
              padding: '4px 10px', borderRadius: 4, border: 'none', cursor: 'pointer',
              fontSize: 12, fontWeight: 600,
              background: domain === d ? '#f97316' : 'transparent',
              color: domain === d ? '#fff' : '#8b949e',
            }}>{d}</button>
          ))}
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
          <button onClick={() => setShowLeft(s => !s)} style={btn}>{showLeft ? '◀' : '▶'} 필터</button>
          <button onClick={fitGraph} style={btn}>⤢ Fit</button>
          <button onClick={relayoutGraph} style={btn}>↻ Relayout</button>
          <button onClick={load} style={btn}>새로고침</button>
          <button onClick={() => setShowDetail(s => !s)} style={btn}>{showDetail ? '▶' : '◀'} 상세</button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, height: '100%', minHeight: 0, padding: '0 16px 16px' }}>
        {/* 좌측 — 검색 + 필터 (토글 가능) */}
        {showLeft && (
        <div style={{ width: 220, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', gap: 4 }}>
            <input value={searchQ} onChange={e => setSearchQ(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && doSearch()}
              placeholder="검색 (FTS)..."
              style={{ flex: 1, background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d', borderRadius: 6, padding: '6px 10px', fontSize: 13 }} />
            <button onClick={doSearch} style={btn}>🔍</button>
          </div>
          {searchResults.length > 0 && (
            <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 6, padding: 8, maxHeight: 180, overflowY: 'auto' }}>
              {searchResults.map(r => (
                <div key={r.id} onClick={() => focusNode(r.id)} style={{ padding: '4px 6px', cursor: 'pointer', fontSize: 12, color: '#e6edf3', borderRadius: 4 }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#21262d')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                  <span style={{ color: NODE_COLORS[r.type] }}>●</span> <b>{r.type}</b>: {r.name.slice(0, 40)}
                </div>
              ))}
            </div>
          )}
          <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 6, padding: 12 }}>
            <div style={{ fontSize: 12, color: '#8b949e', marginBottom: 8, fontWeight: 600 }}>필터</div>
            {ALL_TYPES.map(t => {
              const cnt = stats.node_counts?.[t] || 0
              const enabled = enabledTypes.has(t)
              return (
                <div key={t} onClick={() => {
                  const ns = new Set(enabledTypes)
                  if (enabled) ns.delete(t); else ns.add(t)
                  setEnabledTypes(ns)
                }}
                  style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0', cursor: 'pointer', opacity: enabled ? 1 : 0.4 }}>
                  <span style={{ width: 10, height: 10, borderRadius: '50%', background: NODE_COLORS[t] }} />
                  <span style={{ fontSize: 12, color: '#e6edf3', flex: 1 }}>{t}</span>
                  <span style={{ fontSize: 11, color: '#8b949e' }}>{cnt}</span>
                </div>
              )
            })}
          </div>
        </div>
        )}

        {/* 중앙 — 그래프 (메인) */}
        <div style={{ flex: 1, position: 'relative', background: '#0d1117', border: '1px solid #21262d', borderRadius: 8, overflow: 'hidden' }}>
          <div ref={cyContainer} style={{ width: '100%', height: '100%' }} />
        </div>

        {/* 우측 — Detail (토글 가능) */}
        {showDetail && (
        <div style={{ width: 340, background: '#0d1117', border: '1px solid #21262d', borderRadius: 8, padding: 14, overflowY: 'auto' }}>
          {!selectedId && <div style={{ color: '#8b949e', fontSize: 13, textAlign: 'center', padding: 20 }}>노드를 클릭하면 상세가 나옵니다</div>}
          {selectedId && !detail && <div style={{ color: '#8b949e' }}>로드 중...</div>}
          {detail?.error && <div style={{ color: '#f85149' }}>{detail.error}</div>}
          {detail?.node && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ width: 12, height: 12, borderRadius: '50%', background: NODE_COLORS[detail.node.type] }} />
                <span style={{ fontSize: 11, color: NODE_COLORS[detail.node.type], fontWeight: 700, textTransform: 'uppercase' as const }}>
                  {detail.node.type}
                </span>
                <span style={{ fontSize: 11, color: '#8b949e', marginLeft: 'auto' }}>{detail.node.updated_at?.slice(0, 16)}</span>
              </div>
              <h3 style={{ fontSize: 16, color: '#e6edf3', marginBottom: 6, marginTop: 0 }}>{detail.node.name}</h3>
              <div style={{ fontSize: 11, color: '#8b949e', fontFamily: 'monospace' as const, marginBottom: 14, wordBreak: 'break-all' as const }}>{detail.node.id}</div>

              {/* type 별 핵심 콘텐츠 표시 */}
              {detail.node.type === 'Playbook' && detail.node.content && (
                <NodeSection title="Description">
                  <div style={{ fontSize: 12, color: '#e6edf3', whiteSpace: 'pre-wrap' as const }}>
                    {detail.node.content.description}
                  </div>
                  {detail.node.content.reasoning && (
                    <div style={{ marginTop: 8 }}>
                      <div style={{ fontSize: 11, color: '#8b949e', fontWeight: 600 }}>Reasoning</div>
                      <div style={{ fontSize: 12, color: '#e6edf3', marginTop: 4, whiteSpace: 'pre-wrap' as const }}>
                        {detail.node.content.reasoning.why_this_approach || detail.node.content.reasoning.task_decomposition || ''}
                      </div>
                    </div>
                  )}
                  {detail.node.content.known_pitfalls?.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <div style={{ fontSize: 11, color: '#8b949e', fontWeight: 600 }}>Known Pitfalls</div>
                      <ul style={{ fontSize: 12, color: '#e6edf3', margin: '4px 0', paddingLeft: 18 }}>
                        {detail.node.content.known_pitfalls.map((p: string, i: number) =>
                          <li key={i}>{p}</li>)}
                      </ul>
                    </div>
                  )}
                  <div style={{ marginTop: 8, fontSize: 11, color: '#8b949e' }}>
                    v{detail.node.content.version || 1} · risk: {detail.node.content.risk_level} ·
                    exec: {detail.node.content.exec_history?.success || 0}/{detail.node.content.exec_history?.total || 0}
                  </div>
                </NodeSection>
              )}
              {detail.node.type === 'Experience' && detail.node.content && (
                <NodeSection title="Task">
                  <div style={{ fontSize: 12, color: '#e6edf3', whiteSpace: 'pre-wrap' as const }}>{detail.node.content.task_summary}</div>
                  <div style={{ marginTop: 8, fontSize: 11, color: detail.node.content.outcome === 'success' ? '#3fb950' : '#f85149' }}>
                    outcome: {detail.node.content.outcome}
                  </div>
                  {detail.node.content.tool_outputs?.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <div style={{ fontSize: 11, color: '#8b949e', fontWeight: 600 }}>Tool calls</div>
                      {detail.node.content.tool_outputs.map((t: any, i: number) => (
                        <div key={i} style={{ fontSize: 12, color: '#e6edf3', marginTop: 4 }}>
                          <span style={{ color: t.success ? '#3fb950' : '#f85149' }}>●</span>{' '}
                          {t.skill} (exit={t.exit_code})
                        </div>
                      ))}
                    </div>
                  )}
                </NodeSection>
              )}
              {detail.node.type === 'Skill' && detail.node.content && (
                <NodeSection title="Description">
                  <div style={{ fontSize: 12, color: '#e6edf3' }}>{detail.node.content.description}</div>
                  <div style={{ marginTop: 6, fontSize: 11, color: '#8b949e' }}>
                    target: {detail.node.content.target_vm}
                  </div>
                </NodeSection>
              )}
              {detail.node.type === 'Insight' && detail.node.content && (
                <NodeSection title="Insight">
                  <div style={{ fontSize: 13, color: '#e6edf3', fontStyle: 'italic' as const }}>"{detail.node.content.text}"</div>
                </NodeSection>
              )}
              {detail.node.type === 'Narrative' && (
                <NodeSection title="Narrative">
                  <div style={{ fontSize: 12, color: '#8b949e' }}>
                    status: <b style={{ color: detail.node.meta?.status === 'open' ? '#3fb950' : '#8b949e' }}>{detail.node.meta?.status}</b>
                    {detail.node.meta?.event_count !== undefined &&
                      <span style={{ marginLeft: 8 }}>events: {detail.node.meta.event_count}</span>}
                  </div>
                  <div style={{ fontSize: 11, color: '#8b949e', marginTop: 4 }}>
                    started: {detail.node.meta?.started_at?.slice(0, 16)}
                    {detail.node.meta?.ended_at && <span> · ended: {detail.node.meta.ended_at.slice(0, 16)}</span>}
                  </div>
                  {detail.node.meta?.summary && (
                    <div style={{ fontSize: 12, color: '#e6edf3', marginTop: 8, whiteSpace: 'pre-wrap' as const }}>
                      {detail.node.meta.summary}
                    </div>
                  )}
                </NodeSection>
              )}
              {detail.node.type === 'Anchor' && (
                <NodeSection title="Anchor (압축 면역)">
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                    <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10, background: '#ffa65722', color: '#ffa657', fontWeight: 700, textTransform: 'uppercase' as const }}>
                      {detail.node.meta?.kind}
                    </span>
                    <span style={{ fontSize: 11, color: '#8b949e' }}>
                      {detail.node.meta?.valid_from?.slice(0, 10)}
                      {detail.node.meta?.valid_until ? ` ~ ${detail.node.meta.valid_until.slice(0, 10)}` : ' ~ 영구'}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: '#e6edf3', whiteSpace: 'pre-wrap' as const, fontFamily: 'monospace' as const, background: '#0d1117', padding: 8, borderRadius: 6 }}>
                    {detail.node.meta?.body}
                  </div>
                </NodeSection>
              )}

              {/* Asset/Narrative 선택 시 timeline (events) */}
              {timeline && (timeline.events?.length > 0 || timeline.narratives?.length > 0 || timeline.anchors?.length > 0) && (
                <NodeSection title={`History Timeline ${timeline.events ? `(${timeline.events.length} events)` : ''}`}>
                  {timeline.narratives?.length > 0 && (
                    <div style={{ marginBottom: 8 }}>
                      <div style={{ fontSize: 11, color: '#8b949e', fontWeight: 600 }}>Narratives ({timeline.narratives.length})</div>
                      {timeline.narratives.slice(0, 5).map((n: any) => (
                        <div key={n.id} onClick={() => focusNode(n.id)} style={{ fontSize: 12, color: '#79c0ff', cursor: 'pointer', padding: '2px 0' }}>
                          ▸ {n.title} <span style={{ color: '#8b949e' }}>({n.status})</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {timeline.anchors?.length > 0 && (
                    <div style={{ marginBottom: 8 }}>
                      <div style={{ fontSize: 11, color: '#8b949e', fontWeight: 600 }}>Anchors ({timeline.anchors.length})</div>
                      {timeline.anchors.slice(0, 5).map((a: any) => (
                        <div key={a.id} onClick={() => focusNode(a.id)} style={{ fontSize: 12, color: '#ffa657', cursor: 'pointer', padding: '2px 0' }}>
                          ⚓ <b>{a.kind}</b> · {a.label}
                        </div>
                      ))}
                    </div>
                  )}
                  {timeline.events?.length > 0 && (
                    <div>
                      <div style={{ fontSize: 11, color: '#8b949e', fontWeight: 600 }}>Recent Events</div>
                      <div style={{ maxHeight: 220, overflowY: 'auto', marginTop: 4 }}>
                        {timeline.events.slice(0, 30).map((e: any) => (
                          <div key={e.id} style={{ padding: '4px 0', borderBottom: '1px solid #21262d', fontSize: 12 }}>
                            <span style={{ color: '#8b949e', fontFamily: 'monospace' as const, marginRight: 6 }}>{e.ts?.slice(11, 19)}</span>
                            <span style={{ color: e.kind === 'task_done' ? '#3fb950' : e.kind === 'task_fail' ? '#f85149' : '#d29922', fontWeight: 600, marginRight: 6 }}>
                              {e.kind}
                            </span>
                            <span style={{ color: '#e6edf3' }}>{e.summary?.slice(0, 80)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {timeline.changelog?.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <div style={{ fontSize: 11, color: '#8b949e', fontWeight: 600 }}>Changelog ({timeline.changelog.length})</div>
                      {timeline.changelog.slice(-5).reverse().map((c: any, i: number) => (
                        <div key={i} style={{ fontSize: 12, color: '#e6edf3', padding: '2px 0' }}>
                          v{c.version} <span style={{ color: '#8b949e' }}>{c.ts?.slice(0, 10)}</span> · {c.diff?.slice(0, 60)}
                        </div>
                      ))}
                    </div>
                  )}
                </NodeSection>
              )}

              {/* Backlinks */}
              {detail.backlinks && Object.keys(detail.backlinks).length > 0 && (
                <NodeSection title="Backlinks">
                  {Object.entries(detail.backlinks).map(([etype, list]: [string, any]) => (
                    <div key={etype} style={{ marginBottom: 6 }}>
                      <div style={{ fontSize: 11, color: '#8b949e' }}>{etype} ({list.length})</div>
                      {list.slice(0, 8).map((l: any, i: number) => (
                        <div key={i} onClick={() => focusNode(l.other)}
                          style={{ fontSize: 12, color: '#58a6ff', cursor: 'pointer', padding: '2px 0' }}>
                          ← <span style={{ color: NODE_COLORS[l.other_type] }}>●</span> {l.other_name}
                        </div>
                      ))}
                    </div>
                  ))}
                </NodeSection>
              )}

              {/* Out edges */}
              {detail.out_edges && detail.out_edges.length > 0 && (
                <NodeSection title="Outgoing">
                  {detail.out_edges.slice(0, 12).map((e: any, i: number) => (
                    <div key={i} onClick={() => focusNode(e.other)}
                      style={{ fontSize: 12, color: '#58a6ff', cursor: 'pointer', padding: '2px 0' }}>
                      <span style={{ color: '#8b949e' }}>{e.edge_type}</span> →{' '}
                      <span style={{ color: NODE_COLORS[e.other_type] }}>●</span> {e.other_name}
                    </div>
                  ))}
                </NodeSection>
              )}

              {/* Actions */}
              <div style={{ marginTop: 14, display: 'flex', gap: 6, flexWrap: 'wrap' as const }}>
                {detail.node.type === 'Playbook' && (
                  <button onClick={() => compactPlaybook(detail.node.id)} style={{ ...btn, background: '#bc8cff22', color: '#bc8cff', borderColor: '#bc8cff' }}>
                    🧪 Compact
                  </button>
                )}
                <button onClick={() => deleteNode(detail.node.id)} style={{ ...btn, background: '#da363322', color: '#f85149', borderColor: '#f85149' }}>
                  🗑 삭제
                </button>
              </div>
            </div>
          )}
        </div>
        )}
      </div>
    </div>
  )
}

const btn: React.CSSProperties = {
  padding: '6px 12px', borderRadius: 6, border: '1px solid #30363d',
  background: '#21262d', color: '#e6edf3', cursor: 'pointer', fontSize: 12,
  display: 'flex', alignItems: 'center', gap: 4,
}

function NodeSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 14, padding: 10, background: '#161b22', border: '1px solid #21262d', borderRadius: 6 }}>
      <div style={{ fontSize: 11, color: '#8b949e', fontWeight: 600, marginBottom: 6, textTransform: 'uppercase' as const, letterSpacing: '0.3px' }}>
        {title}
      </div>
      {children}
    </div>
  )
}

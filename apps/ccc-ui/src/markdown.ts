// Shared markdown → HTML renderer (Education.tsx / Papers.tsx 공용)
// Design tokens (교안 렌더러와 동일):
//   brand-orange #f97316 · fg-bright #e6edf3 · fg-body #c9d1d9 · fg-dim #8b949e
//   semantic-green #3fb950 (bash/sh 전용) · surface-0/1/2 #0d1117/#161b22/#21262d
export function markdownToHtml(md: string): string {
  // 1. Mermaid → placeholder (이스케이프 전 보존)
  const mermaidBlocks: string[] = []
  md = md.replace(/```mermaid\n([\s\S]*?)```/g, (_, code) => {
    mermaidBlocks.push(code)
    return `__MERMAID_${mermaidBlocks.length - 1}__`
  })

  // 2. 코드블록도 placeholder화 — 내부 **·|·#의 마크다운 오인 방지
  const codeBlocks: { lang: string; body: string }[] = []
  md = md.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, body) => {
    codeBlocks.push({ lang: (lang || '').toLowerCase(), body })
    return `__CODE_${codeBlocks.length - 1}__`
  })

  // 3. HTML escape + 마크다운 치환
  let html = md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^#### (.+)$/gm, '<h4 style="font-size:17px;color:#c9d1d9;margin:20px 0 8px;font-weight:600">$1</h4>')
    .replace(/^### (.+)$/gm, '<h3 style="font-size:19px;color:#e6edf3;margin:24px 0 10px;font-weight:600">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="font-size:22px;color:#e6edf3;margin:32px 0 14px;border-bottom:1px solid #30363d;padding-bottom:8px;font-weight:700">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="font-size:26px;color:#e6edf3;margin:0 0 18px;padding-bottom:10px;border-bottom:2px solid #f97316;font-weight:700">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#e6edf3;font-weight:700">$1</strong>')
    .replace(/`([^`]+)`/g, '<code style="background:#21262d;padding:2px 7px;border-radius:4px;font-size:0.92em;color:#f97316;font-family:\'D2Coding\',Consolas,Monaco,monospace">$1</code>')
    .replace(/((?:^&gt; .+(?:\n|$))+)/gm, (match) => {
      const body = match.replace(/^&gt; /gm, '').replace(/\n$/, '').replace(/\n/g, '<br/>')
      return `<div style="border-left:3px solid #f97316;padding:10px 16px;margin:14px 0;background:#161b22;color:#c9d1d9;font-size:15px;border-radius:0 6px 6px 0">${body}</div>`
    })
    .replace(/^- (.+)$/gm, '<div style="padding:3px 0 3px 22px;font-size:16px;position:relative"><span style="position:absolute;left:6px;color:#f97316">•</span>$1</div>')
    .replace(/^(\d+)\. (.+)$/gm, '<div style="padding:3px 0 3px 22px;font-size:16px;position:relative"><span style="position:absolute;left:0;color:#f97316;font-weight:600">$1.</span>$2</div>')
    .replace(/^---+$/gm, '<hr style="border:none;border-top:1px solid #30363d;margin:28px 0"/>')

  // 4. 테이블 → <table>
  html = html.replace(/((?:^\|.*\|\s*\n)+)/gm, (block) => {
    const rows = block.trim().split('\n').filter(r => r.trim().startsWith('|'))
    if (rows.length < 2) return block
    const sep = rows[1]
    const isHeader = /^\|[\s\-:|]+\|$/.test(sep.trim())
    if (!isHeader) return block
    const parseCells = (row: string) => row.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim())
    const headers = parseCells(rows[0])
    const bodyRows = rows.slice(2).map(parseCells)
    const thead = '<thead><tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr></thead>'
    const tbody = '<tbody>' + bodyRows.map(r => '<tr>' + r.map(c => `<td>${c}</td>`).join('') + '</tr>').join('') + '</tbody>'
    return `<table>${thead}${tbody}</table>`
  })

  // 5. 줄바꿈
  html = html
    .replace(/\n{2,}/g, '<div style="height:10px"></div>')
    .replace(/\n/g, '<br/>')

  // 6. 코드블록 복원
  codeBlocks.forEach(({ lang, body }, i) => {
    const escaped = body.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    const isShell = /^(bash|sh|shell|console|terminal|zsh)$/.test(lang)
    const color = isShell ? '#3fb950' : '#e6edf3'
    const label = lang ? `<div style="position:absolute;top:6px;right:10px;font-size:11px;color:#8b949e;font-family:system-ui;text-transform:uppercase;letter-spacing:0.5px">${lang}</div>` : ''
    const pre = `<div style="position:relative;margin:14px 0">${label}<pre style="background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:16px 20px;font-size:14px;line-height:1.55;overflow-x:auto;color:${color};margin:0;font-family:'D2Coding','Nanum Gothic Coding',Consolas,Monaco,'Courier New',monospace;white-space:pre;tab-size:4;letter-spacing:0">${escaped}</pre></div>`
    html = html.replace(`__CODE_${i}__`, pre)
  })

  // 7. Mermaid 복원
  mermaidBlocks.forEach((code, i) => {
    html = html.replace(`__MERMAID_${i}__`, `<div class="mermaid">${code}</div>`)
  })

  return html
}

// Education.tsx의 인라인 스타일과 동일한 CSS (클래스명만 지정하면 적용).
// <style>{MARKDOWN_CSS}</style> + <div className={MARKDOWN_CLASS}> 로 감싸 사용.
export const MARKDOWN_CLASS = 'md-content'
export const MARKDOWN_CSS = `
.${MARKDOWN_CLASS} table { border-collapse: collapse; width: auto; max-width: 100%; margin: 16px 0; font-size: 14px; }
.${MARKDOWN_CLASS} th, .${MARKDOWN_CLASS} td { border: 1px solid #30363d; padding: 8px 14px; text-align: left; vertical-align: top; }
.${MARKDOWN_CLASS} th { background: #21262d; color: #e6edf3; font-weight: 600; white-space: nowrap; }
.${MARKDOWN_CLASS} td { color: #c9d1d9; }
.${MARKDOWN_CLASS} td code { white-space: normal; word-break: break-word; }
.${MARKDOWN_CLASS} tr:hover td { background: #1c2128; }
.${MARKDOWN_CLASS} pre { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 16px 20px; overflow-x: auto; font-size: 14px; line-height: 1.55; }
.${MARKDOWN_CLASS} code { background: #21262d; padding: 2px 7px; border-radius: 4px; font-size: 0.92em; color: #f97316; font-family: 'D2Coding',Consolas,Monaco,monospace; }
.${MARKDOWN_CLASS} pre code { background: none; padding: 0; color: inherit; font-size: 14px; }
.${MARKDOWN_CLASS} h1 { font-size: 26px; border-bottom: 2px solid #f97316; padding-bottom: 10px; margin: 0 0 18px; color: #e6edf3; font-weight: 700; }
.${MARKDOWN_CLASS} h2 { font-size: 22px; border-bottom: 1px solid #30363d; padding-bottom: 8px; margin-top: 32px; color: #e6edf3; font-weight: 700; }
.${MARKDOWN_CLASS} h3 { font-size: 19px; margin-top: 24px; color: #e6edf3; font-weight: 600; }
.${MARKDOWN_CLASS} h4 { font-size: 17px; margin-top: 20px; color: #c9d1d9; font-weight: 600; }
.${MARKDOWN_CLASS} blockquote { border-left: 3px solid #f97316; padding: 10px 16px; margin: 14px 0; background: #161b22; color: #c9d1d9; border-radius: 0 6px 6px 0; }
.${MARKDOWN_CLASS} strong { color: #e6edf3; font-weight: 700; }
.${MARKDOWN_CLASS} img { max-width: 100%; border-radius: 8px; }
.${MARKDOWN_CLASS} ul, .${MARKDOWN_CLASS} ol { padding-left: 24px; }
.${MARKDOWN_CLASS} li { margin-bottom: 4px; }
.${MARKDOWN_CLASS} hr { border: none; border-top: 1px solid #30363d; margin: 28px 0; }
.${MARKDOWN_CLASS} a { color: #58a6ff; text-decoration: none; }
.${MARKDOWN_CLASS} a:hover { text-decoration: underline; }
.${MARKDOWN_CLASS} .mermaid { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin: 14px 0; text-align: center; }
`

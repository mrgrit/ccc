import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'
import { getUser } from '../auth.ts'

const ROLES = [
  { role: 'attacker', label: 'Attacker (Kali)', icon: '🗡️', desc: 'nmap, metasploit, hydra, sqlmap, burpsuite, impacket, bloodhound', needSubagent: true },
  { role: 'secu', label: 'Security Gateway', icon: '🛡️', desc: 'nftables, suricata, sysmon, osquery, auditd', needSubagent: true },
  { role: 'web', label: 'Web Server', icon: '🌐', desc: 'ModSecurity, JuiceShop, DVWA, WebGoat, sysmon, osquery', needSubagent: true },
  { role: 'siem', label: 'SIEM', icon: '📡', desc: 'Wazuh, SIGMA, OpenCTI, sysmon, osquery, 로그 수집', needSubagent: true },
  { role: 'windows', label: 'Windows (분석)', icon: '🪟', desc: 'Sysmon, osquery, Ghidra, x64dbg, Autopsy, FTK Imager', needSubagent: true },
  { role: 'manager', label: 'Manager AI', icon: '🤖', desc: 'Ollama, LLM 추론, CCC 운영 에이전트', needSubagent: true },
]

const statusColor: Record<string, string> = {
  healthy: '#3fb950', bootstrapped: '#58a6ff', registered: '#d29922', unreachable: '#f85149', error: '#f85149',
}

export default function MyInfra() {
  const user = getUser()
  const [infras, setInfras] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [setting, setSetting] = useState(false)
  const [setupResult, setSetupResult] = useState<any>(null)
  const [onboardLog, setOnboardLog] = useState<any[]>([])
  const [form, setForm] = useState({
    attacker_ip: '', secu_ip: '', web_ip: '', siem_ip: '',
    ssh_user: 'ccc', ssh_password: '1',
    windows_ip: '', manager_ip: '', gpu_url: '',
    manager_model: '', subagent_model: '',
  })
  const [llmUrl, setLlmUrl] = useState('http://localhost:11434')
  const [llmModels, setLlmModels] = useState<string[]>([])
  const [llmConnected, setLlmConnected] = useState(false)
  const [llmLoading, setLlmLoading] = useState(false)

  const connectLlm = async () => {
    setLlmLoading(true)
    setLlmConnected(false)
    setLlmModels([])
    try {
      const url = llmUrl.replace(/\/+$/, '')
      const d = await api('/api/llm/models', {
        method: 'POST',
        body: JSON.stringify({ url }),
      })
      const models: string[] = d.models || []
      setLlmModels(models)
      setLlmConnected(d.connected)
      if (d.connected) {
        setForm(f => ({ ...f, gpu_url: url }))
        if (models.length > 0 && !form.manager_model) {
          setForm(f => ({ ...f, manager_model: models[0] }))
        }
        if (models.length > 1 && !form.subagent_model) {
          setForm(f => ({ ...f, subagent_model: models[1] }))
        } else if (models.length === 1 && !form.subagent_model) {
          setForm(f => ({ ...f, subagent_model: models[0] }))
        }
      }
    } catch {
      setLlmConnected(false)
    }
    setLlmLoading(false)
  }

  const load = () => {
    api('/api/infras/my')
      .then(d => setInfras(d.infras || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const setup = async () => {
    if (!form.attacker_ip || !form.secu_ip || !form.web_ip || !form.siem_ip || !form.manager_ip) {
      alert('5개 VM의 IP를 모두 입력하세요 (Attacker, Security, Web, SIEM, Manager)')
      return
    }
    setSetting(true)
    setSetupResult(null)
    setOnboardLog([])

    // 1단계: DB 등록
    try {
      await api('/api/infras/setup', { method: 'POST', body: JSON.stringify(form) })
    } catch (e: any) { alert('등록 실패: ' + e.message); setSetting(false); return }

    // 2단계: 온보딩 (SSE 스트리밍)
    try {
      const token = localStorage.getItem('ccc_token') || ''
      const resp = await fetch('/api/infras/onboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': 'ccc-api-key-2026', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(form),
      })
      const reader = resp.body?.getReader()
      const decoder = new TextDecoder()
      if (reader) {
        let buf = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buf += decoder.decode(value, { stream: true })
          const lines = buf.split('\n')
          buf = lines.pop() || ''
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const evt = JSON.parse(line.slice(6))
                setOnboardLog(prev => [...prev, evt])
              } catch {}
            }
          }
        }
      }
    } catch (e: any) {
      setOnboardLog(prev => [...prev, { event: 'error', role: 'system', message: e.message }])
    }

    load()
    setSetting(false)
  }

  const checkHealth = async (iid: string) => {
    try {
      const d = await api(`/api/infras/${iid}/health`)
      load()
    } catch {}
  }

  const hasInfra = infras.length >= 5

  if (loading) return <div style={{ color: '#8b949e', padding: 40, textAlign: 'center' }}>Loading...</div>

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, color: '#e6edf3' }}>My Infrastructure</h2>
      <p style={{ fontSize: 15, color: '#8b949e', marginBottom: 24 }}>
        실습과 대전에 사용할 VM 5대의 외부 IP를 입력합니다. 내부 IP(10.20.30.x)는 자동 할당됩니다.
      </p>

      {/* 현재 인프라 상태 */}
      {hasInfra && (
        <div style={{ marginBottom: 28 }}>
          <h3 style={{ fontSize: 17, marginBottom: 14, color: '#e6edf3' }}>현재 인프라</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
            {infras.map(infra => {
              const cfg = infra.vm_config || {}
              const roleMeta = ROLES.find(r => r.role === cfg.role) || ROLES[0]
              return (
                <div key={infra.id} style={{
                  background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 20,
                  borderLeft: `4px solid ${statusColor[infra.status] || '#8b949e'}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span style={{ fontSize: 22 }}>{roleMeta.icon}</span>
                      <span style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3' }}>{roleMeta.label}</span>
                    </div>
                    <span style={{
                      padding: '3px 10px', borderRadius: 10, fontSize: 13, fontWeight: 600,
                      color: statusColor[infra.status] || '#8b949e',
                      background: `${statusColor[infra.status] || '#8b949e'}15`,
                    }}>{infra.status}</span>
                  </div>
                  <div style={{ fontSize: 14, color: '#8b949e', marginBottom: 6 }}>
                    IP: <code style={{ color: '#d2a8ff' }}>{infra.ip}</code>
                  </div>
                  {infra.subagent_url && (
                    <div style={{ fontSize: 13, color: '#8b949e', marginBottom: 8 }}>
                      SubAgent: <code style={{ color: '#58a6ff' }}>{infra.subagent_url}</code>
                    </div>
                  )}
                  {roleMeta.needSubagent && (
                    <button onClick={() => checkHealth(infra.id)} style={smallBtn}>Health Check</button>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 설정 폼 */}
      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 10, padding: 28 }}>
        <h3 style={{ fontSize: 18, marginBottom: 6, color: '#e6edf3' }}>
          {hasInfra ? '인프라 재설정' : '인프라 등록'}
        </h3>
        <p style={{ fontSize: 14, color: '#8b949e', marginBottom: 20 }}>
          5개 VM의 IP를 입력하고 "자동 설정"을 누르면 Bastion AI가 SubAgent를 설치합니다.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
          {/* Attacker */}
          <div style={vmCard}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 20 }}>🗡️</span>
              <span style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3' }}>Attacker (Kali)</span>
              <span style={reqBadge}>필수</span>
            </div>
            <div style={reqBox}>
              <div style={reqLine}>OS: Kali Linux 2024+ / Ubuntu 22.04+</div>
              <div style={reqLine}>CPU: 2코어 이상 / RAM: 4GB 이상</div>
              <div style={reqLine}>디스크: 40GB 이상</div>
              <div style={reqLine}>네트워크: 내부망(10.x) 접근 가능</div>
            </div>
            <input placeholder="외부 IP (예: 192.168.0.50)" value={form.attacker_ip}
              onChange={e => setForm({ ...form, attacker_ip: e.target.value })} style={inputStyle} />
            <div style={{ fontSize: 12, color: '#58a6ff', marginTop: 4 }}>내부: 10.20.30.201 (자동)</div>
            <div style={{ fontSize: 12, color: '#3fb950' }}>nmap, metasploit, hydra, sqlmap + SubAgent 자동설치</div>
          </div>

          {/* Secu */}
          <div style={vmCard}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 20 }}>🛡️</span>
              <span style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3' }}>Security Gateway</span>
              <span style={reqBadge}>필수</span>
            </div>
            <div style={reqBox}>
              <div style={reqLine}>OS: Ubuntu 22.04+ / Debian 12+</div>
              <div style={reqLine}>CPU: 2코어 이상 / RAM: 4GB 이상</div>
              <div style={reqLine}>디스크: 20GB 이상</div>
              <div style={{ ...reqLine, color: '#f97316' }}>NIC 2개 필수: 외부(bridge) + 내부(10.x)</div>
              <div style={reqLine}>IP forwarding 활성화 (sysctl)</div>
            </div>
            <input placeholder="외부 IP (예: 192.168.0.51)" value={form.secu_ip}
              onChange={e => setForm({ ...form, secu_ip: e.target.value })} style={inputStyle} />
            <div style={{ fontSize: 12, color: '#58a6ff', marginTop: 4 }}>내부: 10.20.30.1 (자동) — 인터넷 게이트웨이</div>
            <div style={{ fontSize: 12, color: '#3fb950' }}>nftables + Suricata IPS + NAT + SubAgent 자동설치</div>
          </div>

          {/* Web */}
          <div style={vmCard}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 20 }}>🌐</span>
              <span style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3' }}>Web Server</span>
              <span style={reqBadge}>필수</span>
            </div>
            <div style={reqBox}>
              <div style={reqLine}>OS: Ubuntu 22.04+ / Debian 12+</div>
              <div style={reqLine}>CPU: 2코어 이상 / RAM: 4GB 이상</div>
              <div style={reqLine}>디스크: 30GB 이상</div>
              <div style={reqLine}>포트: 80, 443, 3000(JuiceShop), 8080(DVWA)</div>
            </div>
            <input placeholder="외부 IP (예: 192.168.0.52)" value={form.web_ip}
              onChange={e => setForm({ ...form, web_ip: e.target.value })} style={inputStyle} />
            <div style={{ fontSize: 12, color: '#58a6ff', marginTop: 4 }}>내부: 10.20.30.80 (자동)</div>
            <div style={{ fontSize: 12, color: '#3fb950' }}>Apache + JuiceShop + WAF + SubAgent 자동설치</div>
          </div>

          {/* SIEM */}
          <div style={vmCard}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 20 }}>📡</span>
              <span style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3' }}>SIEM</span>
              <span style={reqBadge}>필수</span>
            </div>
            <div style={reqBox}>
              <div style={reqLine}>OS: Ubuntu 22.04+ / Debian 12+</div>
              <div style={reqLine}>CPU: 4코어 이상</div>
              <div style={{ ...reqLine, color: '#f97316' }}>RAM: 8GB 이상 (Wazuh+OpenCTI 동시 구동)</div>
              <div style={reqLine}>디스크: 50GB 이상 (로그 저장)</div>
              <div style={reqLine}>포트: 1514(Wazuh), 5601(Dashboard), 9200(ES)</div>
            </div>
            <input placeholder="외부 IP (예: 192.168.0.53)" value={form.siem_ip}
              onChange={e => setForm({ ...form, siem_ip: e.target.value })} style={inputStyle} />
            <div style={{ fontSize: 12, color: '#58a6ff', marginTop: 4 }}>내부: 10.20.30.100 (자동)</div>
            <div style={{ fontSize: 12, color: '#3fb950' }}>Wazuh + SIGMA + OpenCTI + SubAgent 자동설치</div>
          </div>

          {/* Windows */}
          <div style={vmCard}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 20 }}>🪟</span>
              <span style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3' }}>Windows (분석/포렌식)</span>
              <span style={optBadge}>선택</span>
            </div>
            <div style={reqBox}>
              <div style={reqLine}>OS: Windows 10/11 Pro 이상</div>
              <div style={reqLine}>CPU: 2코어 이상 / RAM: 8GB 이상</div>
              <div style={reqLine}>디스크: 60GB 이상 (분석 도구 + 이미지)</div>
              <div style={reqLine}>OpenSSH Server 활성화 필수</div>
            </div>
            <input placeholder="외부 IP (선택, 없으면 skip)" value={form.windows_ip}
              onChange={e => setForm({ ...form, windows_ip: e.target.value })} style={inputStyle} />
            <div style={{ fontSize: 12, color: '#58a6ff', marginTop: 4 }}>내부: 10.20.30.50 (자동)</div>
            <div style={{ fontSize: 12, color: '#8b949e' }}>Sysmon, Ghidra, x64dbg, Autopsy, FTK Imager</div>
          </div>

          {/* Manager AI */}
          <div style={vmCard}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 20 }}>🤖</span>
              <span style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3' }}>Manager AI</span>
              <span style={reqBadge}>필수</span>
            </div>
            <div style={reqBox}>
              <div style={reqLine}>OS: Ubuntu 22.04+ / Debian 12+</div>
              <div style={reqLine}>CPU: 4코어 이상 / RAM: 8GB 이상</div>
              <div style={reqLine}>디스크: 30GB 이상</div>
              <div style={reqLine}>외부 GPU 미사용 시: VRAM 8GB+ GPU 권장</div>
              <div style={reqLine}>포트: 11434(Ollama), 8765(SubAgent)</div>
            </div>
            <input placeholder="외부 IP (예: 192.168.0.55)" value={form.manager_ip}
              onChange={e => setForm({ ...form, manager_ip: e.target.value })} style={inputStyle} />
            <div style={{ fontSize: 12, color: '#58a6ff', marginTop: 4 }}>내부: 10.20.30.200 (자동)</div>

            {/* LLM 서버 연결 */}
            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
              <input placeholder="LLM 서버 URL (예: http://dgx-spark:11434)" value={llmUrl}
                onChange={e => setLlmUrl(e.target.value)} style={{ ...inputStyle, flex: 1 }} />
              <button onClick={connectLlm} disabled={llmLoading} style={{
                padding: '8px 16px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap' as const,
                background: llmConnected ? '#3fb950' : '#f97316', color: '#fff',
              }}>{llmLoading ? '...' : llmConnected ? `✓ ${llmModels.length}개 모델` : '연결'}</button>
            </div>

            {/* 모델 선택 (연결 후 표시) */}
            {llmConnected && llmModels.length > 0 && (
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: '#8b949e', marginBottom: 4 }}>Manager 모델 (분석/피드백)</div>
                  <select value={form.manager_model} onChange={e => setForm({ ...form, manager_model: e.target.value })}
                    style={{ ...inputStyle, width: '100%', cursor: 'pointer' }}>
                    {llmModels.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: '#8b949e', marginBottom: 4 }}>SubAgent 모델 (챗봇/경량)</div>
                  <select value={form.subagent_model} onChange={e => setForm({ ...form, subagent_model: e.target.value })}
                    style={{ ...inputStyle, width: '100%', cursor: 'pointer' }}>
                    {llmModels.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
              </div>
            )}
            {llmConnected && llmModels.length === 0 && (
              <div style={{ fontSize: 12, color: '#f85149', marginTop: 6 }}>모델이 없습니다. ollama pull로 모델을 설치하세요.</div>
            )}
            {!llmConnected && !llmLoading && (
              <div style={{ fontSize: 12, color: '#8b949e', marginTop: 6 }}>LLM 서버 URL을 입력하고 연결 버튼을 클릭하세요</div>
            )}
            <div style={{ fontSize: 12, color: '#3fb950', marginTop: 6 }}>Ollama + Bastion 자동설치, 학생이 자기 인프라를 직접 운영</div>
          </div>
        </div>

        {/* SSH 자격증명 */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
          <input placeholder="SSH 사용자 (기본: ccc)" value={form.ssh_user}
            onChange={e => setForm({ ...form, ssh_user: e.target.value })} style={{ ...inputStyle, flex: 1 }} />
          <input placeholder="SSH 비밀번호" type="password" value={form.ssh_password}
            onChange={e => setForm({ ...form, ssh_password: e.target.value })} style={{ ...inputStyle, flex: 1 }} />
        </div>

        <button onClick={setup} disabled={setting} style={{
          width: '100%', padding: '14px 0', borderRadius: 8, border: 'none',
          background: setting ? '#21262d' : '#f97316', color: '#fff', fontSize: 17, fontWeight: 700, cursor: setting ? 'wait' : 'pointer',
        }}>{setting ? '온보딩 진행 중...' : '자동 설정 시작'}</button>
      </div>

      {/* 온보딩 실시간 로그 */}
      {onboardLog.length > 0 && (
        <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: 10, padding: 20, marginTop: 20, fontFamily: 'Consolas,Monaco,monospace', fontSize: 13 }}>
          <h3 style={{ fontSize: 15, marginBottom: 12, color: '#e6edf3' }}>온보딩 진행상황</h3>
          <div style={{ maxHeight: 400, overflowY: 'auto' }}>
            {onboardLog.map((evt, i) => {
              if (evt.event === 'start') return (
                <div key={i} style={{ padding: '4px 0', color: '#f97316' }}>
                  ▶ [{evt.progress}] {evt.role} ({evt.ip}) 설치 시작...
                </div>
              )
              if (evt.event === 'step') return (
                <div key={i}>
                  <div style={{ padding: '2px 0 2px 16px', color: evt.success ? '#3fb950' : '#f85149' }}>
                    {evt.success ? '✓' : '✗'} {evt.step}
                  </div>
                  {!evt.success && evt.stderr && (
                    <div style={{ padding: '0 0 2px 32px', color: '#8b949e', fontSize: 11 }}>{evt.stderr}</div>
                  )}
                </div>
              )
              if (evt.event === 'done') return (
                <div key={i} style={{ padding: '4px 0', color: evt.status === 'healthy' ? '#3fb950' : '#d29922', fontWeight: 600 }}>
                  {evt.status === 'healthy' ? '✓' : '⚠'} [{evt.progress}] {evt.role}: {evt.status}
                </div>
              )
              if (evt.event === 'error') return (
                <div key={i} style={{ padding: '4px 0', color: '#f85149' }}>
                  ✗ {evt.role}: {evt.message}
                </div>
              )
              if (evt.event === 'complete') return (
                <div key={i} style={{ padding: '8px 0 0', color: '#58a6ff', fontWeight: 600, borderTop: '1px solid #21262d', marginTop: 8 }}>
                  ■ 온보딩 완료 ({evt.total}대)
                </div>
              )
              return null
            })}
          </div>
        </div>
      )}
    </div>
  )
}

const vmCard: React.CSSProperties = {
  background: '#0d1117', border: '1px solid #21262d', borderRadius: 8, padding: 16,
}
const inputStyle: React.CSSProperties = {
  width: '100%', background: '#161b22', color: '#e6edf3', border: '1px solid #30363d',
  borderRadius: 6, padding: '10px 14px', fontSize: 15,
}
const smallBtn: React.CSSProperties = {
  padding: '6px 14px', borderRadius: 6, border: '1px solid #30363d',
  background: '#21262d', color: '#e6edf3', cursor: 'pointer', fontSize: 13,
}
const reqBadge: React.CSSProperties = {
  fontSize: 11, padding: '1px 8px', borderRadius: 10, background: 'rgba(248,81,73,0.15)', color: '#f85149', fontWeight: 600,
}
const optBadge: React.CSSProperties = {
  fontSize: 11, padding: '1px 8px', borderRadius: 10, background: 'rgba(139,148,158,0.15)', color: '#8b949e', fontWeight: 600,
}
const reqBox: React.CSSProperties = {
  background: '#0d1117', border: '1px solid #21262d', borderRadius: 6, padding: '8px 12px', marginBottom: 10, fontSize: 12, lineHeight: 1.8,
}
const reqLine: React.CSSProperties = {
  color: '#8b949e',
}

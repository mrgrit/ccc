import { getToken } from './auth.ts'

const BASE = ''
const API_KEY = 'ccc-api-key-2026'

export async function api<T = any>(path: string, opts?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts?.headers as Record<string, string> || {}),
  }
  // JWT 토큰이 있으면 Bearer, 없으면 API Key
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  } else {
    headers['X-API-Key'] = API_KEY
  }
  const res = await fetch(`${BASE}${path}`, { ...opts, headers })
  if (!res.ok) {
    if (res.status === 401) {
      // 토큰 만료 시 로그아웃
      localStorage.removeItem('ccc_token')
      localStorage.removeItem('ccc_user')
    }
    const text = await res.text().catch(() => res.statusText)
    throw new Error(text || `${res.status}`)
  }
  return res.json()
}

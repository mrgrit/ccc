// 인증 상태 관리
const TOKEN_KEY = 'ccc_token'
const USER_KEY = 'ccc_user'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function getUser(): any | null {
  const u = localStorage.getItem(USER_KEY)
  return u ? JSON.parse(u) : null
}

export function setAuth(token: string, user: any) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function isLoggedIn(): boolean {
  return !!getToken()
}

export function isAdmin(): boolean {
  const u = getUser()
  return u?.role === 'admin' || u?.role === 'instructor'
}

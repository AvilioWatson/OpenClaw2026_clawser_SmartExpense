const STORAGE_KEY = 'smart_expense_jwt'

export function getStoredToken(): string | null {
  return localStorage.getItem(STORAGE_KEY)
}

export function setStoredToken(token: string): void {
  localStorage.setItem(STORAGE_KEY, token)
}

export function clearStoredToken(): void {
  localStorage.removeItem(STORAGE_KEY)
}

type OnUnauthorized = () => void

let onUnauthorized: OnUnauthorized | null = null

export function setOnUnauthorized(handler: OnUnauthorized): void {
  onUnauthorized = handler
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  opts?: { auth?: boolean; handleUnauthorized?: boolean },
): Promise<T> {
  const useAuth = opts?.auth ?? true
  const handleUnauthorized = opts?.handleUnauthorized ?? true

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (useAuth) {
    const token = getStoredToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  const res = await fetch(path, { ...options, headers })

  if (res.status === 401 && handleUnauthorized) {
    clearStoredToken()
    onUnauthorized?.()
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const text = await res.text()
    let message = text
    try {
      const json = JSON.parse(text)
      message = json.error ?? text
    } catch {
      // use raw text
    }
    throw new Error(message)
  }

  return res.json() as Promise<T>
}

export async function login(apiToken: string) {
  const data = await request<import('../types').LoginResponse>(
    '/api/v1/auth/login',
    {
      method: 'POST',
      body: JSON.stringify({ token: apiToken }),
    },
    { auth: false, handleUnauthorized: false },
  )
  setStoredToken(data.access_token)
  return data
}

export async function fetchTransactions() {
  return request<import('../types').Transaction[]>('/api/v1/transactions')
}

export async function fetchCategories() {
  return request<import('../types').Category[]>('/api/v1/categories')
}

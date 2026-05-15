import type {
  Category,
  CategoryBreakdown,
  LoginResponse,
  TransactionFilters,
  TransactionListResponse,
  TransactionSummary,
} from '../types'

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

function buildQuery(filters?: TransactionFilters): string {
  if (!filters) return ''
  const params = new URLSearchParams()
  if (filters.year != null) params.set('year', String(filters.year))
  if (filters.month != null) params.set('month', String(filters.month))
  if (filters.from) params.set('from', filters.from)
  if (filters.to) params.set('to', filters.to)
  if (filters.type) params.set('type', filters.type)
  if (filters.category_id) params.set('category_id', filters.category_id)
  if (filters.q) params.set('q', filters.q)
  if (filters.sort) params.set('sort', filters.sort)
  if (filters.order) params.set('order', filters.order)
  if (filters.limit != null) params.set('limit', String(filters.limit))
  if (filters.offset != null) params.set('offset', String(filters.offset))
  const qs = params.toString()
  return qs ? `?${qs}` : ''
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
  const data = await request<LoginResponse>(
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

export async function fetchTransactions(filters?: TransactionFilters) {
  return request<TransactionListResponse>(
    `/api/v1/transactions${buildQuery(filters)}`,
  )
}

export async function fetchTransactionSummary(filters?: TransactionFilters) {
  return request<TransactionSummary>(
    `/api/v1/transactions/summary${buildQuery(filters)}`,
  )
}

export async function fetchTransactionsByCategory(filters?: TransactionFilters) {
  return request<CategoryBreakdown[]>(
    `/api/v1/transactions/by-category${buildQuery(filters)}`,
  )
}

export async function fetchCategories() {
  return request<Category[]>('/api/v1/categories')
}

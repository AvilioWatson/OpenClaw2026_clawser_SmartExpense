import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  clearStoredToken,
  getStoredToken,
  login as apiLogin,
  setOnUnauthorized,
} from '../api/client'

interface AuthContextValue {
  isAuthenticated: boolean
  telegramId: string | null
  login: (token: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

function parseTelegramId(jwt: string): string | null {
  try {
    const payload = jwt.split('.')[1]
    if (!payload) return null
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
    return decoded.sub ?? null
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(() => getStoredToken())

  const logout = useCallback(() => {
    clearStoredToken()
    setAccessToken(null)
  }, [])

  useEffect(() => {
    setOnUnauthorized(() => {
      setAccessToken(null)
    })
  }, [])

  const login = useCallback(async (token: string) => {
    const res = await apiLogin(token.trim())
    setAccessToken(res.access_token)
  }, [])

  const telegramId = useMemo(
    () => (accessToken ? parseTelegramId(accessToken) : null),
    [accessToken],
  )

  const value = useMemo(
    () => ({
      isAuthenticated: !!accessToken,
      telegramId,
      login,
      logout,
    }),
    [accessToken, telegramId, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

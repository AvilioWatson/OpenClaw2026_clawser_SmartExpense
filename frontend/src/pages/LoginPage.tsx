import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [token, setToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(token)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page login-page">
      <div className="card login-card">
        <h1>Smart Expense</h1>
        <p className="subtitle">
          Paste your API token to sign in. This token works once — after sign-in,
          request a new token if you need to log in again.
        </p>
        <form onSubmit={handleSubmit}>
          <label htmlFor="token">API Token</label>
          <textarea
            id="token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste your token here..."
            rows={4}
            autoComplete="off"
            required
          />
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={loading || !token.trim()}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}

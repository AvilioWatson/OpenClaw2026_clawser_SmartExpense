import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchCategories, fetchTransactions } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import CategoriesTable from '../components/CategoriesTable'
import TransactionsTable from '../components/TransactionsTable'
import type { Category, Transaction } from '../types'

export default function DashboardPage() {
  const { telegramId, logout } = useAuth()
  const navigate = useNavigate()
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const [txns, cats] = await Promise.all([
          fetchTransactions(),
          fetchCategories(),
        ])
        if (!cancelled) {
          setTransactions(txns)
          setCategories(cats)
        }
      } catch (err) {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : 'Failed to load data'
          if (msg === 'Unauthorized') {
            navigate('/login', { replace: true })
          } else {
            setError(msg)
          }
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [navigate])

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="page dashboard-page">
      <header className="dashboard-header">
        <div>
          <h1>Smart Expense</h1>
          {telegramId && (
            <p className="telegram-id">Telegram ID: {telegramId}</p>
          )}
        </div>
        <button type="button" className="btn-secondary" onClick={handleLogout}>
          Log out
        </button>
      </header>

      {loading && <p className="loading">Loading...</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && (
        <>
          <section>
            <h2>Transactions</h2>
            <TransactionsTable transactions={transactions} />
          </section>
          <section>
            <h2>Categories</h2>
            <CategoriesTable categories={categories} />
          </section>
        </>
      )}
    </div>
  )
}

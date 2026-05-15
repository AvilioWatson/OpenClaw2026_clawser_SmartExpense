import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  fetchCategories,
  fetchTransactionSummary,
  fetchTransactions,
  fetchTransactionsByCategory,
} from '../api/client'
import CategoryChart from '../components/CategoryChart'
import CategoriesTable from '../components/CategoriesTable'
import SummaryCards from '../components/SummaryCards'
import TransactionFilters from '../components/TransactionFilters'
import TransactionsTable from '../components/TransactionsTable'
import { useAuth } from '../auth/AuthContext'
import { exportTransactionsCSV } from '../utils/csv'
import type {
  Category,
  CategoryBreakdown,
  Transaction,
  TransactionFilters as Filters,
  TransactionSummary,
} from '../types'

const PAGE_SIZE = 50

const defaultFilters = (): Filters => ({
  sort: 'transaction_date',
  order: 'desc',
  limit: PAGE_SIZE,
})

export default function DashboardPage() {
  const { telegramId, logout } = useAuth()
  const navigate = useNavigate()

  const [draftFilters, setDraftFilters] = useState<Filters>(defaultFilters)
  const [appliedFilters, setAppliedFilters] = useState<Filters>(defaultFilters)

  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [total, setTotal] = useState(0)
  const [summary, setSummary] = useState<TransactionSummary | null>(null)
  const [breakdown, setBreakdown] = useState<CategoryBreakdown[]>([])
  const [categories, setCategories] = useState<Category[]>([])

  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch(() => {})
  }, [])

  const loadData = useCallback(
    async (filters: Filters, append = false, offset = 0) => {
      if (append) {
        setLoadingMore(true)
      } else {
        setLoading(true)
      }
      setError(null)
      try {
        if (append) {
          const txnRes = await fetchTransactions({ ...filters, offset })
          setTransactions((prev) => [...prev, ...txnRes.items])
          setTotal(txnRes.total)
          return
        }
        const [txnRes, sum, chart] = await Promise.all([
          fetchTransactions({ ...filters, offset: 0 }),
          fetchTransactionSummary(filters),
          fetchTransactionsByCategory(filters),
        ])
        setTransactions(txnRes.items)
        setTotal(txnRes.total)
        setSummary(sum)
        setBreakdown(chart)
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load data'
        if (msg === 'Unauthorized') {
          navigate('/login', { replace: true })
        } else {
          setError(msg)
        }
      } finally {
        setLoading(false)
        setLoadingMore(false)
      }
    },
    [navigate],
  )

  useEffect(() => {
    loadData(appliedFilters)
  }, [appliedFilters, loadData])

  function handleApply() {
    setAppliedFilters({ ...draftFilters })
  }

  function handleReset() {
    const f = defaultFilters()
    setDraftFilters(f)
    setAppliedFilters(f)
  }

  function handleLoadMore() {
    loadData(appliedFilters, true, transactions.length)
  }

  function handleExport() {
    exportTransactionsCSV(transactions)
  }

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  const hasMore = transactions.length < total
  const hasActiveFilters =
    appliedFilters.type != null ||
    appliedFilters.category_id != null ||
    appliedFilters.q != null ||
    appliedFilters.from != null ||
    appliedFilters.to != null

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

      <TransactionFilters
        filters={draftFilters}
        categories={categories}
        onChange={setDraftFilters}
        onApply={handleApply}
        onReset={handleReset}
      />

      {error && <p className="error">{error}</p>}

      <section>
        <h2>Summary</h2>
        <SummaryCards summary={summary} loading={loading && !summary} />
      </section>

      <section>
        <h2>Spending by category</h2>
        <CategoryChart breakdown={breakdown} loading={loading && breakdown.length === 0} />
      </section>

      <section>
        <div className="section-header">
          <h2>Transactions</h2>
          <div className="section-actions">
            {!loading && transactions.length > 0 && (
              <button type="button" className="btn-secondary" onClick={handleExport}>
                Export CSV
              </button>
            )}
          </div>
        </div>
        {loading && transactions.length === 0 ? (
          <p className="loading">Loading transactions...</p>
        ) : (
          <>
            <p className="result-count">
              Showing {transactions.length} of {total}
            </p>
            <TransactionsTable
              transactions={transactions}
              hasFilters={hasActiveFilters}
            />
            {hasMore && (
              <button
                type="button"
                className="btn-load-more"
                disabled={loadingMore}
                onClick={handleLoadMore}
              >
                {loadingMore ? 'Loading...' : 'Load more'}
              </button>
            )}
          </>
        )}
      </section>

      <section>
        <h2>Categories</h2>
        <CategoriesTable categories={categories} />
      </section>
    </div>
  )
}

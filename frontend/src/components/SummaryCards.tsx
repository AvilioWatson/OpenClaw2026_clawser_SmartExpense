import type { TransactionSummary } from '../types'

function formatIDR(amount: number): string {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
  }).format(amount)
}

interface Props {
  summary: TransactionSummary | null
  loading?: boolean
}

export default function SummaryCards({ summary, loading }: Props) {
  if (loading) {
    return <p className="loading">Loading summary...</p>
  }
  if (!summary) return null

  return (
    <div className="summary-cards">
      <div className="summary-card">
        <span className="summary-label">Income</span>
        <span className="summary-value income">{formatIDR(summary.total_income)}</span>
      </div>
      <div className="summary-card">
        <span className="summary-label">Expense</span>
        <span className="summary-value expense">{formatIDR(summary.total_expense)}</span>
      </div>
      <div className="summary-card">
        <span className="summary-label">Net</span>
        <span className={`summary-value ${summary.net >= 0 ? 'income' : 'expense'}`}>
          {formatIDR(summary.net)}
        </span>
      </div>
      <div className="summary-card">
        <span className="summary-label">Transactions</span>
        <span className="summary-value">{summary.count}</span>
      </div>
    </div>
  )
}

import type { CategoryBreakdown } from '../types'

function formatIDR(amount: number): string {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    notation: 'compact',
  }).format(amount)
}

interface Props {
  breakdown: CategoryBreakdown[]
  loading?: boolean
}

export default function CategoryChart({ breakdown, loading }: Props) {
  if (loading) {
    return <p className="loading">Loading chart...</p>
  }

  const expenses = breakdown.filter((b) => b.type === 'expense')
  if (expenses.length === 0) {
    return <p className="empty">No expense data for the selected period.</p>
  }

  const max = Math.max(...expenses.map((b) => b.total))

  return (
    <div className="category-chart">
      {expenses.map((b) => (
        <div key={`${b.category_name}-${b.type}`} className="chart-row">
          <div className="chart-label">
            {b.category_icon && <span>{b.category_icon}</span>}
            <span>{b.category_name}</span>
          </div>
          <div className="chart-bar-wrap">
            <div
              className="chart-bar"
              style={{
                width: max > 0 ? `${(b.total / max) * 100}%` : '0%',
                background: b.category_color ?? 'var(--accent)',
              }}
            />
          </div>
          <span className="chart-amount">{formatIDR(b.total)}</span>
        </div>
      ))}
    </div>
  )
}

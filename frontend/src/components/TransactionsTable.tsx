import type { Transaction } from '../types'

function formatAmount(amount: number, type: string): string {
  const formatted = new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
  }).format(amount)
  return type === 'expense' ? `-${formatted}` : formatted
}

interface Props {
  transactions: Transaction[]
  hasFilters?: boolean
}

export default function TransactionsTable({ transactions, hasFilters }: Props) {
  if (transactions.length === 0) {
    return (
      <p className="empty">
        {hasFilters
          ? 'No transactions match your filters. Try adjusting the date range or search.'
          : 'No transactions found.'}
      </p>
    )
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Category</th>
            <th>Type</th>
            <th>Amount</th>
            <th>Description</th>
            <th>Merchant</th>
            <th>Payment</th>
            <th>AI comment</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((t) => (
            <tr key={t.id}>
              <td>{t.transaction_date}</td>
              <td>
                <span className="category-cell">
                  {t.category_icon && <span>{t.category_icon}</span>}
                  {t.category_name}
                </span>
              </td>
              <td>
                <span className={`badge badge-${t.type}`}>{t.type}</span>
              </td>
              <td className={`amount amount-${t.type}`}>
                {formatAmount(t.amount, t.type)}
              </td>
              <td>{t.description ?? '—'}</td>
              <td>{t.merchant ?? '—'}</td>
              <td>{t.payment_method ?? '—'}</td>
              <td className="llm-comment" title={t.llm_comment ?? undefined}>
                {t.llm_comment ? (
                  <span className="llm-comment-text">{t.llm_comment}</span>
                ) : (
                  '—'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

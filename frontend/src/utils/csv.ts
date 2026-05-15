import type { Transaction } from '../types'

export function exportTransactionsCSV(transactions: Transaction[], filename = 'transactions.csv') {
  const headers = [
    'date',
    'category',
    'type',
    'amount',
    'description',
    'merchant',
    'payment_method',
    'notes',
    'tags',
    'llm_comment',
  ]
  const rows = transactions.map((t) => [
    t.transaction_date,
    t.category_name,
    t.type,
    String(t.amount),
    t.description ?? '',
    t.merchant ?? '',
    t.payment_method ?? '',
    t.notes ?? '',
    (t.tags ?? []).join(';'),
    t.llm_comment ?? '',
  ])
  const escape = (v: string) => {
    if (v.includes(',') || v.includes('"') || v.includes('\n')) {
      return `"${v.replace(/"/g, '""')}"`
    }
    return v
  }
  const csv = [headers, ...rows].map((row) => row.map(escape).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

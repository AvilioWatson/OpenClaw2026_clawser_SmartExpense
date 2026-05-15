import type { Category, TransactionFilters as Filters } from '../types'

interface Props {
  filters: Filters
  categories: Category[]
  onChange: (filters: Filters) => void
  onApply: () => void
  onReset: () => void
}

const currentYear = new Date().getFullYear()
const years = Array.from({ length: 6 }, (_, i) => currentYear - i)

export default function TransactionFilters({
  filters,
  categories,
  onChange,
  onApply,
  onReset,
}: Props) {
  function set<K extends keyof Filters>(key: K, value: Filters[K]) {
    onChange({ ...filters, [key]: value })
  }

  const useYearMonth = filters.year != null && filters.from == null && filters.to == null

  return (
    <div className="filters-panel">
      <div className="filters-grid">
        <label>
          Period
          <select
            value={useYearMonth ? 'year' : 'range'}
            onChange={(e) => {
              if (e.target.value === 'year') {
                onChange({ ...filters, year: currentYear, month: undefined, from: undefined, to: undefined })
              } else {
                onChange({ ...filters, year: undefined, month: undefined })
              }
            }}
          >
            <option value="year">Year / Month</option>
            <option value="range">Date range</option>
          </select>
        </label>

        {useYearMonth ? (
          <>
            <label>
              Year
              <select
                value={filters.year ?? ''}
                onChange={(e) => set('year', Number(e.target.value))}
              >
                {years.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </label>
            <label>
              Month
              <select
                value={filters.month ?? ''}
                onChange={(e) =>
                  set('month', e.target.value ? Number(e.target.value) : undefined)
                }
              >
                <option value="">All months</option>
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                  <option key={m} value={m}>
                    {new Date(2000, m - 1).toLocaleString('en', { month: 'long' })}
                  </option>
                ))}
              </select>
            </label>
          </>
        ) : (
          <>
            <label>
              From
              <input
                type="date"
                value={filters.from ?? ''}
                onChange={(e) => set('from', e.target.value || undefined)}
              />
            </label>
            <label>
              To
              <input
                type="date"
                value={filters.to ?? ''}
                onChange={(e) => set('to', e.target.value || undefined)}
              />
            </label>
          </>
        )}

        <label>
          Type
          <select
            value={filters.type ?? ''}
            onChange={(e) => set('type', e.target.value || undefined)}
          >
            <option value="">All</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
        </label>

        <label>
          Category
          <select
            value={filters.category_id ?? ''}
            onChange={(e) => set('category_id', e.target.value || undefined)}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.icon ? `${c.icon} ` : ''}{c.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Search
          <input
            type="search"
            placeholder="Merchant or description"
            value={filters.q ?? ''}
            onChange={(e) => set('q', e.target.value || undefined)}
          />
        </label>

        <label>
          Sort by
          <select
            value={filters.sort ?? 'transaction_date'}
            onChange={(e) => set('sort', e.target.value)}
          >
            <option value="transaction_date">Date</option>
            <option value="amount">Amount</option>
            <option value="category_name">Category</option>
            <option value="created_at">Created</option>
          </select>
        </label>

        <label>
          Order
          <select
            value={filters.order ?? 'desc'}
            onChange={(e) => set('order', e.target.value)}
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </label>
      </div>

      <div className="filters-actions">
        <button type="button" onClick={onApply}>Apply filters</button>
        <button type="button" className="btn-secondary" onClick={onReset}>Reset</button>
      </div>
    </div>
  )
}

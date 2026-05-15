import type { Category } from '../types'

interface Props {
  categories: Category[]
}

export default function CategoriesTable({ categories }: Props) {
  if (categories.length === 0) {
    return <p className="empty">No categories found.</p>
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Icon</th>
            <th>Name</th>
            <th>Type</th>
            <th>Color</th>
            <th>Description</th>
            <th>Order</th>
          </tr>
        </thead>
        <tbody>
          {categories.map((c) => (
            <tr key={c.id}>
              <td>{c.icon ?? '—'}</td>
              <td>{c.name}</td>
              <td>
                <span className={`badge badge-${c.type}`}>{c.type}</span>
              </td>
              <td>
                {c.color ? (
                  <span className="color-swatch" style={{ background: c.color }} />
                ) : (
                  '—'
                )}
              </td>
              <td>{c.description ?? '—'}</td>
              <td>{c.display_order}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

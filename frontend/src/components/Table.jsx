import EmptyState from './EmptyState'
import Spinner from './Spinner'

export default function Table({
  columns,
  data,
  loading = false,
  error = null,
  emptyTitle = 'No records found',
  emptyDescription = 'Try adjusting your filters or create a new record.',
  keyField = 'id',
}) {
  if (loading) {
    return <Spinner label="Loading records..." />
  }

  if (error) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {error}
      </div>
    )
  }

  if (!data || data.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
        <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className={`px-4 py-3 ${col.headerClassName || ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {data.map((row) => (
            <tr key={row[keyField]} className="hover:bg-slate-50/70 transition-colors">
              {columns.map((col) => (
                <td key={col.key} className={`px-4 py-3 text-slate-700 ${col.cellClassName || ''}`}>
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

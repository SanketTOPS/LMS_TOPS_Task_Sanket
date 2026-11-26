import Button from './Button'

export default function Pagination({ page, totalPages, total, onPageChange }) {
  if (totalPages <= 1 && total === 0) return null

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 pt-4 text-sm text-slate-600">
      <span>
        Page <strong className="text-slate-900">{page}</strong> of{' '}
        <strong className="text-slate-900">{totalPages}</strong> ({total} total)
      </span>
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </Button>
        <Button
          variant="secondary"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  )
}

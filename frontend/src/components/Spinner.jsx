export default function Spinner({ size = 'md', label = 'Loading...' }) {
  const dims = size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-8 w-8' : 'h-6 w-6'
  return (
    <div className="flex items-center justify-center gap-2 py-6 text-sm text-slate-500">
      <span
        className={`${dims} animate-spin rounded-full border-2 border-indigo-600 border-t-transparent`}
      />
      {label && <span>{label}</span>}
    </div>
  )
}

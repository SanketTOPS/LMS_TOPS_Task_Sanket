export default function Input({
  label,
  id,
  error,
  hint,
  className = '',
  ...props
}) {
  const inputId = id || props.name
  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="mb-1.5 block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`block w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 shadow-sm transition focus:outline-none focus:ring-2 ${
          error
            ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-200'
            : 'border-slate-300 focus:border-indigo-500 focus:ring-indigo-200'
        } disabled:bg-slate-100 disabled:text-slate-500 ${className}`}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-rose-600">{error}</p>}
      {!error && hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  )
}

export default function Card({ title, subtitle, actions, children, className = '', hover = false }) {
  return (
    <div
      className={`rounded-2xl border border-slate-200/80 bg-white shadow-sm ${
        hover ? 'card-hover' : ''
      } ${className}`}
    >
      {(title || subtitle || actions) && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
          <div>
            {title && <h2 className="text-base font-bold text-slate-900">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  )
}

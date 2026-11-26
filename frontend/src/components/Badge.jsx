const TONE_CLASSES = {
  neutral: 'bg-slate-100 text-slate-800 border border-slate-200',
  primary: 'bg-blue-50 text-blue-800 border border-blue-200',
  info: 'bg-blue-50 text-blue-800 border border-blue-200',
  accent: 'bg-orange-50 text-orange-700 border border-orange-200',
  success: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
  warning: 'bg-amber-50 text-amber-800 border border-amber-200',
  danger: 'bg-rose-50 text-rose-700 border border-rose-200',
}

export default function Badge({ children, tone, variant, className = '' }) {
  const key = tone || variant || 'neutral'
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${TONE_CLASSES[key] || TONE_CLASSES.neutral} ${className}`}
    >
      {children}
    </span>
  )
}

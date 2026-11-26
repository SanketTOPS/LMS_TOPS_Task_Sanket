const TONE_CLASSES = {
  neutral: 'bg-slate-100 text-slate-800 border border-slate-200',
  primary: 'bg-brand-50 text-brand-700 border border-brand-200',
  info: 'bg-brand-50 text-brand-700 border border-brand-200',
  accent: 'bg-accent-50 text-accent-700 border border-accent-200',
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

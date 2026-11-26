const VARIANT_CLASSES = {
  primary:
    'bg-brand-700 text-white hover:bg-brand-800 focus:ring-brand-500 border-transparent shadow-sm',
  accent:
    'bg-accent-500 text-white hover:bg-accent-600 focus:ring-accent-500 border-transparent shadow-sm',
  secondary:
    'bg-white text-slate-800 hover:bg-slate-50 focus:ring-brand-500 border-slate-300 shadow-sm',
  outlineLight:
    'bg-white/15 text-white hover:bg-white/25 focus:ring-white border-white/35 backdrop-blur-sm shadow-sm',
  danger:
    'bg-rose-600 text-white hover:bg-rose-700 focus:ring-rose-500 border-transparent shadow-sm',
  ghost:
    'bg-transparent text-slate-700 hover:bg-slate-100 focus:ring-slate-400 border-transparent',
}

const SIZE_CLASSES = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  type = 'button',
  loading = false,
  disabled = false,
  className = '',
  ...props
}) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg border font-semibold transition-all duration-150 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-60 ${VARIANT_CLASSES[variant] || VARIANT_CLASSES.primary} ${SIZE_CLASSES[size] || SIZE_CLASSES.md} ${className}`}
      {...props}
    >
      {loading && (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  )
}

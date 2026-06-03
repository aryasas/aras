// claude-sonnet-4-6
// Unified status badge. Covers ERP doc statuses (Draft/Confirmed/Posted/Cancelled),
// task statuses (running/success/failed/error), and generic pass/fail strings.

const SUCCESS_TERMS = ['success', 'done', 'approved', 'posted', 'confirmed', 'active', 'completed', 'paid']
const DANGER_TERMS  = ['fail', 'error', 'reject', 'cancel', 'void', 'denied', 'expired']
const WARN_TERMS    = ['warn', 'pending', 'draft', 'partial', 'review', 'hold']
const INFO_TERMS    = ['run', 'progress', 'processing', 'queued', 'open']

function resolveColor(status: string): string {
  const v = status.toLowerCase()
  if (SUCCESS_TERMS.some((t) => v.includes(t))) return 'var(--success, #2e7d32)'
  if (DANGER_TERMS.some((t) => v.includes(t)))  return 'var(--danger, #c62828)'
  if (WARN_TERMS.some((t) => v.includes(t)))    return 'var(--warn, #b45309)'
  if (INFO_TERMS.some((t) => v.includes(t)))    return 'var(--accent)'
  return 'var(--text-3)'
}

interface StatusBadgeProps {
  status?: string | null
  className?: string
  /** Show as a pill with background instead of plain coloured text */
  pill?: boolean
}

export function StatusBadge({ status, className = '', pill = false }: StatusBadgeProps) {
  const label = (status || 'unknown').toLowerCase()
  const color = resolveColor(label)

  if (pill) {
    return (
      <span
        className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${className}`}
        style={{ color, background: `color-mix(in oklch, ${color} 14%, var(--surface))`, border: `1px solid color-mix(in oklch, ${color} 28%, var(--line))` }}
      >
        {label}
      </span>
    )
  }

  return (
    <span className={`arc-id shrink-0 ${className}`} style={{ color }}>
      {label}
    </span>
  )
}

/** Standalone function for cases where the colour is needed without JSX (e.g. inline style on a parent). */
export function statusColor(status?: string | null): string {
  return resolveColor((status || '').toLowerCase())
}

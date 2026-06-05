// claude-sonnet-4-6
// Pure presentation helpers extracted from ListView.tsx so the cell-formatting and
// status logic is independently testable and ListView stays focused on data + layout.
import { FormattingService } from '../services/FormattingService'

export type FieldValue =
  | string | number | boolean | null | Record<string, unknown> | unknown[]

export type ApiError = Error & {
  name?: string
  response?: { data?: { detail?: string } }
}

// claude-sonnet-4-6
export const getErrorMessage = (err: unknown, fallback: string) =>
  (err as ApiError).response?.data?.detail || fallback

// claude-sonnet-4-6
export const isCanceledError = (err: unknown) => (err as ApiError).name === 'CanceledError'

export const roleColors: Record<string, string> = {
  customer: 'bg-sky-50 text-sky-700 border-sky-100',
  supplier: 'bg-amber-50 text-amber-700 border-amber-100',
  member: 'bg-violet-50 text-violet-700 border-violet-100',
  other: 'bg-[var(--aras-panel-soft)] text-[var(--aras-muted)] border-[var(--aras-border)]',
}

export const STATUS_GLYPH: Record<string, { ch: string; color: string }> = {
  in_progress: { ch: '◐', color: 'var(--accent)' },
  'in progress': { ch: '◐', color: 'var(--accent)' },
  draft:       { ch: '○', color: 'var(--text-3)' },
  open:        { ch: '○', color: 'var(--text-3)' },
  in_review:   { ch: '△', color: '#d97706' },
  'in review': { ch: '△', color: '#d97706' },
  pending:     { ch: '△', color: '#d97706' },
  released:    { ch: '●', color: '#059669' },
  active:      { ch: '●', color: '#059669' },
  posted:      { ch: '●', color: '#059669' },
  approved:    { ch: '●', color: '#059669' },
  blocked:     { ch: '✕', color: '#e11d48' },
  cancelled:   { ch: '✕', color: '#e11d48' },
  rejected:    { ch: '✕', color: '#e11d48' },
}

// claude-opus-4-7 (moved by claude-sonnet-4-6)
export function StatusGlyph({ value }: { value: FieldValue }) {
  const key = String(value ?? '').toLowerCase().trim()
  const g = STATUS_GLYPH[key] || { ch: '○', color: 'var(--text-3)' }
  return <span style={{ color: g.color, fontFamily: 'Geist Mono, ui-monospace, monospace', fontSize: 13 }}>{g.ch}</span>
}

// claude-sonnet-4-6 (extracted from ListView)
export const renderCellValue = (value: FieldValue, type: string, fieldName?: string) => {
  if (value === null || value === undefined) return <span className="text-[var(--aras-muted)]">-</span>
  if (fieldName === 'status' || fieldName === 'state' || type === 'boolean') {
    const rawLabel = typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)
    return <span className="inline-flex items-center gap-2 text-[13px] font-medium capitalize text-[var(--text-2)]"><StatusGlyph value={rawLabel} />{rawLabel.replace(/_/g, ' ')}</span>
  }
  if (fieldName === 'role') {
    return <span className={`inline-flex rounded-[var(--aras-radius)] border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${roleColors[String(value)] || roleColors.other}`}>{String(value)}</span>
  }
  switch (type) {
    case 'currency': return <span className="text-[var(--aras-text)] font-bold">{FormattingService.formatCurrency(Number(value || 0))}</span>
    case 'date':
    case 'datetime': return FormattingService.formatDate(String(value))
    default:
      if (typeof value === 'object') return <span className="text-[var(--aras-muted)] italic text-xs">{JSON.stringify(value).slice(0, 60)}</span>
      return String(value)
  }
}

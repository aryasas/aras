// claude-sonnet-4-6
// Thin helpers over FormattingService for use in views.
// Always use these instead of inline toLocaleString / toFixed / new Date().toLocaleString().
import { FormattingService } from '../aras-core/services/FormattingService'

export function formatCurrency(value: number, currency?: string): string {
  if (value == null || !Number.isFinite(value)) return '—'
  try { return FormattingService.formatCurrency(value, currency) } catch { return String(value) }
}

export function fmtDate(value: string | Date | null | undefined): string {
  if (!value) return '—'
  try { return FormattingService.formatDate(value) } catch { return String(value) }
}

export function fmtDateTime(value: string | Date | null | undefined): string {
  if (!value) return '—'
  try {
    return FormattingService.formatDateTime(value)
  } catch { return String(value) }
}

export function fmtCurrency(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  try { return formatCurrency(value) } catch { return String(value) }
}

export function fmtNumber(value: number | null | undefined, decimals = 2): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return value.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

export function fmtPercent(value: number | null | undefined, decimals = 1): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${value.toFixed(decimals)}%`
}

export function fmtFileSize(bytes: number | null | undefined): string {
  if (bytes == null || bytes < 0) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

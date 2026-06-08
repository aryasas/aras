// claude-sonnet-4-6
// Tests for the pure cell-render helpers extracted from ListView. These were previously
// untestable inline closures; extraction lets us lock the formatting contract directly.
import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import { renderCellValue, getErrorMessage, isCanceledError } from '../components/listView.helpers'

vi.mock('../services/FormattingService', () => ({
  FormattingService: {
    formatCurrency: (n: number) => `$${n.toFixed(2)}`,
    formatDate: (s: string) => `D(${s})`,
  },
}))

const text = (node: React.ReactNode) => {
  if (typeof node === 'string') return node
  const { container } = render(<>{node}</>)
  return container.textContent ?? ''
}

describe('renderCellValue', () => {
  it('renders a dash for null/undefined', () => {
    expect(text(renderCellValue(null, 'string'))).toBe('-')
    expect(text(renderCellValue(undefined as never, 'string'))).toBe('-')
  })

  it('renders booleans as Yes/No with a status glyph', () => {
    expect(text(renderCellValue(true, 'boolean'))).toContain('Yes')
    expect(text(renderCellValue(false, 'boolean'))).toContain('No')
  })

  it('humanizes underscored status values', () => {
    expect(text(renderCellValue('in_progress', 'string', 'status'))).toContain('in progress')
  })

  it('formats currency via FormattingService', () => {
    expect(text(renderCellValue(1500, 'currency'))).toBe('$1500.00')
  })

  it('formats dates via FormattingService', () => {
    expect(text(renderCellValue('2026-06-05', 'date'))).toBe('D(2026-06-05)')
  })

  it('stringifies and truncates object values', () => {
    const out = text(renderCellValue({ a: 1, b: 'x'.repeat(100) }, 'string'))
    expect(out.length).toBeLessThanOrEqual(60)
  })

  it('falls back to String() for plain scalars', () => {
    expect(text(renderCellValue(42, 'number'))).toBe('42')
  })
})

describe('error helpers', () => {
  it('getErrorMessage prefers the API detail, else the fallback', () => {
    expect(getErrorMessage({ response: { data: { detail: 'boom' } } }, 'fb')).toBe('boom')
    expect(getErrorMessage(new Error('x'), 'fb')).toBe('fb')
  })

  it('isCanceledError detects axios cancellations', () => {
    expect(isCanceledError({ name: 'CanceledError' })).toBe(true)
    expect(isCanceledError(new Error('other'))).toBe(false)
  })
})

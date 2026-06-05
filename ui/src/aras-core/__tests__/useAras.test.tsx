// claude-sonnet-4-6
// useAras is the per-view convenience hook (notify/confirm/api/appName/formatters).
// We mock the context providers and assert the derived/forwarded values: appName from
// the route, and the formatter delegations.
import { describe, it, expect, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type { ReactNode } from 'react'

const notify = { success: vi.fn() }
const confirm = vi.fn()

vi.mock('../contexts/NotificationContext', () => ({ useNotify: () => notify }))
vi.mock('../contexts/ConfirmContext', () => ({ useConfirm: () => confirm }))
vi.mock('../../lib/api', () => ({ default: { get: vi.fn() } }))
vi.mock('../../lib/formatters', () => ({
  formatCurrency: (n: number) => `CUR(${n})`,
}))

import { useAras } from '../hooks/useAras'

const wrapperFor = (route: string) =>
  ({ children }: { children: ReactNode }) => (
    <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter>
  )

describe('useAras', () => {
  it('derives appName from the first path segment', () => {
    const { result } = renderHook(() => useAras(), { wrapper: wrapperFor('/accounting/invoices/5') })
    expect(result.current.appName).toBe('accounting')
  })

  it('returns null appName at the root path', () => {
    const { result } = renderHook(() => useAras(), { wrapper: wrapperFor('/') })
    expect(result.current.appName).toBeNull()
  })

  it('exposes notify, confirm and api', () => {
    const { result } = renderHook(() => useAras(), { wrapper: wrapperFor('/x') })
    expect(result.current.notify).toBe(notify)
    expect(result.current.confirm).toBe(confirm)
    expect(result.current.api).toBeDefined()
  })

  it('delegates formatCurrency to the shared formatter', () => {
    const { result } = renderHook(() => useAras(), { wrapper: wrapperFor('/x') })
    expect(result.current.formatCurrency(1500)).toBe('CUR(1500)')
  })

  it('formatDate produces a locale date string', () => {
    const { result } = renderHook(() => useAras(), { wrapper: wrapperFor('/x') })
    const out = result.current.formatDate('2026-06-05T00:00:00Z')
    expect(typeof out).toBe('string')
    expect(out.length).toBeGreaterThan(0)
  })
})

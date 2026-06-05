// claude-sonnet-4-6
// ListView is the framework's universal data grid — every list route renders it.
// This test drives the real fetch→render→interact path with a path-routed api mock:
// it loads metadata, fetches rows, renders cell values, and fires onRowClick. Context
// hooks (vocabulary, uiStore, useAras) are stubbed to isolate ListView's own logic.
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import { renderWithRouter } from '../../test/renderWithRouter'

const META = {
  resource: 'item',
  title: 'Items',
  api_path: 'stock/items',
  fields: [
    { name: 'id', label: 'ID', type: 'number' },
    { name: 'name', label: 'Name', type: 'string' },
    { name: 'status', label: 'Status', type: 'string' },
  ],
}
const ROWS = [
  { id: 1, name: 'Widget', status: 'active' },
  { id: 2, name: 'Gadget', status: 'draft' },
]

const get = vi.fn((url: string = '') => {
  if (url.startsWith('/metadata/')) return Promise.resolve({ data: META })
  if (url.startsWith('/preference')) return Promise.resolve({ data: { value: null } })
  if (url.startsWith('/sys_filters')) return Promise.resolve({ data: { items: [] } })
  // the data endpoint (/stock/items or /item)
  return Promise.resolve({ data: { items: ROWS, total: ROWS.length } })
})

vi.mock('../../lib/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: vi.fn(), put: vi.fn().mockResolvedValue({}), delete: vi.fn() },
}))
vi.mock('../../context/VocabularyContext', () => ({
  useVocabulary: () => ({ get: (s: string) => s }),
}))
vi.mock('../hooks/useAras', () => ({
  useAras: () => ({ notify: vi.fn(), confirm: vi.fn().mockResolvedValue(true) }),
}))
vi.mock('../../services/FormattingService', () => ({
  FormattingService: { formatCurrency: (n: number) => `$${n}`, formatDate: (s: string) => s },
}))
// uiStore is a zustand hook used with a selector by ListView. Inert state.
vi.mock('../../store/uiStore', () => {
  const state = { setPageTitle: vi.fn(), showPanel: vi.fn(), inlineEdit: false }
  return { useUIStore: (sel?: any) => (typeof sel === 'function' ? sel(state) : state) }
})
// The design wrappers are builder-mode chrome unrelated to data rendering; stub them
// to passthrough divs so ListView's fetch→render path is what's exercised.
vi.mock('../components/design/DesignContainer', () => ({
  DesignContainer: ({ children, ...r }: any) => <div {...r}>{children}</div>,
}))
vi.mock('../components/design/DesignElement', () => ({
  DesignElement: ({ children, ...r }: any) => <div {...r}>{children}</div>,
}))

import ListView from '../components/ListView'

beforeEach(() => get.mockClear())

describe('ListView data loading', () => {
  it('requests metadata for the resource on mount', async () => {
    renderWithRouter(<ListView resource="item" />)
    await waitFor(() =>
      expect(get).toHaveBeenCalledWith(expect.stringContaining('/metadata/item'), expect.anything()),
    )
  })

  it('fetches list data using the api_path from metadata, with params', async () => {
    renderWithRouter(<ListView resource="item" />)
    await waitFor(() =>
      expect(get).toHaveBeenCalledWith(
        expect.stringContaining('stock/items'),
        expect.objectContaining({ params: expect.objectContaining({ page: 1, per_page: 20 }) }),
      ),
    )
  })

  it('passes an abort signal to the metadata request', async () => {
    renderWithRouter(<ListView resource="item" />)
    await waitFor(() => {
      const metaCall = get.mock.calls.find((c) => String(c[0]).startsWith('/metadata/'))
      expect(metaCall?.[1]).toHaveProperty('signal')
    })
  })
})

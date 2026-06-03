import { useCallback, useEffect, useMemo, useState } from 'react'
import { useModel } from './useModel'

type SortOrder = 'asc' | 'desc'
type ListFilters = Record<string, unknown>
type ListResponse<T> = {
  items: T[]
  total: number
  pages: number
  raw: unknown
}

// gpt-codex
export function useListView<T>(resource: string) {
  const { fetchList, list, loading } = useModel<T>(resource)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [sortField, setSortField] = useState<string | null>('id')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [filters, setFiltersState] = useState<ListFilters>({})

  const normalizedFilters = useMemo(() => {
    return Object.fromEntries(
      Object.entries(filters).filter(([, value]) => value !== undefined && value !== null && value !== '')
    )
  }, [filters])

  const load = useCallback(async () => {
    const params: Record<string, unknown> = {
      page,
      per_page: pageSize,
      sort: sortField ?? 'id',
      order: sortOrder,
    }

    if (Object.keys(normalizedFilters).length > 0) {
      params.filters = JSON.stringify(normalizedFilters)
    }

    try {
      const response = await fetchList(params) as ListResponse<T>
      setTotal(response.total)
      return response
    } catch {
      return null
    }
  }, [fetchList, normalizedFilters, page, pageSize, sortField, sortOrder])

  useEffect(() => {
    void load()
  }, [load])

  const setSort = useCallback((field: string | null, order?: SortOrder) => {
    setPage(1)
    setSortField(field)
    setSortOrder((current) => {
      if (!field) return 'asc'
      if (order) return order
      if (sortField === field) return current === 'asc' ? 'desc' : 'asc'
      return 'asc'
    })
  }, [sortField])

  const setFilters = useCallback((next: ListFilters) => {
    setPage(1)
    setFiltersState(next)
  }, [])

  const refresh = useCallback(() => {
    void load()
  }, [load])

  return {
    rows: list,
    loading,
    page,
    pageSize,
    total,
    sortField,
    sortOrder,
    filters: normalizedFilters,
    setPage,
    setPageSize: (next: number) => {
      setPage(1)
      setPageSize(next)
    },
    setSort,
    setFilters,
    refresh,
  }
}

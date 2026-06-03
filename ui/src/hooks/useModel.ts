import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useAras } from '../aras-core/hooks/useAras'
import { cleanResourcePath } from '../lib/resourceUtils'

type ListResponse<T> = {
  items: T[]
  total: number
  pages: number
  raw: unknown
}

type RecordLike = Record<string, unknown>

function getErrorMessage(error: unknown) {
  if (error && typeof error === 'object') {
    const response = (error as { response?: { data?: RecordLike | string } }).response?.data
    if (typeof response === 'string') return response
    if (response && typeof response === 'object') {
      const responseData = response as RecordLike
      if (typeof responseData.detail === 'string') return responseData.detail
      if (typeof responseData.message === 'string') return responseData.message
      if (typeof responseData.error === 'string') return responseData.error
      if (responseData.error && typeof responseData.error === 'object' && typeof (responseData.error as RecordLike).message === 'string') {
        return (responseData.error as RecordLike).message as string
      }
    }
    if (typeof (error as { message?: unknown }).message === 'string') {
      return (error as { message: string }).message
    }
  }

  if (typeof error === 'string') return error
  return 'Request failed'
}

function isRecord(value: unknown): value is RecordLike {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function normalizeListResponse<T>(value: unknown): ListResponse<T> {
  if (Array.isArray(value)) {
    return {
      items: value as T[],
      total: value.length,
      pages: 1,
      raw: value,
    }
  }

  if (isRecord(value)) {
    const items = Array.isArray(value.items)
      ? value.items
      : Array.isArray(value.data)
        ? value.data
        : []
    const total = typeof value.total === 'number' ? value.total : items.length
    const pages = typeof value.pages === 'number' ? value.pages : (total > 0 ? 1 : 0)

    return {
      items: items as T[],
      total,
      pages,
      raw: value,
    }
  }

  return {
    items: [],
    total: 0,
    pages: 0,
    raw: value,
  }
}

// gpt-codex
export function useModel<T>(resource: string, id?: string | number) {
  const { api } = useAras()
  const cleanResource = useMemo(() => cleanResourcePath(resource), [resource])
  const baseUrl = useMemo(() => `/${cleanResource}`, [cleanResource])

  const [data, setData] = useState<T | null>(null)
  const [list, setList] = useState<T[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const requestSeq = useRef(0)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  useEffect(() => {
    setData(null)
    setList([])
    setError(null)
  }, [baseUrl])

  const beginRequest = useCallback(() => {
    requestSeq.current += 1
    setLoading(true)
    setError(null)
    return requestSeq.current
  }, [])

  const endRequest = useCallback((seq: number) => {
    if (!mountedRef.current || seq !== requestSeq.current) return
    setLoading(false)
  }, [])

  const fetch = useCallback(async () => {
    if (id == null || id === '') {
      setData(null)
      setError(null)
      return null
    }

    const seq = beginRequest()
    try {
      const response = await api.get<T>(`${baseUrl}/${encodeURIComponent(String(id))}`)
      if (mountedRef.current && seq === requestSeq.current) {
        setData(response.data)
      }
      return response.data
    } catch (err) {
      if (mountedRef.current && seq === requestSeq.current) {
        setError(getErrorMessage(err))
      }
      throw err
    } finally {
      endRequest(seq)
    }
  }, [api, baseUrl, beginRequest, endRequest, id])

  const fetchList = useCallback(async (params?: Record<string, unknown>) => {
    const seq = beginRequest()
    try {
      const response = await api.get<unknown>(baseUrl, { params })
      const normalized = normalizeListResponse<T>(response.data)
      if (mountedRef.current && seq === requestSeq.current) {
        setList(normalized.items)
      }
      return normalized
    } catch (err) {
      if (mountedRef.current && seq === requestSeq.current) {
        setError(getErrorMessage(err))
      }
      throw err
    } finally {
      endRequest(seq)
    }
  }, [api, baseUrl, beginRequest, endRequest])

  useEffect(() => {
    if (id == null || id === '') {
      setData(null)
      return
    }

    void fetch()
  }, [fetch, id])

  const save = useCallback(async (payload: Partial<T>) => {
    const seq = beginRequest()
    try {
      const response = id == null || id === ''
        ? await api.post<T>(baseUrl, payload)
        : await api.patch<T>(`${baseUrl}/${encodeURIComponent(String(id))}`, payload)

      const saved = response.data
      if (mountedRef.current && seq === requestSeq.current) {
        setData(saved)
        setList((current) => {
          if (!isRecord(saved) || !('id' in saved)) return current
          const savedId = saved.id
          const index = current.findIndex((item) => isRecord(item) && String(item.id) === String(savedId))
          if (index >= 0) {
            const next = [...current]
            next[index] = saved
            return next
          }
          return [saved, ...current]
        })
      }
      return saved
    } catch (err) {
      if (mountedRef.current && seq === requestSeq.current) {
        setError(getErrorMessage(err))
      }
      throw err
    } finally {
      endRequest(seq)
    }
  }, [api, baseUrl, beginRequest, endRequest, id])

  const remove = useCallback(async (targetId: string | number) => {
    const seq = beginRequest()
    try {
      await api.delete(`${baseUrl}/${encodeURIComponent(String(targetId))}`)
      if (mountedRef.current && seq === requestSeq.current) {
        setList((current) => current.filter((item) => !(isRecord(item) && String(item.id) === String(targetId))))
        if (id != null && String(id) === String(targetId)) {
          setData(null)
        }
      }
    } catch (err) {
      if (mountedRef.current && seq === requestSeq.current) {
        setError(getErrorMessage(err))
      }
      throw err
    } finally {
      endRequest(seq)
    }
  }, [api, baseUrl, beginRequest, endRequest, id])

  return {
    data,
    list,
    loading,
    error,
    fetch,
    fetchList,
    save,
    remove,
  }
}

export type { ListResponse }

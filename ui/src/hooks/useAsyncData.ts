import { useCallback, useEffect, useRef, useState } from 'react'

type AsyncState<T> = {
  data: T | null
  loading: boolean
  error: string | null
  reload: () => void
}

function getErrorMessage(err: unknown): string {
  if (typeof err === 'string') return err
  if (err && typeof err === 'object') {
    const e = err as Record<string, unknown>
    const resp = (e.response as Record<string, unknown> | undefined)?.data
    if (typeof resp === 'string') return resp
    if (resp && typeof resp === 'object') {
      const d = resp as Record<string, unknown>
      if (typeof d.detail === 'string') return d.detail
      if (typeof d.message === 'string') return d.message
      if (typeof d.error === 'string') return d.error
    }
    if (typeof e.message === 'string') return e.message
  }
  return 'Request failed'
}

// claude-sonnet-4-6
export function useAsyncData<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  const mountedRef = useRef(true)
  const seqRef = useRef(0)

  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const stableFetcher = useCallback(fetcher, deps)

  useEffect(() => {
    let cancelled = false
    const seq = ++seqRef.current
    setLoading(true)
    setError(null)

    stableFetcher()
      .then((result) => {
        if (!cancelled && mountedRef.current && seq === seqRef.current) {
          setData(result)
        }
      })
      .catch((err) => {
        if (!cancelled && mountedRef.current && seq === seqRef.current) {
          setError(getErrorMessage(err))
        }
      })
      .finally(() => {
        if (!cancelled && mountedRef.current && seq === seqRef.current) {
          setLoading(false)
        }
      })

    return () => { cancelled = true }
  // tick is the reload trigger; stableFetcher rebuilds when deps change
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stableFetcher, tick])

  const reload = useCallback(() => setTick((n) => n + 1), [])

  return { data, loading, error, reload }
}

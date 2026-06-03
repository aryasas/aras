import { useCallback, useEffect, useMemo, useState } from 'react'
import { useModel } from './useModel'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function cloneValue<T>(value: T): T {
  if (!isRecord(value)) return value
  return JSON.parse(JSON.stringify(value))
}

function isEqual(a: unknown, b: unknown) {
  return JSON.stringify(a) === JSON.stringify(b)
}

// gpt-codex
export function useFormState<T>(resource: string, id?: string | number) {
  const model = useModel<T>(resource, id)
  const [values, setValues] = useState<Partial<T>>({})
  const [initialValues, setInitialValues] = useState<Partial<T>>({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const nextValues = (model.data && isRecord(model.data) ? cloneValue(model.data) : {}) as Partial<T>
    setValues(nextValues)
    setInitialValues(nextValues)
    setError(model.error)
  }, [model.data, model.error])

  const dirty = useMemo(() => !isEqual(values, initialValues), [initialValues, values])

  const setValue = useCallback((field: keyof T, value: unknown) => {
    setValues((current) => ({
      ...current,
      [field]: value,
    }))
  }, [])

  const reset = useCallback(() => {
    setValues(cloneValue(initialValues))
    setError(null)
  }, [initialValues])

  const submit = useCallback(async () => {
    setSaving(true)
    setError(null)
    try {
      const saved = await model.save(values)
      const nextValues = (saved && isRecord(saved) ? cloneValue(saved) : values) as Partial<T>
      setValues(nextValues)
      setInitialValues(nextValues)
      return saved
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Request failed'
      setError(message)
      throw err
    } finally {
      setSaving(false)
    }
  }, [model, values])

  return {
    values,
    dirty,
    saving,
    error,
    setValue,
    reset,
    submit,
  }
}

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

export default function ArasFormView({ app, resource, id, fields = [], redirectOnSave }) {
  const qc = useQueryClient()
  const isNew = !id

  const { data: obj, isLoading } = useQuery({
    queryKey: [app, resource, id],
    queryFn: () => api.get(app, resource, id),
    enabled: !isNew,
  })

  const [form, setForm] = useState({})
  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (obj) setForm(obj)
  }, [obj])

  const save = useMutation({
    mutationFn: data => isNew
      ? api.create(app, resource, data)
      : api.update(app, resource, id, data),
    onSuccess: result => {
      qc.invalidateQueries([app, resource])
      const dest = redirectOnSave ?? `/admin/${app}/${resource}/`
      window.location.href = dest
    },
    onError: err => setErrors({ _global: err.message }),
  })

  function handleSubmit(e) {
    e.preventDefault()
    setErrors({})
    save.mutate(form)
  }

  if (isLoading) return <div className="p-4 text-gray-400">Loading...</div>

  return (
    <form onSubmit={handleSubmit} className="p-4 max-w-2xl space-y-4">
      {errors._global && (
        <div className="text-red-600 text-sm bg-red-50 border border-red-200 rounded px-3 py-2">
          {errors._global}
        </div>
      )}

      {fields.map(field => (
        <div key={field.key}>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {field.label ?? field.key}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          {field.type === 'textarea' ? (
            <textarea
              value={form[field.key] ?? ''}
              onChange={e => setForm(f => ({ ...f, [field.key]: e.target.value }))}
              rows={3}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          ) : field.type === 'select' ? (
            <select
              value={form[field.key] ?? ''}
              onChange={e => setForm(f => ({ ...f, [field.key]: e.target.value }))}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">— Select —</option>
              {(field.choices ?? []).map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          ) : (
            <input
              type={field.type ?? 'text'}
              value={form[field.key] ?? ''}
              onChange={e => setForm(f => ({ ...f, [field.key]: e.target.value }))}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          )}
          {errors[field.key] && (
            <p className="text-red-500 text-xs mt-1">{errors[field.key]}</p>
          )}
        </div>
      ))}

      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={save.isPending}
          className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {save.isPending ? 'Saving...' : 'Save'}
        </button>
        <a
          href={`/admin/${app}/${resource}/`}
          className="px-4 py-2 border rounded text-sm text-gray-600 hover:bg-gray-50"
        >
          Cancel
        </a>
      </div>
    </form>
  )
}

// Thin wrapper — same-origin, uses Flask session cookie automatically
export async function apiFetch(path, options = {}) {
  console.log(`[api] ${options.method ?? 'GET'} ${path}`)
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    credentials: 'same-origin',
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    console.error(`[api] error ${res.status}:`, err)
    throw new Error(err.error || res.statusText)
  }
  const data = await res.json()
  console.log(`[api] success ${path}:`, data)
  return data
}

export const api = {
  list: (app, resource, params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return apiFetch(`/api/${app}/${resource}/${qs ? '?' + qs : ''}`)
  },
  get: (app, resource, id) => apiFetch(`/api/${app}/${resource}/${id}/`),
  create: (app, resource, data) =>
    apiFetch(`/api/${app}/${resource}/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (app, resource, id, data) =>
    apiFetch(`/api/${app}/${resource}/${id}/`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (app, resource, id) =>
    apiFetch(`/api/${app}/${resource}/${id}/`, { method: 'DELETE' }),

  // UI System
  uiInit: () => apiFetch('/admin/api/ui/init'),
  resourceConfig: (resource) => apiFetch(`/admin/api/ui/resource-config/${resource}`),
}

import React, { useEffect, useMemo, useState } from 'react'
import { Play, Loader2, Search, ChevronRight } from 'lucide-react'
import api from '../../lib/api'
import DataGrid from '../../aras-core/components/DataGrid'
import { getOpenApiJsonUrl } from '../../lib/apiDocs'

// claude-opus-4-8
// Self-rendering API console: reads /openapi.json and generates a live request form
// for every operation from its parameter + requestBody JSON-schema. Fires the call,
// renders the response. No per-endpoint code — add a backend route, it appears here.

type JsonSchema = {
  type?: string
  format?: string
  enum?: unknown[]
  items?: JsonSchema
  properties?: Record<string, JsonSchema>
  required?: string[]
  $ref?: string
  default?: unknown
  description?: string
  anyOf?: JsonSchema[]
  allOf?: JsonSchema[]
}
type Param = { name: string; in: 'query' | 'path' | 'header'; required?: boolean; schema?: JsonSchema; description?: string }
type Operation = {
  method: string
  path: string
  summary?: string
  tags: string[]
  parameters: Param[]
  bodySchema?: JsonSchema
}
type OpenAPI = {
  paths: Record<string, Record<string, {
    summary?: string
    tags?: string[]
    parameters?: Param[]
    requestBody?: { content?: Record<string, { schema?: JsonSchema }> }
  }>>
  components?: { schemas?: Record<string, JsonSchema> }
}

const METHODS = ['get', 'post', 'put', 'patch', 'delete']
const methodColor: Record<string, string> = {
  get: 'bg-emerald-100 text-emerald-700', post: 'bg-blue-100 text-blue-700',
  put: 'bg-amber-100 text-amber-700', patch: 'bg-amber-100 text-amber-700', delete: 'bg-red-100 text-red-700',
}

// claude-opus-4-8
// Resolve a (possibly $ref) schema against components.schemas, flattening allOf/anyOf.
function resolveSchema(schema: JsonSchema | undefined, schemas: Record<string, JsonSchema>, depth = 0): JsonSchema {
  if (!schema || depth > 6) return {}
  if (schema.$ref) {
    const name = schema.$ref.split('/').pop() || ''
    return resolveSchema(schemas[name], schemas, depth + 1)
  }
  if (schema.allOf?.length) {
    const merged: JsonSchema = { type: 'object', properties: {}, required: [] }
    for (const part of schema.allOf) {
      const r = resolveSchema(part, schemas, depth + 1)
      Object.assign(merged.properties!, r.properties)
      if (r.required) merged.required!.push(...r.required)
    }
    return merged
  }
  if (schema.anyOf?.length) {
    // pick first non-null branch (FastAPI Optional[x] → anyOf[x, null])
    const branch = schema.anyOf.find(s => s.type !== 'null') || schema.anyOf[0]
    return resolveSchema(branch, schemas, depth + 1)
  }
  return schema
}

// claude-opus-4-8
function defaultFor(schema: JsonSchema): unknown {
  if (schema.default !== undefined) return schema.default
  switch (schema.type) {
    case 'integer': case 'number': return ''
    case 'boolean': return false
    case 'array': return ''
    case 'object': return {}
    default: return ''
  }
}

// claude-opus-4-8
function parseSpec(spec: OpenAPI): Operation[] {
  const schemas = spec.components?.schemas || {}
  const ops: Operation[] = []
  for (const [path, methods] of Object.entries(spec.paths || {})) {
    for (const m of METHODS) {
      const op = methods[m]
      if (!op) continue
      let bodySchema: JsonSchema | undefined
      const json = op.requestBody?.content?.['application/json']?.schema
      if (json) bodySchema = resolveSchema(json, schemas)
      ops.push({
        method: m, path,
        summary: op.summary,
        tags: op.tags?.length ? op.tags : ['untagged'],
        parameters: (op.parameters || []).map(p => ({ ...p, schema: resolveSchema(p.schema, schemas) })),
        bodySchema,
      })
    }
  }
  return ops
}

// claude-opus-4-8
export default function ApiConsole() {
  const [ops, setOps] = useState<Operation[]>([])
  const [filter, setFilter] = useState('')
  const [active, setActive] = useState<Operation | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(getOpenApiJsonUrl())
      .then(r => r.json())
      .then((spec: OpenAPI) => setOps(parseSpec(spec)))
      .catch(() => setError('Could not load /openapi.json'))
  }, [])

  const grouped = useMemo(() => {
    const f = filter.toLowerCase()
    const match = ops.filter(o => !f || o.path.toLowerCase().includes(f) || (o.summary || '').toLowerCase().includes(f) || o.tags.some(t => t.toLowerCase().includes(f)))
    const g: Record<string, Operation[]> = {}
    for (const o of match) for (const t of o.tags) (g[t] ||= []).push(o)
    return Object.entries(g).sort((a, b) => a[0].localeCompare(b[0]))
  }, [ops, filter])

  if (error) return <div className="px-4 py-3 rounded bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-5 h-[calc(100vh-260px)]">
      {/* Operation list */}
      <div className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius-lg)] flex flex-col overflow-hidden">
        <div className="p-3 border-b border-[var(--line)]">
          <div className="flex items-center gap-2 px-2.5 py-1.5 bg-[var(--surface-2)] rounded-[var(--radius)] border border-[var(--line)]">
            <Search size={14} className="text-[var(--text-3)]" />
            <input
              value={filter}
              onChange={e => setFilter(e.target.value)}
              placeholder="Filter endpoints…"
              className="bg-transparent text-sm flex-1 outline-none text-[var(--text)]"
            />
            <span className="text-xs text-[var(--text-3)] font-mono">{ops.length}</span>
          </div>
        </div>
        <div className="overflow-auto flex-1">
          {grouped.map(([tag, list]) => (
            <div key={tag}>
              <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-[var(--text-3)] bg-[var(--surface-2)] sticky top-0">{tag}</div>
              {list.map(o => (
                <button
                  key={`${o.method}:${o.path}`}
                  onClick={() => setActive(o)}
                  className={`w-full flex items-center gap-2 px-3 py-1.5 text-left hover:bg-[var(--surface-2)] transition-colors border-l-2 ${active === o ? 'border-[var(--accent)] bg-[var(--surface-2)]' : 'border-transparent'}`}
                >
                  <span className={`text-[9px] font-black uppercase px-1.5 py-0.5 rounded ${methodColor[o.method]}`}>{o.method}</span>
                  <span className="text-xs font-mono text-[var(--text-2)] truncate flex-1">{o.path}</span>
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Request panel */}
      <div className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius-lg)] overflow-auto">
        {active ? <RequestPanel op={active} /> : (
          <div className="h-full flex items-center justify-center text-[var(--text-3)] text-sm">
            <div className="text-center"><ChevronRight className="mx-auto mb-2 opacity-40" /> Select an endpoint</div>
          </div>
        )}
      </div>
    </div>
  )
}

// claude-opus-4-8
function RequestPanel({ op }: { op: Operation }) {
  const [pathVals, setPathVals] = useState<Record<string, string>>({})
  const [queryVals, setQueryVals] = useState<Record<string, string>>({})
  const [body, setBody] = useState<Record<string, unknown>>({})
  const [response, setResponse] = useState<{ status: number; data: unknown; ms: number } | null>(null)
  const [error, setError] = useState('')
  const [running, setRunning] = useState(false)

  // Reset form when operation changes
  useEffect(() => {
    setPathVals({})
    setQueryVals({})
    const init: Record<string, unknown> = {}
    if (op.bodySchema?.properties) for (const [k, s] of Object.entries(op.bodySchema.properties)) init[k] = defaultFor(s)
    setBody(init)
    setResponse(null)
    setError('')
  }, [op])

  const pathParams = op.parameters.filter(p => p.in === 'path')
  const queryParams = op.parameters.filter(p => p.in === 'query')

  const send = async () => {
    setRunning(true); setError(''); setResponse(null)
    let url = op.path.replace(/^\/api\/v1/, '')
    for (const p of pathParams) url = url.replace(`{${p.name}}`, encodeURIComponent(pathVals[p.name] || ''))
    const params: Record<string, string> = {}
    for (const p of queryParams) if (queryVals[p.name] !== undefined && queryVals[p.name] !== '') params[p.name] = queryVals[p.name]
    const t0 = performance.now()
    try {
      const hasBody = op.method !== 'get' && op.method !== 'delete' && op.bodySchema
      const res = await api.request({
        method: op.method,
        url,
        params,
        data: hasBody ? coerceBody(body, op.bodySchema!) : undefined,
      })
      setResponse({ status: res.status, data: res.data, ms: Math.round(performance.now() - t0) })
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: unknown }; message?: string }
      if (err.response) setResponse({ status: err.response.status || 0, data: err.response.data, ms: Math.round(performance.now() - t0) })
      else setError(err.message || 'request failed')
    } finally {
      setRunning(false)
    }
  }

  const rows = asRows(response?.data)

  return (
    <div className="p-5 space-y-4">
      <div className="flex items-center gap-2">
        <span className={`text-[10px] font-black uppercase px-2 py-1 rounded ${methodColor[op.method]}`}>{op.method}</span>
        <code className="font-mono text-sm text-[var(--text)] font-bold">{op.path}</code>
      </div>
      {op.summary && <p className="text-sm text-[var(--text-3)]">{op.summary}</p>}

      {pathParams.length > 0 && (
        <Group title="Path">
          {pathParams.map(p => (
            <Field key={p.name} label={p.name} required={p.required} schema={p.schema}
              value={pathVals[p.name] ?? ''} onChange={v => setPathVals(s => ({ ...s, [p.name]: v }))} />
          ))}
        </Group>
      )}
      {queryParams.length > 0 && (
        <Group title="Query">
          {queryParams.map(p => (
            <Field key={p.name} label={p.name} required={p.required} schema={p.schema}
              value={queryVals[p.name] ?? ''} onChange={v => setQueryVals(s => ({ ...s, [p.name]: v }))} />
          ))}
        </Group>
      )}
      {op.bodySchema?.properties && (
        <Group title="Body">
          {Object.entries(op.bodySchema.properties).map(([k, s]) => (
            <Field key={k} label={k} required={op.bodySchema!.required?.includes(k)} schema={s}
              value={body[k] as never} onChange={v => setBody(b => ({ ...b, [k]: v }))} object />
          ))}
        </Group>
      )}

      <button onClick={send} disabled={running}
        className="flex items-center gap-2 px-5 py-2 bg-[var(--accent)] text-white rounded-[var(--radius)] font-bold text-sm hover:opacity-90 disabled:opacity-50">
        {running ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />} Send
      </button>

      {error && <div className="px-3 py-2 rounded bg-red-50 text-red-700 text-sm font-mono border border-red-200">{error}</div>}
      {response && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className={`px-2 py-0.5 rounded font-bold ${response.status < 300 ? 'bg-emerald-100 text-emerald-700' : response.status < 500 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'}`}>{response.status}</span>
            <span className="text-[var(--text-3)]">{response.ms}ms</span>
          </div>
          {rows ? <DataGrid columns={Object.keys(rows[0] || {})} rows={rows} maxHeight={360} />
            : <pre className="text-xs font-mono bg-[var(--surface-2)] p-3 rounded border border-[var(--line)] overflow-auto max-h-96 text-[var(--text)]">{JSON.stringify(response.data, null, 2)}</pre>}
        </div>
      )}
    </div>
  )
}

// claude-opus-4-8
// Renders one input from its JSON-schema type. `object` mode handles typed body coercion.
function Field({ label, required, schema, value, onChange, object }: {
  label: string; required?: boolean; schema?: JsonSchema; value: string | boolean; onChange: (v: never) => void; object?: boolean
}) {
  const s = schema || {}
  const type = s.type
  const base = 'w-full px-2.5 py-1.5 rounded border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/40'
  let input: React.ReactNode
  if (s.enum?.length) {
    input = (
      <select value={String(value)} onChange={e => onChange(e.target.value as never)} className={base}>
        <option value="">—</option>
        {s.enum.map(o => <option key={String(o)} value={String(o)}>{String(o)}</option>)}
      </select>
    )
  } else if (type === 'boolean') {
    input = <input type="checkbox" checked={!!value} onChange={e => onChange(e.target.checked as never)} className="w-4 h-4 accent-[var(--accent)]" />
  } else if (type === 'integer' || type === 'number') {
    input = <input type="number" value={String(value ?? '')} onChange={e => onChange((object ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value) as never)} className={base} />
  } else if (type === 'object' || type === 'array') {
    input = <textarea rows={2} value={typeof value === 'string' ? value : JSON.stringify(value)} onChange={e => onChange(e.target.value as never)} placeholder={type === 'array' ? '[…] JSON' : '{…} JSON'} className={base + ' resize-y'} />
  } else {
    input = <input type="text" value={String(value ?? '')} onChange={e => onChange(e.target.value as never)} className={base} />
  }
  return (
    <label className="block">
      <span className="text-xs font-semibold text-[var(--text-2)] mb-1 flex items-center gap-1">
        {label}{required && <span className="text-red-500">*</span>}
        {type && <span className="text-[var(--text-3)] font-normal font-mono">{type}</span>}
      </span>
      {input}
    </label>
  )
}

const Group = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <div className="space-y-2.5">
    <h4 className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-3)]">{title}</h4>
    {children}
  </div>
)

// claude-opus-4-8
// Coerce string-typed form values to their schema type before sending.
function coerceBody(body: Record<string, unknown>, schema: JsonSchema): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  const props = schema.properties || {}
  for (const [k, v] of Object.entries(body)) {
    const t = props[k]?.type
    if (v === '' && !schema.required?.includes(k)) continue
    if ((t === 'object' || t === 'array') && typeof v === 'string') {
      try { out[k] = v.trim() ? JSON.parse(v) : (t === 'array' ? [] : {}) } catch { out[k] = v }
    } else if (t === 'integer' || t === 'number') {
      out[k] = v === '' ? null : Number(v)
    } else {
      out[k] = v
    }
  }
  return out
}

// claude-opus-4-8
// If response is a flat array of objects, render as grid; else fall back to JSON.
function asRows(data: unknown): Record<string, unknown>[] | null {
  if (Array.isArray(data) && data.length && typeof data[0] === 'object' && data[0] !== null && !Array.isArray(data[0])) {
    return data as Record<string, unknown>[]
  }
  const items = (data as { items?: unknown })?.items
  if (Array.isArray(items) && items.length && typeof items[0] === 'object') return items as Record<string, unknown>[]
  return null
}

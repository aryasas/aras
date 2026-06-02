import { useEffect, useMemo, useState } from 'react'
import { Activity, AlertTriangle, CheckCircle2, ExternalLink, RefreshCw, Server, Smartphone } from 'lucide-react'
import api from '../../lib/api'
import { getApiDocsUrl, getOpenApiJsonUrl } from '../../lib/apiDocs'
import { devApi } from './devApi'

type CheckState = 'checking' | 'ok' | 'warn' | 'down'

type Health = {
  backend: CheckState
  appTools: CheckState
  openapi: CheckState
  expo: CheckState
  errors: number
  requests: number
  p95: number
  message: string
}

const defaultExpoUrl = () => localStorage.getItem('template-builder:expo-url') || import.meta.env.VITE_EXPO_PREVIEW_URL || 'http://localhost:8081'

export default function DevHealthPanel() {
  const [expoUrl, setExpoUrl] = useState(defaultExpoUrl)
  const [health, setHealth] = useState<Health>({
    backend: 'checking',
    appTools: 'checking',
    openapi: 'checking',
    expo: 'checking',
    errors: 0,
    requests: 0,
    p95: 0,
    message: 'Checking developer surfaces...',
  })

  const load = async () => {
    setHealth(current => ({ ...current, backend: 'checking', appTools: 'checking', openapi: 'checking', expo: 'checking', message: 'Checking developer surfaces...' }))
    const [info, metrics, openapi, expo] = await Promise.allSettled([
      api.get(devApi.info),
      api.get(devApi.metrics),
      fetch(getOpenApiJsonUrl(), { credentials: 'same-origin' }),
      fetch(expoUrl, { mode: 'no-cors' }),
    ])

    const metricsData = metrics.status === 'fulfilled' ? metrics.value.data : null
    const backend = info.status === 'fulfilled' ? 'ok' : 'down'
    const appTools = metrics.status === 'fulfilled' ? ((metricsData?.total_errors || 0) > 0 ? 'warn' : 'ok') : 'down'
    const openapiState = openapi.status === 'fulfilled' ? 'ok' : 'down'
    const expoState = expo.status === 'fulfilled' ? 'ok' : 'warn'
    const down = [backend, appTools, openapiState].filter(state => state === 'down').length

    setHealth({
      backend,
      appTools,
      openapi: openapiState,
      expo: expoState,
      errors: metricsData?.total_errors || 0,
      requests: metricsData?.total_requests || 0,
      p95: metricsData?.latency_p95 || 0,
      message: down ? `${down} required developer surface${down === 1 ? '' : 's'} unavailable.` : 'Core developer surfaces are reachable.',
    })
  }

  useEffect(() => { load().catch(() => {}) }, [])

  useEffect(() => {
    localStorage.setItem('template-builder:expo-url', expoUrl)
  }, [expoUrl])

  const overall = useMemo<CheckState>(() => {
    if ([health.backend, health.appTools, health.openapi].includes('down')) return 'down'
    if ([health.appTools, health.expo].includes('warn')) return 'warn'
    if ([health.backend, health.appTools, health.openapi, health.expo].includes('checking')) return 'checking'
    return 'ok'
  }, [health])

  return (
    <section className={`mb-5 rounded-[var(--radius-lg)] border p-4 ${
      overall === 'down' ? 'border-red-200 bg-red-50' : overall === 'warn' ? 'border-amber-200 bg-amber-50' : 'border-[var(--line)] bg-[var(--surface)]'
    }`}>
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <StatusIcon state={overall} />
            <h2 className="text-sm font-black text-[var(--text)]">DevTools Health</h2>
            <span className="text-xs font-bold text-[var(--text-3)]">{health.message}</span>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 md:grid-cols-4 xl:grid-cols-7">
            <Check label="Backend" value="/api/v1/dev/info" state={health.backend} icon={<Server size={13} />} />
            <Check label="App Tools" value="/api/v1/dev/dev/*" state={health.appTools} icon={<Activity size={13} />} />
            <Check label="OpenAPI" value="/openapi.json" state={health.openapi} icon={<ExternalLink size={13} />} />
            <Check label="Expo" value={expoUrl.replace(/^https?:\/\//, '')} state={health.expo} icon={<Smartphone size={13} />} />
            <Metric label="Requests" value={String(health.requests)} />
            <Metric label="Errors" value={String(health.errors)} tone={health.errors ? 'warn' : 'ok'} />
            <Metric label="p95" value={`${health.p95} ms`} tone={health.p95 > 800 ? 'warn' : 'ok'} />
          </div>
        </div>
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <input
            value={expoUrl}
            onChange={(event) => setExpoUrl(event.target.value)}
            className="h-9 min-w-[220px] flex-1 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 text-xs font-semibold text-[var(--text)] outline-none focus:border-[var(--accent)] xl:w-64 xl:flex-none"
            placeholder="Expo preview URL"
          />
          <button onClick={load} className="flex h-9 items-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 text-xs font-black text-[var(--text)] hover:bg-[var(--surface-2)]">
            <RefreshCw size={13} />
            Check
          </button>
          <a href={getApiDocsUrl()} target="_blank" rel="noopener noreferrer" className="flex h-9 items-center gap-2 rounded-[var(--radius)] bg-[var(--accent)] px-3 text-xs font-black text-white hover:opacity-90">
            <ExternalLink size={13} />
            Swagger
          </a>
        </div>
      </div>
    </section>
  )
}

function StatusIcon({ state }: { state: CheckState }) {
  if (state === 'ok') return <CheckCircle2 size={17} className="text-emerald-600" />
  if (state === 'down') return <AlertTriangle size={17} className="text-red-600" />
  if (state === 'warn') return <AlertTriangle size={17} className="text-amber-600" />
  return <RefreshCw size={17} className="animate-spin text-[var(--text-3)]" />
}

function Check({ label, value, state, icon }: { label: string; value: string; state: CheckState; icon: React.ReactNode }) {
  return (
    <div className="min-w-0 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-2">
      <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.12em] text-[var(--text-3)]">{icon}{label}</div>
      <div className="mt-1 flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${state === 'ok' ? 'bg-emerald-500' : state === 'down' ? 'bg-red-500' : state === 'warn' ? 'bg-amber-500' : 'bg-slate-300'}`} />
        <span className="truncate font-mono text-[11px] font-bold text-[var(--text)]">{value}</span>
      </div>
    </div>
  )
}

function Metric({ label, value, tone = 'ok' }: { label: string; value: string; tone?: 'ok' | 'warn' }) {
  return (
    <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-2">
      <div className="text-[10px] font-black uppercase tracking-[0.12em] text-[var(--text-3)]">{label}</div>
      <div className={`mt-1 text-sm font-black ${tone === 'warn' ? 'text-amber-700' : 'text-[var(--text)]'}`}>{value}</div>
    </div>
  )
}

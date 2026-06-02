import React, { useEffect, useState } from 'react'
import { Cpu, Activity, Boxes, AlertTriangle, Trash2 } from 'lucide-react'
import api from '../../lib/api'
import DataGrid from '../../aras-core/components/DataGrid'
import { devApi } from './devApi'

// claude-opus-4-8
type SysInfo = { os: string; os_release: string; cpu_count: number; python_version: string; memory: { total: number; available: number; percent: number }; process: { memory_usage: number; cpu_percent: number; threads: number; uptime_seconds: number } }
type Metrics = { uptime_seconds: number; total_requests: number; total_errors: number; error_rate: number; rate_per_second: number; latency_p50: number; latency_p95: number; latency_p99: number }
type AppStatus = { name: string; label: string; type: string; models_count: number; routers_count: number }
type ErrorEntry = Record<string, unknown>

const mb = (b: number) => `${(b / 1048576).toFixed(0)} MB`
const hms = (s: number) => `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`

// claude-opus-4-8
export default function SystemTab() {
  const [sys, setSys] = useState<SysInfo | null>(null)
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [apps, setApps] = useState<AppStatus[]>([])
  const [config, setConfig] = useState<Record<string, string>>({})
  const [errors, setErrors] = useState<ErrorEntry[]>([])
  const [loaded, setLoaded] = useState(false)
  const [loadError, setLoadError] = useState('')

  const load = async () => {
    setLoaded(false)
    setLoadError('')
    const [s, m, a, c, e] = await Promise.allSettled([
      api.get(devApi.systemInfo), api.get(devApi.metrics), api.get(devApi.appsStatus),
      api.get(devApi.config), api.get(devApi.errors),
    ])
    if (s.status === 'fulfilled') setSys(s.value.data)
    if (m.status === 'fulfilled') setMetrics(m.value.data)
    if (a.status === 'fulfilled') setApps(a.value.data)
    if (c.status === 'fulfilled') setConfig(c.value.data)
    if (e.status === 'fulfilled') setErrors(e.value.data)
    if ([s, m, a, c, e].every(result => result.status === 'rejected')) setLoadError('System endpoints did not respond. Check API server/authentication.')
    setLoaded(true)
  }

  const clearErrors = async () => {
    await api.delete(devApi.errors)
    setErrors([])
  }

  useEffect(() => { load() }, [])

  return (
    <div className="space-y-6">
      {loadError && <div className="rounded-[var(--radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{loadError}</div>}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card icon={<Cpu size={18} />} title="System">
          {sys ? (
            <dl className="space-y-1.5 text-sm">
              <Row k="OS" v={`${sys.os} ${sys.os_release}`} />
              <Row k="Python" v={sys.python_version} />
              <Row k="CPU cores" v={String(sys.cpu_count)} />
              <Row k="Memory" v={`${sys.memory.percent}% of ${mb(sys.memory.total)}`} />
              <Row k="Process RSS" v={mb(sys.process.memory_usage)} />
              <Row k="Threads" v={String(sys.process.threads)} />
              <Row k="Uptime" v={hms(sys.process.uptime_seconds)} />
            </dl>
          ) : <Skel loaded={loaded} />}
        </Card>

        <Card icon={<Activity size={18} />} title="Live Metrics">
          {metrics ? (
            <dl className="space-y-1.5 text-sm">
              <Row k="Requests" v={String(metrics.total_requests)} />
              <Row k="Errors" v={`${metrics.total_errors} (${metrics.error_rate}%)`} />
              <Row k="Rate/s" v={String(metrics.rate_per_second)} />
              <Row k="p50 / p95 / p99" v={`${metrics.latency_p50} / ${metrics.latency_p95} / ${metrics.latency_p99} ms`} />
            </dl>
          ) : <Skel loaded={loaded} />}
        </Card>

        <Card icon={<Boxes size={18} />} title="Loaded Apps">
          <div className="space-y-1.5 text-sm">
            {apps.length ? apps.map(a => (
              <div key={a.name} className="flex justify-between">
                <span className="font-semibold text-[var(--text)]">{a.label}</span>
                <span className="text-[var(--text-3)] font-mono text-xs">{a.models_count}m · {a.routers_count}r</span>
              </div>
            )) : <Skel loaded={loaded} />}
          </div>
        </Card>
      </div>

      <Card icon={<AlertTriangle size={18} />} title={`Recent Errors (${errors.length})`} action={
        errors.length ? (
          <button onClick={clearErrors} className="flex items-center gap-1.5 text-xs text-red-600 hover:text-red-700 font-semibold">
            <Trash2 size={13} /> Clear
          </button>
        ) : undefined
      }>
        <DataGrid columns={errors.length ? Object.keys(errors[0]) : []} rows={errors} empty="No errors logged" maxHeight={260} />
      </Card>

      <Card icon={<Cpu size={18} />} title="Environment Config">
        <DataGrid
          columns={['key', 'value']}
          rows={Object.entries(config).map(([key, value]) => ({ key, value }))}
          empty="No config"
          maxHeight={260}
        />
      </Card>
    </div>
  )
}

// claude-opus-4-8
function Card({ icon, title, children, action }: { icon: React.ReactNode; title: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="bg-[var(--surface)] p-5 rounded-[var(--radius-lg)] border border-[var(--line)] shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-[var(--text)]">{icon}<h3 className="font-black text-sm">{title}</h3></div>
        {action}
      </div>
      {children}
    </div>
  )
}
const Row = ({ k, v }: { k: string; v: string }) => (
  <div className="flex justify-between"><dt className="text-[var(--text-3)]">{k}</dt><dd className="font-mono text-[var(--text)]">{v}</dd></div>
)
const Skel = ({ loaded = false }: { loaded?: boolean }) => <div className="text-[var(--text-3)] text-sm py-2">{loaded ? 'Unavailable' : 'Loading…'}</div>

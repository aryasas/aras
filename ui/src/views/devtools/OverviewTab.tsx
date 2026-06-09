import { useEffect, useState, type ReactNode } from 'react'
import { Activity, AlertTriangle, Boxes, CalendarDays, Cpu, Database, GitBranch, GitCompare, HelpCircle, Layout, RefreshCw, Route, Settings, Users } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../../lib/api'
import ArasTable from '../../aras-core/components/ArasTable'
import { MetadataService } from '../../aras-core/services/MetadataService'
import { useUIStore } from '../../store/uiStore'
import { useAras } from '../../aras-core/hooks/useAras'
import TenantSwitcher from '../TenantSwitcher'
import SystemTab from './SystemTab'
import { devApi } from './devApi'

interface DbStat {
  table: string
  rows: number | string
}

interface FrameworkInfo {
  version: string
  engine: string
  apps_discovered: string[]
  total_models: number
}

export default function OverviewTab() {
  const [info, setInfo] = useState<FrameworkInfo | null>(null)
  const [stats, setStats] = useState<DbStat[]>([])
  const [syncing, setSyncing] = useState(false)
  const setPageTitle = useUIStore((state) => state.setPageTitle)
  const { designMode, toggleDesignMode } = useUIStore()
  const navigate = useNavigate()
  const { notify } = useAras()

  useEffect(() => {
    setPageTitle('Developer Tools', 'Internal framework inspection and maintenance utilities.', 'SYSTEM / DEV')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  const fetchData = async () => {
    try {
      const [infoRes, statsRes] = await Promise.all([
        api.get(devApi.info),
        api.get(devApi.stats),
      ])
      setInfo(infoRes.data)
      setStats(statsRes.data)
    } catch (error) {
      console.error('Failed to fetch dev tools data', error)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleSync = async () => {
    setSyncing(true)
    try {
      await api.post(devApi.sync)
      MetadataService.clearCache()
      await fetchData()
    } catch {
      notify('Sync failed', 'error')
    } finally {
      setSyncing(false)
    }
  }

  const dbStatColumns = [
    { key: 'table', field: 'table', label: 'Table Name', render: (v: any) => <code className="rounded bg-[var(--surface-2)] px-2 py-0.5 text-xs font-bold text-[var(--accent)]">{String(v)}</code> },
    { key: 'rows', field: 'rows', label: 'Row Count', align: 'right' as const, render: (v: any) => <span className="font-mono text-sm font-bold text-[var(--text)]">{Number(v).toLocaleString()}</span> },
  ]

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 min-w-0">
      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--line)] sm:grid-cols-3 lg:grid-cols-5">
        <StatCell icon={<Cpu size={16} />} label="Engine" value={info ? `${info.engine} ${info.version}` : '—'} />
        <StatCell icon={<Boxes size={16} />} label="Apps" value={info ? String(info.apps_discovered.length) : '—'} />
        <StatCell icon={<GitCompare size={16} />} label="Models" value={info ? String(info.total_models) : '—'} />
        <StatCell icon={<Database size={16} />} label="Tables" value={String(stats.length)} />
        <StatCell
          icon={<AlertTriangle size={16} />}
          label="Errors"
          value={String(stats.find((s) => s.table === 'dev_error_logs')?.rows || 0)}
          tone={(Number(stats.find((s) => s.table === 'dev_error_logs')?.rows) || 0) > 0 ? 'warn' : 'default'}
        />
      </div>

      <div className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-xs font-black uppercase tracking-[0.18em] text-[var(--text-3)]">Quick actions</h2>
          <label className="flex cursor-pointer items-center gap-2 text-xs font-bold text-[var(--text-2)]">
            <span>Design Mode</span>
            <span
              onClick={toggleDesignMode}
              className={`flex h-5 w-9 items-center rounded-full p-0.5 transition-colors ${designMode ? 'bg-[var(--accent)]' : 'bg-[var(--muted)]'}`}
            >
              <span className={`h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${designMode ? 'translate-x-4' : 'translate-x-0'}`} />
            </span>
          </label>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
          <ActionChip
            icon={<RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />}
            label="Sync Now"
            sub="Force update"
            primary
            disabled={syncing}
            onClick={handleSync}
          />
          <ActionChip
            icon={<Layout size={16} />}
            label="Builder"
            sub="Layout annotator"
            badge
            onClick={() => {
              const last = localStorage.getItem('template-studio:last') || ''
              const ref = (() => {
                try {
                  const u = new URL(document.referrer)
                  return u.origin === window.location.origin ? u.pathname : ''
                } catch {
                  return ''
                }
              })()
              const from = ref || last
              navigate(from ? `/dev/template-builder?from=${encodeURIComponent(from)}` : '/dev/template-builder')
            }}
          />
          <ActionChip icon={<Route size={16} />} label="Routes" sub="Explorer" onClick={() => navigate('/admin/dev/routes-debug')} />
          <ActionChip icon={<Activity size={16} />} label="Tasks" sub="Queue" onClick={() => navigate('/dev/tasks')} />
          <ActionChip icon={<CalendarDays size={16} />} label="Heatmap" sub="Activity" onClick={() => navigate('/dev/activity-heatmap')} />
          <ActionChip icon={<HelpCircle size={16} />} label="Dev Help" sub="Reference" onClick={() => navigate('/dev/help')} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <TenantSwitcher />
        <div className="lg:col-span-2 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-[var(--radius)] bg-[var(--surface-2)] text-[var(--accent)]"><Cpu size={18} /></span>
            <h2 className="text-base font-black text-[var(--text)]">Framework Info</h2>
          </div>
          {info ? (
            <div className="grid grid-cols-1 gap-x-8 sm:grid-cols-2">
              <InfoRow label="Engine Version" value={info.version} />
              <InfoRow label="Engine Type" value={info.engine} />
              <InfoRow label="Apps Discovered" value={info.apps_discovered.length.toString()} />
              <InfoRow label="Total Models" value={info.total_models.toString()} />
            </div>
          ) : (
            <div className="animate-pulse space-y-3">
              <div className="h-4 w-3/4 rounded bg-[var(--surface-2)]" />
              <div className="h-4 w-1/2 rounded bg-[var(--surface-2)]" />
            </div>
          )}
        </div>
      </div>

      <section>
        <h2 className="mb-3 text-xs font-black uppercase tracking-[0.18em] text-[var(--text-3)]">Runtime</h2>
        <SystemTab />
      </section>

      <section>
        <h2 className="mb-3 text-xs font-black uppercase tracking-[0.18em] text-[var(--text-3)]">Registries</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <RegistryCard title="System Users" count={stats.find((s) => s.table === 'core_users')?.rows as number || 0} icon={<Users size={22} />} to="/dev/users" color="slate" />
          <RegistryCard title="System Settings" count={stats.find((s) => s.table === 'core_settings')?.rows as number || 0} icon={<Settings size={22} />} to="/admin/settings" color="slate" />
          <RegistryCard title="Handoff Runs" count={stats.find((s) => s.table === 'dev_handoff_runs')?.rows as number || 0} icon={<GitBranch size={22} />} color="slate" to="/admin/dev/handoff" />
          <RegistryCard title="Template Annotations" count={stats.find((s) => s.table === 'dev_template_annotations')?.rows as number || 0} icon={<Layout size={22} />} to="/dev/template-annotations" color="slate" />
        </div>
      </section>

      <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6 shadow-sm">
        <div className="mb-4 flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-[var(--radius)] bg-[var(--surface-2)] text-[var(--accent)]"><Database size={18} /></span>
          <h2 className="text-base font-black text-[var(--text)]">Database Statistics</h2>
          <span className="ml-auto text-xs font-bold text-[var(--text-3)]">{stats.length} tables</span>
        </div>
        <div className="overflow-hidden rounded-[var(--radius)] border border-[var(--line)]">
          <ArasTable columns={dbStatColumns} rows={stats} rowKey={(stat) => stat.table} />
        </div>
      </section>
    </div>
  )
}

function StatCell({ icon, label, value, tone = 'default' }: {
  icon: ReactNode
  label: string
  value: string
  tone?: 'default' | 'warn'
}) {
  return (
    <div className="bg-[var(--surface)] p-4">
      <div className="flex items-center gap-1.5 text-[var(--text-3)]">
        <span className={tone === 'warn' ? 'text-amber-500' : ''}>{icon}</span>
        <span className="text-[10px] font-black uppercase tracking-[0.16em]">{label}</span>
      </div>
      <div className={`mt-1.5 truncate text-lg font-black ${tone === 'warn' ? 'text-amber-500' : 'text-[var(--text)]'}`}>{value}</div>
    </div>
  )
}

function ActionChip({ icon, label, sub, onClick, primary, badge, disabled }: {
  icon: ReactNode
  label: string
  sub: string
  onClick: () => void
  primary?: boolean
  badge?: boolean
  disabled?: boolean
}) {
  const base = 'group flex items-center gap-3 rounded-[var(--radius)] border p-3 text-left transition-all disabled:opacity-50'
  const skin = primary
    ? 'border-[var(--accent)] bg-[var(--accent)] text-white hover:opacity-90'
    : 'border-[var(--line)] bg-[var(--surface-2)] text-[var(--text)] hover:border-[var(--accent)]'
  return (
    <button onClick={onClick} disabled={disabled} className={`${base} ${skin}`}>
      <span className={`relative grid h-8 w-8 shrink-0 place-items-center rounded-[var(--radius)] ${primary ? 'bg-white/15' : 'bg-[var(--surface)] text-[var(--accent)]'} transition-transform group-hover:scale-110`}>
        {icon}
        {badge && (
          <span className="absolute -right-1 -top-1 flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-pink-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-pink-500" />
          </span>
        )}
      </span>
      <span className="min-w-0">
        <span className="block text-sm font-black leading-tight">{label}</span>
        <span className={`block text-[11px] font-medium ${primary ? 'text-white/70' : 'text-[var(--text-3)]'}`}>{sub}</span>
      </span>
    </button>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-[var(--line)] py-2 last:border-0">
      <span className="text-sm text-[var(--text-3)]">{label}</span>
      <span className="text-sm font-bold text-[var(--text)]">{value}</span>
    </div>
  )
}

function RegistryCard({ title, count, icon, to, color }: {
  title: string
  count: number
  icon: ReactNode
  to: string
  color: string
}) {
  const colorClasses: Record<string, string> = {
    indigo: 'bg-indigo-50 text-indigo-600',
    purple: 'bg-purple-50 text-purple-600',
    blue: 'bg-blue-50 text-blue-600',
    slate: 'bg-[var(--surface-2)] text-[var(--text-2)]',
    emerald: 'bg-emerald-50 text-emerald-600',
  }

  return (
    <Link to={to} className="group cursor-pointer rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-lg">
      <div className={`mb-3 w-fit rounded-[var(--radius)] p-3 transition-transform group-hover:scale-110 ${colorClasses[color]}`}>
        {icon}
      </div>
      <h3 className="mb-1 text-sm font-black leading-tight text-[var(--text)]">{title}</h3>
      <div className="mt-2 flex items-end justify-between">
        <span className="text-2xl font-black text-[var(--text)]">{count}</span>
        <span className="text-xs font-black uppercase tracking-widest text-[var(--accent)]">Browse →</span>
      </div>
    </Link>
  )
}

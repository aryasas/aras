import React, { useState, useEffect } from 'react'
import { Database, RefreshCw, Cpu, Layout, Users, Settings, GitBranch, HelpCircle, X, ExternalLink, Code2, Globe, CalendarDays, Activity as ActivityIcon, Boxes, GitCompare, Command, Trash2, Search, Wrench, ShieldCheck, Route } from 'lucide-react'
import api from '../lib/api'
import ArasTable from '../aras-core/components/ArasTable'
import { MetadataService } from '../aras-core/services/MetadataService'
import { useUIStore } from '../store/uiStore'
import { useAras } from '../aras-core/hooks/useAras'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import TenantSwitcher from './TenantSwitcher'
import SqlRunner from './devtools/SqlRunner'
import ScaffoldTab from './devtools/ScaffoldTab'
import AccessTab from './devtools/AccessTab'
import ApiConsole from './devtools/ApiConsole'
import LogStream from './devtools/LogStream'
import { Terminal as TerminalIcon, Shield, Zap, AlertTriangle } from 'lucide-react'
import SystemTab from './devtools/SystemTab'
import SchemaTab from './devtools/SchemaTab'
import RequestTimeline from './devtools/RequestTimeline'
import ModelRegistry from './devtools/ModelRegistry'
import CacheControl from './devtools/CacheControl'
import DevCommandPalette from './devtools/DevCommandPalette'
import { getApiDocsUrl } from '../lib/apiDocs'
import DevHealthPanel from './devtools/DevHealthPanel'
import RouteDebugger from './devtools/RouteDebugger'
import { devApi } from './devtools/devApi'

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

interface HandoffRun {
  id: number
  agent: string
  task: string
  status: string
  started_at: string
  finished_at: string
  summary: string
  branch: string
}

type DevTabKey = 'overview' | 'workbench' | 'schema' | 'timeline' | 'routes' | 'models' | 'cache' | 'commands' | 'console' | 'sql' | 'access' | 'handoff' | 'mocks' | 'api' | 'scaffold' | 'logs'

interface DevTab {
  key: DevTabKey
  label: string
  hint: string
  icon?: React.ReactNode
}

// claude-sonnet-4-6
export default function DevTools() {
  const [info, setInfo] = useState<FrameworkInfo | null>(null)
  const [stats, setStats] = useState<DbStat[]>([])
  const [syncing, setSyncing] = useState(false)
  const setPageTitle = useUIStore(state => state.setPageTitle)

  useEffect(() => {
    setPageTitle('Developer Tools', 'Internal framework inspection and maintenance utilities.', 'SYSTEM / DEV')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  const [activeTab, setActiveTab] = useState<DevTabKey>('overview')
  const [tabQuery, setTabQuery] = useState('')
  const [handoffRuns, setHandoffRuns] = useState<HandoffRun[]>([])
  const [selectedRun, setSelectedRun] = useState<HandoffRun | null>(null)
  const [loadingHandoff, setLoadingHandoff] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { notify } = useAras()

  const { designMode, toggleDesignMode } = useUIStore()

  const fetchData = async () => {
    try {
      const [infoRes, statsRes] = await Promise.all([
        api.get(devApi.info),
        api.get(devApi.stats)
      ])
      setInfo(infoRes.data)
      setStats(statsRes.data)
    } catch (error) {
      console.error('Failed to fetch dev tools data', error)
    }
  }

  const handleSync = async () => {
    setSyncing(true)
    try {
      await api.post(devApi.sync)
      MetadataService.clearCache()
      fetchData()
    } catch (error) {
      notify('Sync failed', 'error')
    } finally {
      setSyncing(false)
    }
  }

  const fetchHandoffRuns = async () => {
    setLoadingHandoff(true)
    try {
      const res = await api.get(devApi.handoffRuns, { params: { limit: 50, sort: 'id', order: 'desc' } })
      setHandoffRuns(res.data.items || res.data || [])
    } catch {
      notify('Failed to load handoff runs', 'error')
    } finally {
      setLoadingHandoff(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    if (activeTab === 'handoff') fetchHandoffRuns()
  }, [activeTab])

  const tabs: DevTab[] = [
    { key: 'overview', label: 'Overview', hint: 'Status, shortcuts, and runtime' },
    { key: 'workbench', label: 'Workbench', hint: 'Common dev workflows', icon: <Wrench size={13} /> },
    { key: 'schema', label: 'Schema', hint: 'Database model drift', icon: <GitCompare size={13} /> },
    { key: 'timeline', label: 'Timeline', hint: 'Request metrics', icon: <ActivityIcon size={13} /> },
    { key: 'routes', label: 'Routes', hint: 'Route debugger', icon: <Route size={13} /> },
    { key: 'models', label: 'Models', hint: 'Model registry', icon: <Boxes size={13} /> },
    { key: 'cache', label: 'Cache', hint: 'Metadata cache controls', icon: <Trash2 size={13} /> },
    { key: 'commands', label: 'Commands', hint: 'Command launcher', icon: <Command size={13} /> },
    { key: 'console', label: 'Test Lab', hint: 'Run API requests, scenarios, and reports', icon: <Zap size={13} /> },
    { key: 'sql', label: 'SQL Runner', hint: 'Read-only SQL tools', icon: <TerminalIcon size={13} /> },
    { key: 'access', label: 'Access', hint: 'RBAC matrix and simulator', icon: <Shield size={13} /> },
    { key: 'handoff', label: 'Handoff', hint: 'Agent run history', icon: <GitBranch size={13} /> },
    { key: 'mocks', label: 'Mocks', hint: 'Mock server surface', icon: <Globe size={13} /> },
    { key: 'api', label: 'API Help', hint: 'Swagger and endpoint docs', icon: <Code2 size={13} /> },
    { key: 'scaffold', label: 'Scaffold', hint: 'Generate app code', icon: <Code2 size={13} /> },
    { key: 'logs', label: 'Logs', hint: 'Live error stream', icon: <AlertTriangle size={13} /> },
  ]

  const filteredTabs = tabs.filter(tab => `${tab.label} ${tab.hint}`.toLowerCase().includes(tabQuery.toLowerCase()))
  const activeTabMeta = tabs.find(tab => tab.key === activeTab)

  useEffect(() => {
    const tab = new URLSearchParams(location.search).get('tab')
    if (tab && tabs.some(item => item.key === tab)) setActiveTab(tab as DevTabKey)
  }, [location.search])

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 min-w-0">
      <div className="sticky top-0 z-30 -mx-4 md:-mx-6 lg:-mx-8 mb-5 border-b border-[var(--line)] bg-[var(--bg)]/95 px-4 py-3 backdrop-blur md:px-6 lg:px-8">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-lg font-black text-[var(--text)]">DevTools</h1>
              <span className="rounded-full border border-[var(--line)] bg-[var(--surface)] px-2.5 py-1 text-[11px] font-black uppercase tracking-[0.14em] text-[var(--text-3)]">
                {activeTabMeta?.label}
              </span>
            </div>
            <p className="mt-1 text-sm font-medium text-[var(--text-3)]">{activeTabMeta?.hint}</p>
          </div>

          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <div className="relative min-w-[220px] flex-1 xl:flex-none">
              <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
              <input
                value={tabQuery}
                onChange={(event) => setTabQuery(event.target.value)}
                placeholder="Find tool"
                className="h-9 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] pl-9 pr-3 text-sm font-semibold text-[var(--text)] outline-none focus:border-[var(--accent)]"
              />
            </div>
            <button
              onClick={() => setActiveTab('workbench')}
              className="flex h-9 items-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 text-xs font-black text-[var(--text)] hover:bg-[var(--surface-2)]"
            >
              <Wrench size={14} />
              Workbench
            </button>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="flex h-9 items-center gap-2 rounded-[var(--radius)] bg-[var(--accent)] px-3 text-xs font-black text-white hover:opacity-90 disabled:opacity-50"
            >
              <RefreshCw className={syncing ? 'animate-spin' : ''} size={14} />
              {syncing ? 'Syncing' : 'Sync'}
            </button>
          </div>
        </div>

        <div className="mt-3 max-w-full overflow-x-auto pb-1">
          <div className="flex w-max min-w-full gap-1 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-2)] p-1">
            {filteredTabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                title={tab.hint}
                className={`flex h-9 shrink-0 items-center gap-1.5 rounded-[var(--radius)] px-3 text-sm font-bold transition-all ${
                  activeTab === tab.key
                    ? 'bg-[var(--surface)] text-[var(--text)] shadow-sm border border-[var(--line)]'
                    : 'text-[var(--text-3)] hover:bg-[var(--surface)] hover:text-[var(--text-2)]'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
            {filteredTabs.length === 0 && (
              <div className="px-3 py-2 text-sm font-semibold text-[var(--text-3)]">No tools match “{tabQuery}”.</div>
            )}
          </div>
        </div>
      </div>

      <DevHealthPanel />

      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* ── At-a-glance stat strip ── */}
          <div className="grid grid-cols-2 gap-px overflow-hidden rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--line)] sm:grid-cols-3 lg:grid-cols-5">
            <StatCell icon={<Cpu size={16} />} label="Engine" value={info ? `${info.engine} ${info.version}` : '—'} />
            <StatCell icon={<Boxes size={16} />} label="Apps" value={info ? String(info.apps_discovered.length) : '—'} />
            <StatCell icon={<GitCompare size={16} />} label="Models" value={info ? String(info.total_models) : '—'} />
            <StatCell icon={<Database size={16} />} label="Tables" value={String(stats.length)} />
            <StatCell
              icon={<AlertTriangle size={16} />}
              label="Errors"
              value={String(stats.find(s => s.table === 'dev_error_logs')?.rows || 0)}
              tone={(Number(stats.find(s => s.table === 'dev_error_logs')?.rows) || 0) > 0 ? 'warn' : 'default'}
            />
          </div>

          {/* ── Quick actions toolbar ── */}
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
                  const ref = (() => { try { const u = new URL(document.referrer); return u.origin === window.location.origin ? u.pathname : '' } catch { return '' } })()
                  const from = ref || last
                  navigate(from ? `/dev/template-builder?from=${encodeURIComponent(from)}` : '/dev/template-builder')
                }}
              />
              <ActionChip icon={<Route size={16} />} label="Routes" sub="Explorer" onClick={() => setActiveTab('routes')} />
              <ActionChip icon={<ActivityIcon size={16} />} label="Tasks" sub="Queue" onClick={() => navigate('/dev/tasks')} />
              <ActionChip icon={<CalendarDays size={16} />} label="Heatmap" sub="Activity" onClick={() => navigate('/dev/activity-heatmap')} />
              <ActionChip icon={<HelpCircle size={16} />} label="Dev Help" sub="Reference" onClick={() => navigate('/dev/help')} />
            </div>
          </div>

          {/* ── Context: tenant + framework info ── */}
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

          {/* ── Runtime telemetry (merged from former System tab) ── */}
          <section>
            <h2 className="mb-3 text-xs font-black uppercase tracking-[0.18em] text-[var(--text-3)]">Runtime</h2>
            <SystemTab />
          </section>

          {/* ── Registry shortcuts ── */}
          <section>
            <h2 className="mb-3 text-xs font-black uppercase tracking-[0.18em] text-[var(--text-3)]">Registries</h2>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <RegistryCard title="System Users" count={stats.find(s => s.table === 'core_users')?.rows as number || 0} icon={<Users size={22} />} to="/dev/users" color="slate" />
              <RegistryCard title="System Settings" count={stats.find(s => s.table === 'core_settings')?.rows as number || 0} icon={<Settings size={22} />} to="/admin/settings" color="slate" />
              <RegistryCard title="Handoff Runs" count={stats.find(s => s.table === 'dev_handoff_runs')?.rows as number || 0} icon={<GitBranch size={22} />} color="slate" onClick={() => setActiveTab('handoff')} />
              <RegistryCard title="Template Annotations" count={stats.find(s => s.table === 'dev_template_annotations')?.rows as number || 0} icon={<Layout size={22} />} to="/dev/template-annotations" color="slate" />
            </div>
          </section>

          {/* ── Database statistics ── */}
          <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-2.5">
              <span className="grid h-9 w-9 place-items-center rounded-[var(--radius)] bg-[var(--surface-2)] text-[var(--accent)]"><Database size={18} /></span>
              <h2 className="text-base font-black text-[var(--text)]">Database Statistics</h2>
              <span className="ml-auto text-xs font-bold text-[var(--text-3)]">{stats.length} tables</span>
            </div>
            {(() => {
              const dbStatColumns = [
                { key: 'table', field: 'table', label: 'Table Name', render: (v: any) => <code className="rounded bg-[var(--surface-2)] px-2 py-0.5 text-xs font-bold text-[var(--accent)]">{String(v)}</code> },
                { key: 'rows', field: 'rows', label: 'Row Count', align: 'right' as const, render: (v: any) => <span className="font-mono text-sm font-bold text-[var(--text)]">{Number(v).toLocaleString()}</span> },
              ]
              return (
                <div className="overflow-hidden rounded-[var(--radius)] border border-[var(--line)]">
                  <ArasTable columns={dbStatColumns} rows={stats} rowKey={(stat) => stat.table} />
                </div>
              )
            })()}
          </section>
        </div>
      )}

      {activeTab === 'workbench' && (
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
          <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <WorkflowCard
              title="Debug an API route"
              desc="Open route explorer, then run the selected endpoint in Test Lab."
              icon={<Route size={18} />}
              actions={[
                { label: 'Routes', onClick: () => setActiveTab('routes') },
                { label: 'Test Lab', onClick: () => setActiveTab('console') },
                { label: 'Swagger', onClick: () => window.open(getApiDocsUrl(), '_blank', 'noopener,noreferrer') },
              ]}
            />
            <WorkflowCard
              title="Inspect a model"
              desc="Review registered fields, table mapping, relationships, and generated metadata."
              icon={<Boxes size={18} />}
              actions={[
                { label: 'Models', onClick: () => setActiveTab('models') },
                { label: 'Schema', onClick: () => setActiveTab('schema') },
                { label: 'Metadata Cache', onClick: () => setActiveTab('cache') },
              ]}
            />
            <WorkflowCard
              title="Fix access"
              desc="Simulate permissions, compare role grants, and inspect user access quickly."
              icon={<ShieldCheck size={18} />}
              actions={[
                { label: 'Access', onClick: () => setActiveTab('access') },
                { label: 'Users', onClick: () => navigate('/dev/users') },
                { label: 'RBAC Settings', onClick: () => navigate('/settings/rbac') },
              ]}
            />
            <WorkflowCard
              title="Polish UI"
              desc="Open the live Template Builder, preview responsive breakpoints, and sync metadata."
              icon={<Layout size={18} />}
              actions={[
                { label: 'Builder', onClick: () => navigate(`/dev/template-builder?from=${encodeURIComponent(location.pathname)}`) },
                { label: 'Mobile / Expo', onClick: () => navigate('/dev/template-builder?from=%2Fdev') },
                { label: 'Sync', onClick: handleSync },
              ]}
            />
            <WorkflowCard
              title="Watch runtime"
              desc="Use live request metrics and error logs while reproducing a problem."
              icon={<ActivityIcon size={18} />}
              actions={[
                { label: 'Timeline', onClick: () => setActiveTab('timeline') },
                { label: 'Logs', onClick: () => setActiveTab('logs') },
                { label: 'Tasks', onClick: () => navigate('/dev/tasks') },
              ]}
            />
            <WorkflowCard
              title="Generate faster"
              desc="Scaffold apps and keep a command palette for repeated maintenance actions."
              icon={<Command size={18} />}
              actions={[
                { label: 'Scaffold', onClick: () => setActiveTab('scaffold') },
                { label: 'Commands', onClick: () => setActiveTab('commands') },
                { label: 'Help', onClick: () => navigate('/dev/help') },
              ]}
            />
          </section>

          <aside className="space-y-4">
            <div className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4">
              <div className="text-xs font-black uppercase tracking-[0.18em] text-[var(--text-3)]">Recommended next</div>
              <div className="mt-3 space-y-3 text-sm text-[var(--text-2)]">
                <p><b className="text-[var(--text)]">Dev session recorder:</b> capture route, API calls, console errors, and screenshots into one shareable run.</p>
                <p><b className="text-[var(--text)]">Seed data studio:</b> generate realistic records per model and reset them safely.</p>
                <p><b className="text-[var(--text)]">Metadata diff apply:</b> show registry drift and apply selected fixes instead of full sync.</p>
                <p><b className="text-[var(--text)]">Mobile selector map:</b> list Expo selectors and preview which native components consume each override.</p>
              </div>
            </div>
            <div className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-slate-950 p-4 text-white">
              <div className="text-xs font-black uppercase tracking-[0.18em] text-slate-400">Quick health</div>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <MiniMetric label="Apps" value={String(info?.apps_discovered.length || 0)} />
                <MiniMetric label="Models" value={String(info?.total_models || 0)} />
                <MiniMetric label="Tables" value={String(stats.length)} />
                <MiniMetric label="Errors" value={String(stats.find(s => s.table === 'dev_error_logs')?.rows || 0)} />
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* Handoff Runs Tab */}
      {activeTab === 'handoff' && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-black text-[var(--text)]">Handoff Run History</h2>
              <p className="text-[var(--text-3)] mt-1 text-sm">All AI agent code generation runs.</p>
            </div>
            <button
              onClick={fetchHandoffRuns}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--surface-2)] hover:bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius)] font-semibold text-sm transition-all"
            >
              <RefreshCw size={13} className={loadingHandoff ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>

          {loadingHandoff ? (
            <div className="text-[var(--text-3)] text-center py-16">Loading...</div>
          ) : handoffRuns.length === 0 ? (
            <div className="text-center py-16 bg-[var(--surface-2)] rounded-[var(--radius-lg)] border border-[var(--line)]">
              <GitBranch size={36} className="mx-auto text-[var(--muted)] mb-4" />
              <p className="text-[var(--text-2)] font-semibold">No handoff runs yet.</p>
              <p className="text-[var(--text-3)] text-sm mt-1">Runs will appear here after <code className="font-mono">python tools/multi_agent.py</code> completes.</p>
            </div>
          ) : (
            // claude-sonnet-4-6
            (() => {
              const handoffColumns = [
                { key: 'started_at', label: 'Started', render: (v: string) => <span className="text-[var(--text-3)] font-mono text-xs whitespace-nowrap">{String(v || '').slice(0, 16).replace('T', ' ')}</span> },
                { key: 'agent', label: 'Agent', render: (v: string) => <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700">{v || '—'}</span> },
                { key: 'task', label: 'Task', render: (v: string) => <span className="font-semibold text-[var(--text)] max-w-xs truncate block">{v}</span> },
                { key: 'branch', label: 'Branch', render: (v: string) => <code className="text-xs text-[var(--text-2)] font-mono">{v || '—'}</code> },
                { key: 'status', label: 'Status', render: (v: string) => <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${v === 'success' ? 'bg-emerald-100 text-emerald-700' : v === 'error' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>{v}</span> },
                { key: 'finished_at', label: 'Finished', render: (v: string) => <span className="text-[var(--text-3)] font-mono text-xs whitespace-nowrap">{v ? String(v).slice(0, 16).replace('T', ' ') : '—'}</span> },
              ]
              return (
                <div className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius-lg)] overflow-hidden">
                  <ArasTable columns={handoffColumns} rows={handoffRuns} rowKey={(run) => run.id} onRowClick={(run) => setSelectedRun(run)} />
                </div>
              )
            })()
          )}

          {selectedRun && (
            <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/30" onClick={() => setSelectedRun(null)}>
              <div
                className="h-full w-full max-w-3xl bg-[var(--surface)] shadow-2xl border-l border-[var(--line)] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="sticky top-0 bg-[var(--surface)]/95 backdrop-blur border-b border-[var(--line)] px-6 py-4 flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-lg font-black text-[var(--text)]">{selectedRun.task}</h3>
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-[var(--text-3)]">
                      <span className="font-mono">{String(selectedRun.started_at || '').slice(0, 16).replace('T', ' ')}</span>
                      <span className="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-bold">{selectedRun.agent}</span>
                      {selectedRun.branch && <code className="font-mono">{selectedRun.branch}</code>}
                      <span className={`px-2 py-0.5 rounded-full font-bold ${selectedRun.status === 'success' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{selectedRun.status}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedRun(null)}
                    className="p-2 rounded-[var(--radius)] text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors"
                  >
                    <X size={16} />
                  </button>
                </div>
                <div className="p-6">
                  <div className="text-xs font-bold text-[var(--text-3)] uppercase tracking-wider mb-2">Summary</div>
                  <pre className="bg-slate-950 text-slate-200 rounded-[var(--radius)] p-4 text-xs overflow-x-auto whitespace-pre-wrap max-h-[60rem] overflow-y-auto">{selectedRun.summary || 'No summary captured.'}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'scaffold' && <ScaffoldTab />}
      {activeTab === 'schema' && <SchemaTab />}
      {activeTab === 'timeline' && <RequestTimeline />}
      {activeTab === 'routes' && <RouteDebugger />}
      {activeTab === 'models' && <ModelRegistry />}
      {activeTab === 'cache' && <CacheControl />}
      {activeTab === 'commands' && <DevCommandPalette />}
      {activeTab === 'console' && <ApiConsole />}
      {activeTab === 'sql' && <SqlRunner />}
      {activeTab === 'access' && <AccessTab />}
      {activeTab === 'logs' && <LogStream />}

      {/* Mocks Tab */}
      {activeTab === 'mocks' && <MockGallery />}

      {/* API Help Tab */}
      {activeTab === 'api' && (
        // claude-sonnet-4-6
        <div className="space-y-8">
          {/* Quick links */}
          <div className="flex flex-wrap gap-3">
            <a
              href={getApiDocsUrl()}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-5 py-2.5 bg-[var(--accent)] text-white rounded-[var(--radius-lg)] font-bold text-sm hover:opacity-90 transition-all shadow-lg shadow-indigo-200/50"
            >
              <ExternalLink size={14} />
              Open Swagger UI (/docs)
            </a>
            <a
              href="/api/v1/dev/inspect/routes"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-5 py-2.5 bg-[var(--surface)] border border-[var(--line)] text-[var(--text)] rounded-[var(--radius-lg)] font-bold text-sm hover:bg-[var(--surface-2)] transition-all"
            >
              <ExternalLink size={14} />
              Inspect Routes JSON
            </a>
          </div>

          {/* API Pattern Reference */}
          <div>
            <h3 className="text-base font-black text-[var(--text)] mb-3">CRUD API Patterns</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {[
                { method: 'GET', path: '/api/v1/{resource}', desc: 'List records. Supports ?page, ?limit, ?search, ?sort, ?order, ?filter_*.' },
                { method: 'POST', path: '/api/v1/{resource}', desc: 'Create a new record. Body is JSON matching the model schema.' },
                { method: 'GET', path: '/api/v1/{resource}/{id}', desc: 'Fetch a single record by primary key.' },
                { method: 'PATCH', path: '/api/v1/{resource}/{id}', desc: 'Partially update a record. Only send changed fields.' },
                { method: 'DELETE', path: '/api/v1/{resource}/{id}', desc: 'Delete a single record.' },
                { method: 'GET', path: '/api/v1/{resource}/export', desc: 'Export records as CSV or Excel.' },
                { method: 'POST', path: '/api/v1/{resource}/query', desc: 'Advanced filter query with complex conditions.' },
                { method: 'POST', path: '/api/v1/{resource}/bulk-delete', desc: 'Delete multiple records by list of IDs.' },
              ].map(({ method, path, desc }) => (
                <div key={path} className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius)] p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-xs font-black px-2 py-0.5 rounded font-mono ${method === 'GET' ? 'bg-blue-50 text-blue-700' : method === 'POST' ? 'bg-emerald-50 text-emerald-700' : method === 'PATCH' ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'}`}>{method}</span>
                    <code className="text-xs text-[var(--text-2)] font-mono">{path}</code>
                  </div>
                  <p className="text-xs text-[var(--text-3)] leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Dev Endpoints */}
          <div>
            <h3 className="text-base font-black text-[var(--text)] mb-3">Dev Endpoints</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {[
                { path: '/api/v1/dev/info', desc: 'Framework version, engine type, discovered apps.' },
                { path: '/api/v1/dev/stats', desc: 'Row counts for framework and system tables.' },
                { path: '/api/v1/dev/inspect/models', desc: 'Full schema detail for all registered models.' },
                { path: '/api/v1/dev/inspect/env', desc: 'Active environment config (redacts secrets).' },
                { path: '/api/v1/dev/inspect/routes', desc: 'All registered API routes with methods and tags.' },
              ].map(({ path, desc }) => (
                <a
                  key={path}
                  href={path}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius)] p-4 hover:border-[var(--accent)] hover:shadow-sm transition-all group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <code className="text-xs text-[var(--accent)] font-mono font-bold">{path}</code>
                    <ExternalLink size={11} className="text-[var(--text-3)] group-hover:text-[var(--accent)] transition-colors" />
                  </div>
                  <p className="text-xs text-[var(--text-3)] leading-relaxed">{desc}</p>
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// claude-sonnet-4-6
function InspectButton({ label, sub, iconBg, iconColor, icon, onClick, badge }: {
  label: string; sub: string; iconBg: string; iconColor: string; icon: React.ReactNode; onClick: () => void; badge?: boolean
}) {
  return (
    <button
      onClick={onClick}
      className="p-3.5 bg-slate-800 hover:bg-slate-700 rounded-[var(--radius)] border border-slate-700 transition-all flex flex-col items-center gap-2 group"
    >
      <div className={`p-2 ${iconBg} ${iconColor} rounded group-hover:scale-110 transition-transform relative`}>
        {icon}
        {badge && (
          <span className="absolute -top-1 -right-1 flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-pink-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-pink-500" />
          </span>
        )}
      </div>
      <div className="text-center">
        <div className="font-bold text-xs">{label}</div>
        <div className="text-[10px] text-slate-400">{sub}</div>
      </div>
    </button>
  )
}

// claude-opus-4-8
type MockEntry = { path: string; title: string; group: 'App Prototypes' | 'Components' }

const MOCK_ENTRIES: MockEntry[] = [
  { path: 'aras-studio/', title: 'Aras Studio', group: 'App Prototypes' },
  { path: 'erp-unified/', title: 'ERP Unified', group: 'App Prototypes' },
  { path: 'erp-modern/', title: 'ERP Modern', group: 'App Prototypes' },
  { path: 'erp-modern-app/', title: 'ERP Modern App', group: 'App Prototypes' },
  { path: 'erp-web/', title: 'ERP Web', group: 'App Prototypes' },
  { path: 'erp-generic/', title: 'ERP Generic', group: 'App Prototypes' },
  { path: 'erp-editorial/', title: 'ERP Editorial', group: 'App Prototypes' },
  { path: 'erp-mobile/', title: 'ERP Mobile', group: 'App Prototypes' },
  { path: 'erp-expo-web/', title: 'ERP Expo (Web)', group: 'App Prototypes' },
  { path: 'erp-expo-native/', title: 'ERP Expo (Native)', group: 'App Prototypes' },
  { path: 'real-layout/', title: 'Real Layout', group: 'App Prototypes' },
  { path: 'implementation-prototype/', title: 'Implementation Prototype', group: 'App Prototypes' },
  { path: 'mock-by-gemini/', title: 'Mock by Gemini', group: 'App Prototypes' },
  { path: 'datatable.html', title: 'Data Table', group: 'Components' },
  { path: 'datatable-light.html', title: 'Data Table (Light)', group: 'Components' },
  { path: 'form.html', title: 'Form', group: 'Components' },
  { path: 'form-light.html', title: 'Form (Light)', group: 'Components' },
  { path: 'formview-proposal.html', title: 'Form View Proposal', group: 'Components' },
  { path: 'listview-proposal.html', title: 'List View Proposal', group: 'Components' },
]

// claude-opus-4-8
function MockCard({ entry }: { entry: MockEntry }) {
  const url = `/mocks/${entry.path}`
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex flex-col overflow-hidden rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] shadow-sm transition-all hover:-translate-y-0.5 hover:border-[var(--accent)] hover:shadow-lg"
    >
      {/* Scaled live preview — iframe at 1280px wide shrunk into the thumb */}
      <div className="relative h-44 overflow-hidden border-b border-[var(--line)] bg-[var(--surface-2)]">
        <iframe
          src={url}
          title={entry.title}
          loading="lazy"
          tabIndex={-1}
          aria-hidden
          className="origin-top-left border-0"
          style={{ width: 1280, height: 800, transform: 'scale(0.32)', pointerEvents: 'none' }}
        />
        {/* click shield so the whole card opens the mock */}
        <span className="absolute inset-0" />
        <span className="absolute right-2 top-2 flex items-center gap-1 rounded-[var(--radius)] bg-[var(--surface)]/90 px-2 py-1 text-[10px] font-black uppercase tracking-wider text-[var(--text-2)] opacity-0 backdrop-blur transition-opacity group-hover:opacity-100">
          <ExternalLink size={11} /> Open
        </span>
      </div>
      <div className="flex items-center justify-between gap-2 p-3">
        <span className="truncate text-sm font-black text-[var(--text)]">{entry.title}</span>
        <code className="shrink-0 truncate text-[11px] font-medium text-[var(--text-3)]">{entry.path}</code>
      </div>
    </a>
  )
}

// claude-opus-4-8
function MockGallery() {
  const [q, setQ] = useState('')
  const filtered = MOCK_ENTRIES.filter(
    e => e.title.toLowerCase().includes(q.toLowerCase()) || e.path.toLowerCase().includes(q.toLowerCase())
  )
  const groups = ['App Prototypes', 'Components'] as const
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-black text-[var(--text)]">Mock Gallery</h2>
          <p className="mt-1 text-sm text-[var(--text-3)]">Static UI prototypes served from <code className="text-[var(--text-2)]">/mocks/</code>. Click a card to open full-size.</p>
        </div>
        <div className="relative">
          <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="Filter mocks…"
            className="w-56 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] py-2 pl-9 pr-3 text-sm text-[var(--text)] outline-none focus:border-[var(--accent)]"
          />
        </div>
      </div>

      {groups.map(group => {
        const items = filtered.filter(e => e.group === group)
        if (items.length === 0) return null
        return (
          <section key={group}>
            <h3 className="mb-3 text-xs font-black uppercase tracking-[0.18em] text-[var(--text-3)]">{group}<span className="ml-2 text-[var(--text-3)]/60">{items.length}</span></h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {items.map(e => <MockCard key={e.path} entry={e} />)}
            </div>
          </section>
        )
      })}

      {filtered.length === 0 && (
        <div className="rounded-[var(--radius-lg)] border border-dashed border-[var(--line)] py-16 text-center text-sm text-[var(--text-3)]">
          No mocks match “{q}”.
        </div>
      )}
    </div>
  )
}

// claude-sonnet-4-6
function StatCell({ icon, label, value, tone = 'default' }: {
  icon: React.ReactNode; label: string; value: string; tone?: 'default' | 'warn'
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

// claude-sonnet-4-6
function ActionChip({ icon, label, sub, onClick, primary, badge, disabled }: {
  icon: React.ReactNode; label: string; sub: string; onClick: () => void; primary?: boolean; badge?: boolean; disabled?: boolean
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

// claude-sonnet-4-6
function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-[var(--line)] last:border-0">
      <span className="text-[var(--text-3)] text-sm">{label}</span>
      <span className="text-[var(--text)] font-bold text-sm">{value}</span>
    </div>
  )
}

function WorkflowCard({ title, desc, icon, actions }: {
  title: string
  desc: string
  icon: React.ReactNode
  actions: Array<{ label: string; onClick: () => void }>
}) {
  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius)] bg-[var(--surface-2)] text-[var(--accent)]">
          {icon}
        </div>
        <div className="min-w-0">
          <h3 className="text-base font-black text-[var(--text)]">{title}</h3>
          <p className="mt-1 text-sm leading-6 text-[var(--text-3)]">{desc}</p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {actions.map(action => (
          <button
            key={action.label}
            onClick={action.onClick}
            className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-2 text-xs font-black text-[var(--text)] hover:border-[var(--accent)] hover:text-[var(--accent)]"
          >
            {action.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[var(--radius)] border border-white/10 bg-white/5 p-3">
      <div className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">{label}</div>
      <div className="mt-1 text-xl font-black text-white">{value}</div>
    </div>
  )
}

// claude-sonnet-4-6
function RegistryCard({ title, count, icon, to, color, onClick }: {
  title: string; count: number; icon: React.ReactNode; color: string; to?: string; onClick?: () => void
}) {
  const colorClasses: Record<string, string> = {
    indigo: 'bg-indigo-50 text-indigo-600',
    purple: 'bg-purple-50 text-purple-600',
    blue: 'bg-blue-50 text-blue-600',
    slate: 'bg-[var(--surface-2)] text-[var(--text-2)]',
    emerald: 'bg-emerald-50 text-emerald-600',
  }
  const cls = 'bg-[var(--surface)] p-5 rounded-[var(--radius-lg)] border border-[var(--line)] shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all group cursor-pointer'

  const content = (
    <>
      <div className={`p-3 rounded-[var(--radius)] w-fit mb-3 group-hover:scale-110 transition-transform ${colorClasses[color]}`}>
        {icon}
      </div>
      <h3 className="text-sm font-black text-[var(--text)] mb-1 leading-tight">{title}</h3>
      <div className="flex items-end justify-between mt-2">
        <span className="text-2xl font-black text-[var(--text)]">{count}</span>
        <span className="text-[var(--accent)] text-xs font-black uppercase tracking-widest">Browse →</span>
      </div>
    </>
  )

  if (onClick) {
    return <button onClick={onClick} className={cls}>{content}</button>
  }
  return <Link to={to!} className={cls}>{content}</Link>
}

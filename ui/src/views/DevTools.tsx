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

type DevTabKey = 'overview' | 'workbench' | 'system' | 'schema' | 'timeline' | 'routes' | 'models' | 'cache' | 'commands' | 'console' | 'sql' | 'access' | 'handoff' | 'mocks' | 'api' | 'scaffold' | 'logs'

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
    { key: 'overview', label: 'Overview', hint: 'Status and shortcuts' },
    { key: 'workbench', label: 'Workbench', hint: 'Common dev workflows', icon: <Wrench size={13} /> },
    { key: 'system', label: 'System', hint: 'Runtime and environment', icon: <Cpu size={13} /> },
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <TenantSwitcher />

          {/* Design Mode */}
          <div className="bg-[var(--surface)] p-6 rounded-[var(--radius-lg)] border border-[var(--line)] shadow-sm">
            <div className="flex items-center gap-3 mb-5">
              <div className="p-2.5 bg-pink-50 text-pink-600 rounded-[var(--radius)]">
                <Layout size={20} />
              </div>
              <h2 className="text-base font-black text-[var(--text)]">Design Mode</h2>
            </div>
            <p className="text-sm text-[var(--text-3)] mb-5 leading-relaxed">
              Highlight editable elements on the current page. Click any element to inspect and adjust its styles.
            </p>
            <div className="flex items-center justify-between p-3.5 bg-[var(--surface-2)] rounded-[var(--radius)] border border-[var(--line)]">
              <span className="font-semibold text-sm text-[var(--text)]">{designMode ? 'Enabled' : 'Disabled'}</span>
              <div
                onClick={toggleDesignMode}
                className={`w-11 h-6 rounded-full p-0.5 cursor-pointer transition-colors duration-300 flex items-center ${designMode ? 'bg-pink-500' : 'bg-[var(--muted)]'}`}
              >
                <div className={`w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-300 ${designMode ? 'translate-x-5' : 'translate-x-0'}`} />
              </div>
            </div>
          </div>

          {/* Framework Info */}
          <div className="bg-[var(--surface)] p-6 rounded-[var(--radius-lg)] border border-[var(--line)] shadow-sm">
            <div className="flex items-center gap-3 mb-5">
              <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-[var(--radius)]">
                <Cpu size={20} />
              </div>
              <h2 className="text-base font-black text-[var(--text)]">Framework Info</h2>
            </div>
            {info ? (
              <div className="space-y-3">
                <InfoRow label="Engine Version" value={info.version} />
                <InfoRow label="Engine Type" value={info.engine} />
                <InfoRow label="Apps Discovered" value={info.apps_discovered.length.toString()} />
                <InfoRow label="Total Models" value={info.total_models.toString()} />
                <div className="mt-4 pt-4 border-t border-[var(--line)]">
                  <h3 className="text-xs font-bold text-[var(--text-3)] uppercase tracking-wider mb-2.5">Discovered Apps</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {info.apps_discovered.map(app => (
                      <span key={app} className="px-2.5 py-1 bg-[var(--surface-2)] text-[var(--text-2)] text-xs font-semibold rounded-[var(--radius)] border border-[var(--line)]">
                        {app}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="animate-pulse space-y-3">
                <div className="h-4 bg-[var(--surface-2)] rounded w-3/4" />
                <div className="h-4 bg-[var(--surface-2)] rounded w-1/2" />
              </div>
            )}
          </div>

          {/* Database Stats */}
          <div className="lg:col-span-2 bg-[var(--surface)] p-6 rounded-[var(--radius-lg)] border border-[var(--line)] shadow-sm">
            <div className="flex items-center gap-3 mb-5">
              <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-[var(--radius)]">
                <Database size={20} />
              </div>
              <h2 className="text-base font-black text-[var(--text)]">Database Statistics</h2>
            </div>
            {/* claude-sonnet-4-6 */}
            {(() => {
              const dbStatColumns = [
                { key: 'table', label: 'Table Name', render: (v: string) => <code className="text-[var(--accent)] font-bold text-xs bg-indigo-50 px-2 py-0.5 rounded">{v}</code> },
                { key: 'rows', label: 'Row Count', align: 'right' as const, render: (v: any) => <span className="font-mono font-bold text-sm text-[var(--text)]">{Number(v).toLocaleString()}</span> },
              ]
              return (
                <div className="overflow-hidden border border-[var(--line)] rounded-[var(--radius)]">
                  <ArasTable columns={dbStatColumns} rows={stats} rowKey={(stat) => stat.table} />
                </div>
              )
            })()}
          </div>

          {/* Registry Shortcuts */}
          <div className="lg:col-span-3 grid grid-cols-2 md:grid-cols-4 gap-4">
            <RegistryCard title="System Users" count={stats.find(s => s.table === 'auth_users')?.rows as number || 0} icon={<Users size={22} />} to="/dev/users" color="indigo" />
            <RegistryCard title="System Settings" count={stats.find(s => s.table === 'core_settings')?.rows as number || 0} icon={<Settings size={22} />} to="/admin/settings" color="slate" />
            <RegistryCard
              title="Handoff Runs"
              count={stats.find(s => s.table === 'dev_handoff_runs')?.rows as number || 0}
              icon={<GitBranch size={22} />}
              color="purple"
              onClick={() => setActiveTab('handoff')}
            />
            <RegistryCard title="Template Annotations" count={stats.find(s => s.table === 'dev_template_annotations')?.rows as number || 0} icon={<Layout size={22} />} to="/dev/template-annotations" color="blue" />
          </div>

          {/* Advanced Inspection */}
          <div className="lg:col-span-3 bg-slate-900 p-7 rounded-[var(--radius-lg)] text-white overflow-hidden relative">
            <div className="relative z-10">
              <h2 className="text-xl font-black mb-1">Advanced Inspection</h2>
              <p className="text-slate-400 mb-6 text-sm font-medium">Deep dive into framework internals and runtime state.</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
                <InspectButton
                  label="Builder"
                  sub="Layout Annotator"
                  iconBg="bg-pink-500/20"
                  iconColor="text-pink-400"
                  icon={<Layout size={18} />}
                  badge
                  onClick={() => {
                    const last = localStorage.getItem('template-studio:last') || ''
                    const ref = (() => { try { const u = new URL(document.referrer); return u.origin === window.location.origin ? u.pathname : '' } catch { return '' } })()
                    const from = ref || last
                    navigate(from ? `/dev/template-builder?from=${encodeURIComponent(from)}` : '/dev/template-builder')
                  }}
                />
                <button
                  onClick={handleSync}
                  disabled={syncing}
                  className="p-3.5 bg-[var(--accent)] hover:bg-indigo-700 rounded-[var(--radius)] border border-indigo-500/50 transition-all flex flex-col items-center gap-2 group disabled:opacity-50"
                >
                  <div className="p-2 bg-white/10 text-white rounded group-hover:rotate-180 transition-transform duration-500">
                    <RefreshCw size={18} className={syncing ? 'animate-spin' : ''} />
                  </div>
                  <div className="text-center">
                    <div className="font-bold text-xs">Sync Now</div>
                    <div className="text-[10px] text-indigo-300">Force Update</div>
                  </div>
                </button>
                <InspectButton label="Dev Help" sub="Reference" iconBg="bg-emerald-500/20" iconColor="text-emerald-400" icon={<HelpCircle size={18} />} onClick={() => navigate('/dev/help')} />
                <InspectButton label="Heatmap" sub="Activity" iconBg="bg-orange-500/20" iconColor="text-orange-300" icon={<CalendarDays size={18} />} onClick={() => navigate('/dev/activity-heatmap')} />
                <InspectButton label="Routes" sub="Explorer" iconBg="bg-blue-500/20" iconColor="text-blue-300" icon={<Globe size={18} />} onClick={() => setActiveTab('routes')} />
                <InspectButton label="Tasks" sub="Queue" iconBg="bg-violet-500/20" iconColor="text-violet-300" icon={<ActivityIcon size={18} />} onClick={() => navigate('/dev/tasks')} />
              </div>
            </div>
            <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--accent)]/10 blur-[100px] -mr-32 -mt-32 pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald-600/10 blur-[100px] -ml-32 -mb-32 pointer-events-none" />
          </div>
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
      {activeTab === 'system' && <SystemTab />}
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
      {activeTab === 'mocks' && (
        // claude-sonnet-4-6
        <div>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-xl font-black text-[var(--text)]">Mock Server</h2>
              <p className="text-[var(--text-3)] mt-1 text-sm">Inspect and manage API mocks via the mock server UI.</p>
            </div>
            <a
              href="/mocks/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-[var(--surface-2)] hover:bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius)] font-semibold text-sm transition-all"
            >
              <ExternalLink size={13} />
              Open in new tab
            </a>
          </div>
          <div className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius-lg)] overflow-hidden">
            <iframe
              src="/mocks/"
              title="Mock Server"
              className="w-full border-0"
              style={{ height: '700px' }}
            />
          </div>
        </div>
      )}

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

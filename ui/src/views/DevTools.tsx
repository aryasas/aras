import React, { useState, useEffect } from 'react'
import { Terminal, Database, RefreshCw, Cpu, Box, Layout, Table, Link as LinkIcon, Users, Settings, GitBranch, HelpCircle, X } from 'lucide-react'
import api from '../lib/api'
import { MetadataService } from '../aras-core/services/MetadataService'
import { useUIStore } from '../store/uiStore'
import { useAras } from '../aras-core/hooks/useAras'
import { Link, useNavigate } from 'react-router-dom'
import TenantSwitcher from './TenantSwitcher'

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
  feature: string
  mode: string
  status: string
  author?: string
  claude_verdict?: string
  run_date: string
  prompt_md: string
  output_md: string
  backend_files: string
  frontend_files: string
  gemini_prompt_tokens: number
  gemini_completion_tokens: number
  gpt_prompt_tokens: number
  gpt_completion_tokens: number
  total_tokens: number
  total_requests: number
  issues: string
}

export default function DevTools() {
  const [info, setInfo] = useState<FrameworkInfo | null>(null)
  const [stats, setStats] = useState<DbStat[]>([])
  const [syncing, setSyncing] = useState(false)
  const setPageTitle = useUIStore(state => state.setPageTitle)

  useEffect(() => {
    setPageTitle('Developer Tools', 'Internal framework inspection and maintenance utilities.', 'SYSTEM / DEV')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  const [activeTab, setActiveTab] = useState<'overview' | 'handoff'>('overview')
  const [handoffRuns, setHandoffRuns] = useState<HandoffRun[]>([])
  const [selectedRun, setSelectedRun] = useState<HandoffRun | null>(null)
  const [loadingHandoff, setLoadingHandoff] = useState(false)
  const navigate = useNavigate()
  const { notify } = useAras()

  const { designMode, toggleDesignMode } = useUIStore()

  const fetchData = async () => {
    try {
      const [infoRes, statsRes] = await Promise.all([
        api.get('/dev/info'),
        api.get('/dev/stats')
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
      await api.post('/dev/sync')
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
      const res = await api.get('/dev/dev_handoff_runs?limit=50&sort=id&order=desc')
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

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-end mb-8">
        <button
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200 disabled:opacity-50"
        >
          <RefreshCw className={syncing ? 'animate-spin' : ''} size={18} />
          {syncing ? 'Syncing...' : 'Force Metadata Sync'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-8 bg-slate-100 p-1 rounded-2xl w-fit">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-6 py-2 rounded-xl font-bold text-sm transition-all ${
            activeTab === 'overview'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('handoff')}
          className={`flex items-center gap-2 px-6 py-2 rounded-xl font-bold text-sm transition-all ${
            activeTab === 'handoff'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          <GitBranch size={14} />
          Handoff Runs
        </button>
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <TenantSwitcher />

          {/* Builder Control */}
          <div className="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-pink-50 text-pink-600 rounded-2xl">
                <Layout size={24} />
              </div>
              <h2 className="text-xl font-black text-slate-900">Design Mode</h2>
            </div>
            
            <p className="text-sm text-slate-500 mb-6 font-medium">
              Enable "Design Mode" to highlight editable elements on the current page. Click any element to inspect and adjust its styles.
            </p>

            
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100 mt-4">
              <span className="font-bold text-slate-700">Active Design Mode {designMode ? 'Enabled' : 'Disabled'}</span>
              <div 
                onClick={toggleDesignMode}
                className={`w-12 h-7 rounded-full p-1 cursor-pointer transition-colors duration-300 flex items-center ${designMode ? 'bg-pink-500' : 'bg-slate-300'}`}
              >
                <div className={`w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-300 ${designMode ? 'translate-x-5' : 'translate-x-0'}`}></div>
              </div>
            </div>
          </div>

          {/* Framework Info */}
          <div className="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-2xl">
                <Cpu size={24} />
              </div>
              <h2 className="text-xl font-black text-slate-900">Framework Info</h2>
            </div>
            {info ? (
              <div className="space-y-4">
                <InfoRow label="Engine Version" value={info.version} />
                <InfoRow label="Engine Type" value={info.engine} />
                <InfoRow label="Apps Discovered" value={info.apps_discovered.length.toString()} />
                <InfoRow label="Total Models" value={info.total_models.toString()} />

                <div className="mt-6">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Discovered Apps</h3>
                  <div className="flex flex-wrap gap-2">
                    {info.apps_discovered.map(app => (
                      <span key={app} className="px-3 py-1 bg-slate-100 text-slate-700 text-xs font-bold rounded-lg border border-slate-200">
                        {app}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-slate-100 rounded w-3/4"></div>
                <div className="h-4 bg-slate-100 rounded w-1/2"></div>
              </div>
            )}
          </div>

          {/* Database Explorer */}
          <div className="lg:col-span-2 bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl">
                <Database size={24} />
              </div>
              <h2 className="text-xl font-black text-slate-900">Database Statistics</h2>
            </div>

            <div className="overflow-hidden border border-slate-100 rounded-2xl">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-bottom border-slate-100">
                    <th className="px-6 py-4 text-xs font-black text-slate-400 uppercase tracking-wider">Table Name</th>
                    <th className="px-6 py-4 text-xs font-black text-slate-400 uppercase tracking-wider text-right">Row Count</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {stats.map(stat => (
                    <tr key={stat.table} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4">
                        <code className="text-indigo-600 font-bold text-sm bg-indigo-50 px-2 py-0.5 rounded-md">
                          {stat.table}
                        </code>
                      </td>
                      <td className="px-6 py-4 text-right font-mono font-bold text-slate-700">
                        {stat.rows.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Registry Shortcuts */}
          <div className="lg:col-span-3 grid grid-cols-2 md:grid-cols-4 gap-6">
            <RegistryCard
              title="App Registry"
              count={info?.apps_discovered.length || 0}
              icon={<Box size={24} />}
              to="/dev/apps"
              color="indigo"
            />
            <RegistryCard
              title="Resource Registry"
              count={stats.find(s => s.table === 'aras_resources')?.rows as number || 0}
              icon={<Layout size={24} />}
              to="/dev/resources"
              color="purple"
            />
            <RegistryCard
              title="Field Registry"
              count={stats.find(s => s.table === 'aras_fields')?.rows as number || 0}
              icon={<Table size={24} />}
              to="/dev/fields"
              color="blue"
            />
            <RegistryCard
              title="Link Registry"
              count={stats.find(s => s.table === 'aras_links')?.rows as number || 0}
              icon={<LinkIcon size={24} />}
              to="/dev/links"
              color="emerald"
            />
            <RegistryCard
              title="Activity Audit Trail"
              count={stats.find(s => s.table === 'aras_activity_logs')?.rows as number || 0}
              icon={<Terminal size={24} />}
              to="/dev/activity-logs"
              color="slate"
            />
            <RegistryCard
              title="System Users"
              count={stats.find(s => s.table === 'auth_users')?.rows as number || 0}
              icon={<Users size={24} />}
              to="/dev/users"
              color="indigo"
            />
            <RegistryCard
              title="System Settings"
              count={stats.find(s => s.table === 'sys_settings')?.rows as number || 0}
              icon={<Settings size={24} />}
              to="/dev/settings"
              color="slate"
            />
            <RegistryCard
              title="Handoff Runs"
              count={stats.find(s => s.table === 'dev_handoff_runs')?.rows as number || 0}
              icon={<GitBranch size={24} />}
              to="/dev/handoff-runs"
              color="purple"
            />
            <RegistryCard
              title="Template Annotations"
              count={stats.find(s => s.table === 'dev_template_annotations')?.rows as number || 0}
              icon={<Layout size={24} />}
              to="/dev/template-annotations"
              color="blue"
            />
          </div>

          {/* Advanced Tools */}
          <div className="lg:col-span-3 bg-slate-900 p-8 rounded-[2.5rem] text-white overflow-hidden relative">
             <div className="relative z-10">
               <h2 className="text-2xl font-black mb-2">Advanced Inspection</h2>
               <p className="text-slate-400 mb-8 font-medium">Deep dive into framework internals and runtime state.</p>

               <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                  <button
                    onClick={() => navigate('/dev/template-builder')}
                    className="p-4 bg-slate-800 hover:bg-slate-700 rounded-2xl border border-slate-700 transition-all flex flex-col items-center gap-2 group"
                  >
                    <div className="p-2 bg-pink-500/20 text-pink-400 rounded-lg group-hover:scale-110 transition-transform relative">
                      <Layout size={20} />
                      <span className="absolute -top-1 -right-1 flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-pink-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-pink-500"></span>
                      </span>
                    </div>
                    <div className="text-center">
                      <div className="font-bold text-sm">Builder</div>
                      <div className="text-[10px] text-slate-500">Layout Annotator</div>
                    </div>
                  </button>

                  <button
                    onClick={() => navigate('/dev/routes')}
                    className="p-4 bg-slate-800 hover:bg-slate-700 rounded-2xl border border-slate-700 transition-all flex flex-col items-center gap-2 group"
                  >
                    <div className="p-2 bg-indigo-500/20 text-indigo-400 rounded-lg group-hover:scale-110 transition-transform">
                      <Layout size={20} />
                    </div>
                    <div className="text-center">
                      <div className="font-bold text-sm">Routes</div>
                      <div className="text-[10px] text-slate-500">API Map</div>
                    </div>
                  </button>

                  <button
                    onClick={() => window.open('/api/v1/dev/inspect/models', '_blank')}
                    className="p-4 bg-slate-800 hover:bg-slate-700 rounded-2xl border border-slate-700 transition-all flex flex-col items-center gap-2 group"
                  >
                    <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-lg group-hover:scale-110 transition-transform">
                      <Box size={20} />
                    </div>
                    <div className="text-center">
                      <div className="font-bold text-sm">Models</div>
                      <div className="text-[10px] text-slate-500">Schema Detail</div>
                    </div>
                  </button>

                  <button
                    onClick={() => window.open('/api/v1/dev/inspect/env', '_blank')}
                    className="p-4 bg-slate-800 hover:bg-slate-700 rounded-2xl border border-slate-700 transition-all flex flex-col items-center gap-2 group"
                  >
                    <div className="p-2 bg-amber-500/20 text-amber-400 rounded-lg group-hover:scale-110 transition-transform">
                      <Cpu size={20} />
                    </div>
                    <div className="text-center">
                      <div className="font-bold text-sm">Environment</div>
                      <div className="text-[10px] text-slate-500">Config</div>
                    </div>
                  </button>

                  <button
                    onClick={() => window.open('/api/v1/dev/info', '_blank')}
                    className="p-4 bg-slate-800 hover:bg-slate-700 rounded-2xl border border-slate-700 transition-all flex flex-col items-center gap-2 group"
                  >
                    <div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg group-hover:scale-110 transition-transform">
                      <RefreshCw size={20} />
                    </div>
                    <div className="text-center">
                      <div className="font-bold text-sm">Raw Info</div>
                      <div className="text-[10px] text-slate-500">Engine JSON</div>
                    </div>
                  </button>

                  <button
                    onClick={() => window.open('/api/v1/dev/stats', '_blank')}
                    className="p-4 bg-slate-800 hover:bg-slate-700 rounded-2xl border border-slate-700 transition-all flex flex-col items-center gap-2 group"
                  >
                    <div className="p-2 bg-purple-500/20 text-purple-400 rounded-lg group-hover:scale-110 transition-transform">
                      <Database size={20} />
                    </div>
                    <div className="text-center">
                      <div className="font-bold text-sm">Raw Stats</div>
                      <div className="text-[10px] text-slate-500">DB JSON</div>
                    </div>
                  </button>

                  <button
                    onClick={handleSync}
                    disabled={syncing}
                    className="p-4 bg-indigo-600 hover:bg-indigo-500 rounded-2xl border border-indigo-500/50 transition-all flex flex-col items-center gap-2 group disabled:opacity-50"
                  >
                    <div className="p-2 bg-white/20 text-white rounded-lg group-hover:rotate-180 transition-transform duration-500">
                      <RefreshCw size={20} className={syncing ? 'animate-spin' : ''} />
                    </div>
                    <div className="text-center">
                      <div className="font-bold text-sm">Sync Now</div>
                      <div className="text-[10px] text-indigo-200">Force Update</div>
                    </div>
                  </button>

                  <button
                    onClick={() => navigate('/dev/help')}
                    className="p-4 bg-slate-800 hover:bg-slate-700 rounded-2xl border border-slate-700 transition-all flex flex-col items-center gap-2 group"
                  >
                    <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-lg group-hover:scale-110 transition-transform">
                      <HelpCircle size={20} />
                    </div>
                    <div className="text-center">
                      <div className="font-bold text-sm">Dev Help</div>
                      <div className="text-[10px] text-slate-500">Reference</div>
                    </div>
                  </button>
               </div>
             </div>

             <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600/10 blur-[100px] -mr-32 -mt-32"></div>
             <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald-600/10 blur-[100px] -ml-32 -mb-32"></div>
          </div>
        </div>
      )}

      {activeTab === 'handoff' && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-black text-slate-900">Handoff Run History</h2>
              <p className="text-slate-500 mt-1">All AI agent code generation runs, with prompts and token usage.</p>
            </div>
            <button
              onClick={fetchHandoffRuns}
              className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl font-bold text-sm transition-all"
            >
              <RefreshCw size={14} className={loadingHandoff ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>

          {loadingHandoff ? (
            <div className="text-slate-400 text-center py-16">Loading...</div>
          ) : handoffRuns.length === 0 ? (
            <div className="text-center py-16 bg-slate-50 rounded-3xl">
              <GitBranch size={40} className="mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500 font-medium">No handoff runs yet.</p>
              <p className="text-slate-400 text-sm mt-1">Runs will appear here after <code>python tools/multi_agent.py</code> completes.</p>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="text-left px-4 py-3 font-bold text-slate-500 text-xs uppercase tracking-wider">Run Date</th>
                    <th className="text-left px-4 py-3 font-bold text-slate-500 text-xs uppercase tracking-wider">Feature</th>
                    <th className="text-left px-4 py-3 font-bold text-slate-500 text-xs uppercase tracking-wider">Mode</th>
                    <th className="text-left px-4 py-3 font-bold text-slate-500 text-xs uppercase tracking-wider">Status</th>
                    <th className="text-left px-4 py-3 font-bold text-slate-500 text-xs uppercase tracking-wider">Author</th>
                    <th className="text-left px-4 py-3 font-bold text-slate-500 text-xs uppercase tracking-wider">Claude Verdict</th>
                    <th className="text-right px-4 py-3 font-bold text-slate-500 text-xs uppercase tracking-wider">Total Tokens</th>
                  </tr>
                </thead>
                <tbody>
                  {handoffRuns.map((run) => (
                      <tr
                        key={run.id}
                        onClick={() => setSelectedRun(run)}
                        className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer transition-colors"
                      >
                        <td className="px-4 py-3 text-slate-500 font-mono text-xs whitespace-nowrap">{String(run.run_date).slice(0, 16).replace('T', ' ')}</td>
                        <td className="px-4 py-3 font-bold text-slate-900 max-w-xs truncate">{run.feature}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-600">{run.mode}</span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                            run.status === 'success' ? 'bg-emerald-100 text-emerald-700' :
                            run.status === 'error'   ? 'bg-red-100 text-red-700' :
                                                       'bg-amber-100 text-amber-700'
                          }`}>{run.status}</span>
                        </td>
                        <td className="px-4 py-3 text-slate-600 text-xs font-bold">{run.author || '—'}</td>
                        <td className="px-4 py-3">
                          <VerdictBadge verdict={run.claude_verdict} />
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-xs font-bold text-slate-900">
                          {(run.total_tokens || 0).toLocaleString()}
                        </td>
                      </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {selectedRun && (
            <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/30" onClick={() => setSelectedRun(null)}>
              <div
                className="h-full w-full max-w-3xl bg-white shadow-2xl border-l border-slate-200 overflow-y-auto"
                onClick={(event) => event.stopPropagation()}
              >
                <div className="sticky top-0 bg-white/95 backdrop-blur border-b border-slate-100 px-6 py-4 flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-xl font-black text-slate-900">{selectedRun.feature}</h3>
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs font-bold text-slate-500">
                      <span>{String(selectedRun.run_date).slice(0, 16).replace('T', ' ')}</span>
                      <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">{selectedRun.mode}</span>
                      <VerdictBadge verdict={selectedRun.claude_verdict} />
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedRun(null)}
                    className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                  >
                    <X size={18} />
                  </button>
                </div>

                <div className="p-6 space-y-6">
                  <div>
                    <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Prompt</div>
                    <pre className="bg-slate-950 text-slate-200 rounded-xl p-4 text-xs overflow-x-auto whitespace-pre-wrap max-h-[36rem] overflow-y-auto">{selectedRun.prompt_md || 'No prompt captured.'}</pre>
                  </div>

                  <div>
                    <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Output</div>
                    <pre className="bg-slate-950 text-slate-200 rounded-xl p-4 text-xs overflow-x-auto whitespace-pre-wrap max-h-[36rem] overflow-y-auto">{selectedRun.output_md || 'No output captured.'}</pre>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function VerdictBadge({ verdict }: { verdict?: string | null }) {
  const normalized = verdict || ''
  const classes = normalized === 'APPROVED'
    ? 'bg-emerald-100 text-emerald-700'
    : normalized === 'NEEDS-FIX'
      ? 'bg-red-100 text-red-700'
      : 'bg-slate-100 text-slate-500'

  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${classes}`}>
      {normalized || '—'}
    </span>
  )
}

function InfoRow({ label, value }: { label: string, value: string }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-slate-50 last:border-0">
      <span className="text-slate-500 text-sm font-medium">{label}</span>
      <span className="text-slate-900 font-bold">{value}</span>
    </div>
  )
}

function RegistryCard({ title, count, icon, to, color }: { title: string, count: number, icon: React.ReactNode, to: string, color: string }) {
  const colorClasses: any = {
    indigo: 'bg-indigo-50 text-indigo-600',
    purple: 'bg-purple-50 text-purple-600',
    blue: 'bg-blue-50 text-blue-600',
    slate: 'bg-slate-50 text-slate-600',
    emerald: 'bg-emerald-50 text-emerald-600',
  }

  return (
    <Link to={to} className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all group">
      <div className={`p-4 rounded-2xl w-fit mb-4 group-hover:scale-110 transition-transform ${colorClasses[color]}`}>
        {icon}
      </div>
      <h3 className="text-lg font-black text-slate-900 mb-1">{title}</h3>
      <div className="flex items-end justify-between">
        <span className="text-3xl font-black text-slate-700">{count}</span>
        <span className="text-indigo-600 text-xs font-black uppercase tracking-widest">Browse →</span>
      </div>
    </Link>
  )
}

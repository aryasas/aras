import { useEffect, useState, type ReactNode } from 'react'
import { Activity, Boxes, Command, Layout, Route, ShieldCheck } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import api from '../../lib/api'
import { getApiDocsUrl } from '../../lib/apiDocs'
import { MetadataService } from '../../aras-core/services/MetadataService'
import { useAras } from '../../aras-core/hooks/useAras'
import { devApi } from './devApi'

interface DbStat {
  table: string
  rows: number | string
}

interface FrameworkInfo {
  apps_discovered: string[]
  total_models: number
}

export default function WorkbenchTab() {
  const [info, setInfo] = useState<FrameworkInfo | null>(null)
  const [stats, setStats] = useState<DbStat[]>([])
  const navigate = useNavigate()
  const location = useLocation()
  const { notify } = useAras()

  const fetchData = async () => {
    try {
      const [infoRes, statsRes] = await Promise.all([
        api.get(devApi.info),
        api.get(devApi.stats),
      ])
      setInfo(infoRes.data)
      setStats(statsRes.data)
    } catch (error) {
      console.error('Failed to fetch dev workbench data', error)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleSync = async () => {
    try {
      await api.post(devApi.sync)
      MetadataService.clearCache()
      await fetchData()
    } catch {
      notify('Sync failed', 'error')
    }
  }

  return (
    <div className="grid grid-cols-1 gap-5 animate-in fade-in slide-in-from-bottom-4 duration-500 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <WorkflowCard
          title="Debug an API route"
          desc="Open route explorer, then run the selected endpoint in Test Lab."
          icon={<Route size={18} />}
          actions={[
            { label: 'Routes', onClick: () => navigate('/admin/dev/routes-debug') },
            { label: 'Test Lab', onClick: () => navigate('/admin/dev/test-lab') },
            { label: 'Swagger', onClick: () => window.open(getApiDocsUrl(), '_blank', 'noopener,noreferrer') },
          ]}
        />
        <WorkflowCard
          title="Inspect a model"
          desc="Review registered fields, table mapping, relationships, and generated metadata."
          icon={<Boxes size={18} />}
          actions={[
            { label: 'Models', onClick: () => navigate('/admin/dev/models') },
            { label: 'Schema', onClick: () => navigate('/admin/dev/schema') },
            { label: 'Metadata Cache', onClick: () => navigate('/admin/dev/cache') },
          ]}
        />
        <WorkflowCard
          title="Fix access"
          desc="Simulate permissions, compare role grants, and inspect user access quickly."
          icon={<ShieldCheck size={18} />}
          actions={[
            { label: 'Access', onClick: () => navigate('/admin/dev/access') },
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
          icon={<Activity size={18} />}
          actions={[
            { label: 'Timeline', onClick: () => navigate('/admin/dev/timeline') },
            { label: 'Logs', onClick: () => navigate('/admin/dev/logs') },
            { label: 'Tasks', onClick: () => navigate('/dev/tasks') },
          ]}
        />
        <WorkflowCard
          title="Generate faster"
          desc="Scaffold apps and keep a command palette for repeated maintenance actions."
          icon={<Command size={18} />}
          actions={[
            { label: 'Scaffold', onClick: () => navigate('/admin/dev/scaffold') },
            { label: 'Commands', onClick: () => navigate('/admin/dev/commands') },
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
        <div className="rounded-[var(--radius-lg)] bg-slate-950 p-4 text-white">
          <div className="text-xs font-black uppercase tracking-[0.18em] text-slate-400">Quick health</div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <MiniMetric label="Apps" value={String(info?.apps_discovered.length || 0)} />
            <MiniMetric label="Models" value={String(info?.total_models || 0)} />
            <MiniMetric label="Tables" value={String(stats.length)} />
            <MiniMetric label="Errors" value={String(stats.find((s) => s.table === 'dev_error_logs')?.rows || 0)} />
          </div>
        </div>
      </aside>
    </div>
  )
}

function WorkflowCard({ title, desc, icon, actions }: {
  title: string
  desc: string
  icon: ReactNode
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
        {actions.map((action) => (
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

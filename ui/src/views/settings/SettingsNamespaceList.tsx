import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Activity, Cpu, Database, History, Key, LayoutDashboard, Package, Server, Settings, Shield, Terminal, UploadCloud } from 'lucide-react'
import { useAras } from '../../aras-core/hooks/useAras'
import { useAuthStore } from '../../store/authStore'
import { resolveIcon } from '../../lib/iconUtils'
import type { SettingsNamespace } from '../../lib/api'

const getArasRole = () => {
  const injectedRole = (globalThis as any).__ARAS_ROLE__
  return String(injectedRole || import.meta.env.VITE_ARAS_ROLE || 'tenant')
}

// Static tool links that live as sub-routes under /admin/settings
type ToolLink = {
  to: string
  label: string
  icon: typeof Settings
  section: 'security' | 'tools'
  adminOnly?: boolean
  controlPanelOnly?: boolean
  tenantOnly?: boolean
}

const TOOL_LINKS: ToolLink[] = [
  { to: '/admin/settings/access',           label: 'Access Control',    icon: Shield,       section: 'security' },
  { to: '/admin/settings/audit',            label: 'Audit Log',         icon: History,      section: 'security' },
  { to: '/admin/settings/master-data',      label: 'Master Data',       icon: Database,     section: 'tools' },
  { to: '/admin/settings/dashboard',        label: 'Dashboard Builder', icon: LayoutDashboard, section: 'tools', adminOnly: true },
  { to: '/apps',                            label: 'App Manager',       icon: Package,      section: 'tools' },
  { to: '/admin/settings/seeder',           label: 'Seeder',            icon: Database,     section: 'tools', adminOnly: true },
  { to: '/admin/settings/files',            label: 'File Manager',      icon: UploadCloud,  section: 'tools' },
  { to: '/admin/settings/tasks',            label: 'Background Tasks',  icon: Activity,     section: 'tools', adminOnly: true },
  { to: '/admin/settings/health',           label: 'Health & Integrity',icon: Server,       section: 'tools', adminOnly: true },
  { to: '/admin/settings/activity-heatmap', label: 'Activity Heatmap', icon: Activity,     section: 'tools', adminOnly: true },
  { to: '/admin/settings/license',          label: 'License',           icon: Key,          section: 'tools', adminOnly: true, tenantOnly: true },
  { to: '/dev',                             label: 'Developer Tools',   icon: Terminal,     section: 'tools' },
  { to: '/control-panel/tenants',           label: 'Tenant Management', icon: Server,       section: 'tools', adminOnly: true, controlPanelOnly: true },
  { to: '/control-panel/licenses',          label: 'Tenant Licenses',   icon: Key,          section: 'tools', adminOnly: true, controlPanelOnly: true },
  { to: '/control-panel/plans',             label: 'SaaS Plans',        icon: Server,       section: 'tools', adminOnly: true, controlPanelOnly: true },
]

const SECTION_LABELS: Record<string, string> = {
  system: 'System',
  security: 'Security',
  apps: 'Apps',
  tools: 'Tools',
}

interface SettingsNamespaceListProps {
  selectedNamespace: string | null
  onSelect: (namespace: string) => void
  onLoaded?: (namespaces: SettingsNamespace[]) => void
}

// claude-sonnet-4-6
function NavItem({
  icon: Icon,
  label,
  sub,
  active,
  onClick,
}: {
  icon: typeof Settings
  label: string
  sub: string
  active: boolean
  onClick?: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex w-full items-center gap-3 rounded-[var(--aras-radius)] px-3 py-2 text-left transition-colors ${
        active
          ? 'border border-[var(--line)] bg-[var(--surface)] text-[var(--text)]'
          : 'border border-transparent text-[var(--text-2)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]'
      }`}
    >
      <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-[var(--aras-radius)] ${active ? 'bg-[var(--accent)] text-white' : 'bg-[var(--surface-2)] text-[var(--text-3)]'}`}>
        <Icon size={15} />
      </span>
      <span className="min-w-0">
        <span className="block truncate text-[13px] font-semibold">{label}</span>
        <span className="arc-mono block truncate text-[10px] uppercase tracking-[0.12em] text-[var(--text-3)]">{sub}</span>
      </span>
    </button>
  )
}

// claude-sonnet-4-6
function NavLinkItem({ link, active }: { link: ToolLink; active: boolean }) {
  const Icon = link.icon
  return (
    <Link
      to={link.to}
      className={`flex items-center gap-3 rounded-[var(--aras-radius)] px-3 py-2 text-left transition-colors ${
        active
          ? 'border border-[var(--line)] bg-[var(--surface)] text-[var(--text)]'
          : 'border border-transparent text-[var(--text-2)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]'
      }`}
    >
      <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-[var(--aras-radius)] ${active ? 'bg-[var(--accent)] text-white' : 'bg-[var(--surface-2)] text-[var(--text-3)]'}`}>
        <Icon size={15} />
      </span>
      <span className="min-w-0">
        <span className="block truncate text-[13px] font-semibold">{link.label}</span>
        <span className="arc-mono block truncate text-[10px] uppercase tracking-[0.12em] text-[var(--text-3)]">{link.to.replace(/^\//, '')}</span>
      </span>
    </Link>
  )
}

// claude-sonnet-4-6
function SectionHeading({ label }: { label: string }) {
  return (
    <div className="arc-mono mb-1 px-3 pt-3 text-[10px] uppercase tracking-[0.14em] text-[var(--text-3)]">
      {label}
    </div>
  )
}

// claude-sonnet-4-6
export default function SettingsNamespaceList({ selectedNamespace, onSelect, onLoaded }: SettingsNamespaceListProps) {
  const { api, notify } = useAras()
  const location = useLocation()
  const user = useAuthStore((state) => state.user)
  const arasRole = getArasRole()
  const [namespaces, setNamespaces] = useState<SettingsNamespace[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api.get<SettingsNamespace[]>('/settings')
      .then((res) => {
        if (cancelled) return
        setNamespaces(res.data)
        onLoaded?.(res.data)
      })
      .catch((err) => {
        if (cancelled) return
        notify(err.message || 'Failed to load settings namespaces', 'error')
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [api, notify, onLoaded])

  const visibleTools = useMemo(() => TOOL_LINKS.filter((link) => {
    if (link.adminOnly && !user?.is_admin) return false
    if (link.controlPanelOnly && arasRole !== 'control-panel') return false
    if (link.tenantOnly && arasRole === 'control-panel') return false
    return true
  }), [arasRole, user?.is_admin])

  const q = search.toLowerCase()

  // system-level namespaces (core, admin)
  const systemNs = useMemo(() =>
    namespaces.filter((ns) => (ns.level || 'app') === 'system' && (!q || ns.name.includes(q) || (ns.label || '').toLowerCase().includes(q)))
  , [namespaces, q])

  // app-level namespaces (per-module configs registered by each app)
  const appNs = useMemo(() =>
    namespaces.filter((ns) => (ns.level || 'app') === 'app' && (!q || ns.name.includes(q) || (ns.label || '').toLowerCase().includes(q)))
  , [namespaces, q])

  const securityTools = useMemo(() =>
    visibleTools.filter((l) => l.section === 'security' && (!q || l.label.toLowerCase().includes(q) || l.to.includes(q)))
  , [visibleTools, q])

  const otherTools = useMemo(() =>
    visibleTools.filter((l) => l.section === 'tools' && (!q || l.label.toLowerCase().includes(q) || l.to.includes(q)))
  , [visibleTools, q])

  const isOnSettings = location.pathname === '/admin/settings'

  if (loading) {
    return (
      <div className="flex flex-col gap-2 p-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 rounded-[var(--aras-radius)] px-3 py-2">
            <div className="h-8 w-8 animate-pulse rounded-[var(--aras-radius)] bg-[var(--surface-2)]" />
            <div className="h-3 flex-1 animate-pulse rounded bg-[var(--surface-2)]" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <nav className="flex flex-col p-3" aria-label="Settings navigation">
      {/* Search */}
      <div className="mb-3 px-1">
        <div className="relative">
          <Settings className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-3)]" size={14} />
          <input
            type="text"
            placeholder="Filter..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-9 w-full rounded-[var(--aras-radius)] border border-[var(--line)] bg-[var(--surface-2)] pl-8 pr-3 text-[12px] text-[var(--text)] outline-none transition-all focus:border-[var(--accent)] focus:bg-[var(--surface)]"
          />
        </div>
      </div>

      {/* SYSTEM — instance-wide config (core, admin namespaces) */}
      {systemNs.length > 0 && (
        <div className="mb-1">
          <SectionHeading label={SECTION_LABELS.system} />
          {systemNs.map((ns) => {
            const Icon = ns.icon ? resolveIcon(ns.icon) : Cpu
            return (
              <NavItem
                key={ns.name}
                icon={Icon}
                label={ns.label || ns.name}
                sub={ns.name}
                active={isOnSettings && selectedNamespace === ns.name}
                onClick={() => onSelect(ns.name)}
              />
            )
          })}
        </div>
      )}

      {/* SECURITY — access control + audit */}
      {securityTools.length > 0 && (
        <div className="mb-1">
          <SectionHeading label={SECTION_LABELS.security} />
          {securityTools.map((link) => (
            <NavLinkItem key={link.to} link={link} active={location.pathname === link.to} />
          ))}
        </div>
      )}

      {/* APPS — per-module settings from each installed app */}
      {appNs.length > 0 && (
        <div className="mb-1">
          <SectionHeading label={SECTION_LABELS.apps} />
          {appNs.map((ns) => {
            const Icon = ns.icon ? resolveIcon(ns.icon) : Package
            return (
              <NavItem
                key={ns.name}
                icon={Icon}
                label={ns.label || ns.name}
                sub={ns.name}
                active={isOnSettings && selectedNamespace === ns.name}
                onClick={() => onSelect(ns.name)}
              />
            )
          })}
        </div>
      )}

      {/* TOOLS — operational admin tools */}
      {otherTools.length > 0 && (
        <div className="mb-1">
          <SectionHeading label={SECTION_LABELS.tools} />
          {otherTools.map((link) => (
            <NavLinkItem key={link.to} link={link} active={location.pathname === link.to || location.pathname.startsWith(link.to + '/')} />
          ))}
        </div>
      )}
    </nav>
  )
}

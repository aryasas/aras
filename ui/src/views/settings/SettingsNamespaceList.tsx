import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Settings, LayoutDashboard, Globe, Shield, History, Terminal, Activity, UploadCloud, Package, Server, Key, CreditCard, Users, Database } from 'lucide-react'
import { useAras } from '../../aras-core/hooks/useAras'
import { useAuthStore } from '../../store/authStore'
import { resolveIcon } from '../../lib/iconUtils'

const getArasRole = () => {
  const injectedRole = (globalThis as any).__ARAS_ROLE__
  return String(injectedRole || import.meta.env.VITE_ARAS_ROLE || 'tenant')
}
import type { SettingsNamespace } from '../../lib/api'

type Shortcut = {
  to: string
  label: string
  sub: string
  icon: typeof Settings
  group: 'platform' | 'preferences' | 'security' | 'tools'
  external?: boolean
  adminOnly?: boolean
  controlPanelOnly?: boolean
  tenantOnly?: boolean
}

const SHORTCUTS: Shortcut[] = [
  { to: '/admin/master-data',            label: 'Master Data',          sub: 'admin/master-data',     icon: Database,        group: 'platform' },
  { to: '/apps',                        label: 'App Manager',         sub: 'apps',                  icon: Package,         group: 'platform' },
  { to: '/control-panel/tenants',       label: 'Tenant Management',   sub: 'control-panel/tenants', icon: Server,          group: 'platform', adminOnly: true, controlPanelOnly: true },
  { to: '/control-panel/licenses',      label: 'Tenant Licenses',     sub: 'control-panel/licenses',icon: Key,             group: 'platform', adminOnly: true, controlPanelOnly: true },
  { to: '/control-panel/plans',         label: 'SaaS Plans',          sub: 'control-panel/plans',   icon: CreditCard,      group: 'platform', adminOnly: true, controlPanelOnly: true },
  { to: '/admin/license',               label: 'License',             sub: 'admin/license',         icon: Key,             group: 'platform', adminOnly: true, tenantOnly: true },
  { to: '/settings/dashboard',          label: 'Dashboard Builder',   sub: 'settings/dashboard',    icon: LayoutDashboard, group: 'preferences', adminOnly: true },
  { to: '/settings/global',             label: 'Global Preferences',  sub: 'settings/global',       icon: Globe,           group: 'preferences' },
  { to: '/settings/rbac',               label: 'Security & Auth',     sub: 'settings/rbac',         icon: Shield,          group: 'security' },
  { to: '/settings/user-access',          label: 'ERP User Access',     sub: 'settings/user-access',    icon: Users,           group: 'security', adminOnly: true },
  { to: '/settings/audit',              label: 'Activity Audit',      sub: 'settings/audit',        icon: History,         group: 'security' },
  { to: '/dev',                         label: 'Developer Tools',     sub: 'dev',                   icon: Terminal,        group: 'tools' },
  { to: '/dev/tasks',                   label: 'Background Tasks',    sub: 'dev/tasks',             icon: Activity,        group: 'tools', adminOnly: true },
  { to: '/settings/files',              label: 'File Manager',        sub: 'settings/files',        icon: UploadCloud,     group: 'tools' },
]

const GROUP_LABELS: Record<Shortcut['group'], string> = {
  platform: 'Platform',
  preferences: 'Preferences',
  security: 'Security',
  tools: 'Tools',
}

interface SettingsNamespaceListProps {
  selectedNamespace: string | null
  onSelect: (namespace: string) => void
  onLoaded?: (namespaces: SettingsNamespace[]) => void
}

export default function SettingsNamespaceList({ selectedNamespace, onSelect, onLoaded }: SettingsNamespaceListProps) {
  const { api, notify } = useAras()
  const user = useAuthStore((s) => s.user)
  const arasRole = getArasRole()
  const [namespaces, setNamespaces] = useState<SettingsNamespace[]>([])
  const [loading, setLoading] = useState(true)

  const visibleShortcuts = SHORTCUTS.filter((sc) => {
    if (sc.adminOnly && !user?.is_admin) return false
    if (sc.controlPanelOnly && arasRole !== 'control-panel') return false
    if (sc.tenantOnly && arasRole === 'control-panel') return false
    return true
  })

  const grouped = (['platform', 'preferences', 'security', 'tools'] as const).map((g) => ({
    group: g,
    items: visibleShortcuts.filter((sc) => sc.group === g),
  })).filter((g) => g.items.length > 0)

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
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [api, notify, onLoaded])

  if (loading) {
    return (
      <div className="flex flex-col gap-2 p-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="flex items-center gap-3 rounded-[var(--aras-radius)] px-3 py-2">
            <div className="h-8 w-8 animate-pulse rounded-[var(--aras-radius)] bg-[var(--surface-2)]" />
            <div className="h-3 flex-1 animate-pulse rounded bg-[var(--surface-2)]" />
          </div>
        ))}
      </div>
    )
  }

  if (namespaces.length === 0) {
    return (
      <div className="p-5 text-center text-[12px] text-[var(--text-3)]">
        No app settings are available.
      </div>
    )
  }

  return (
    <nav className="flex flex-col gap-1 p-3" aria-label="Settings namespaces">
      {grouped.map(({ group, items }) => (
        <div key={group} className="mb-2">
          <div className="arc-mono mb-1 px-3 pt-1 text-[10px] uppercase tracking-[0.14em] text-[var(--text-3)]">{GROUP_LABELS[group]}</div>
          {items.map((sc) => {
            const Icon = sc.icon
            const linkProps = sc.external
              ? { href: sc.to, target: '_blank', rel: 'noreferrer' }
              : null
            const content = (
              <>
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-[var(--aras-radius)] bg-[var(--surface-2)] text-[var(--text-3)]">
                  <Icon size={15} />
                </span>
                <span className="min-w-0">
                  <span className="block truncate text-[13px] font-semibold">{sc.label}</span>
                  <span className="arc-mono block truncate text-[10px] uppercase tracking-[0.12em] text-[var(--text-3)]">{sc.sub}</span>
                </span>
              </>
            )
            const cls = 'flex items-center gap-3 rounded-[var(--aras-radius)] border border-transparent px-3 py-2 text-left text-[var(--text-2)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]'
            return linkProps ? (
              <a key={sc.to} {...linkProps} className={cls}>{content}</a>
            ) : (
              <Link key={sc.to} to={sc.to} className={cls}>{content}</Link>
            )
          })}
        </div>
      ))}
      <div className="arc-mono mb-1 mt-3 px-3 pt-1 text-[10px] uppercase tracking-[0.14em] text-[var(--text-3)]">App Settings</div>
      {namespaces.map((namespace) => {
        const Icon = namespace.icon ? resolveIcon(namespace.icon) : Settings
        const active = selectedNamespace === namespace.name
        return (
          <button
            key={namespace.name}
            type="button"
            onClick={() => onSelect(namespace.name)}
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
              <span className="block truncate text-[13px] font-semibold">{namespace.label || namespace.name}</span>
              <span className="arc-mono block truncate text-[10px] uppercase tracking-[0.12em] text-[var(--text-3)]">{namespace.name}</span>
            </span>
          </button>
        )
      })}
    </nav>
  )
}

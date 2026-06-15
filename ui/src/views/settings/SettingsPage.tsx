import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate, useOutlet, useSearchParams } from 'react-router-dom'
import { ArrowLeft, Boxes, Cpu, Settings, Shield } from 'lucide-react'
import SettingsForm from './SettingsForm'
import SettingsNamespaceList from './SettingsNamespaceList'
import type { SettingsNamespace } from '../../lib/api'
import { resolveIcon } from '../../lib/iconUtils'
import { useUIStore } from '../../store/uiStore'
import { useAras } from '../../aras-core/hooks/useAras'

// Title/breadcrumb per outlet child route. Keeps the shell as the single owner
// of the page header so child views never fight over it.
const OUTLET_META: Record<string, { title: string; subtitle: string; breadcrumb: string }> = {
  access: { title: 'Access Control', subtitle: 'Roles, permissions, users, organization access, and diagnostics.', breadcrumb: 'ADMIN / SETTINGS / ACCESS' },
  'master-data': { title: 'Master Data', subtitle: 'Manage shared and module-owned reference records from one surface.', breadcrumb: 'ADMIN / SETTINGS / MASTER DATA' },
  audit: { title: 'Audit Log', subtitle: 'Review system activity and change history.', breadcrumb: 'ADMIN / SETTINGS / AUDIT' },
  files: { title: 'File Manager', subtitle: 'Upload and retrieve framework-managed files.', breadcrumb: 'ADMIN / SETTINGS / FILES' },
  dashboard: { title: 'Dashboard Settings', subtitle: 'Configure dashboard widgets and layout.', breadcrumb: 'ADMIN / SETTINGS / DASHBOARD' },
  seeder: { title: 'Data Seeder', subtitle: 'Select baseline and optional seed data for the current organization.', breadcrumb: 'ADMIN / SETTINGS / SEEDER' },
  license: { title: 'License', subtitle: 'Instance license status and activation.', breadcrumb: 'ADMIN / SETTINGS / LICENSE' },
  health: { title: 'System Health & Integrity', subtitle: 'Real-time status of framework core and database registry.', breadcrumb: 'ADMIN / SETTINGS / HEALTH' },
  tasks: { title: 'Background Tasks', subtitle: 'Enqueue and inspect async jobs.', breadcrumb: 'ADMIN / SETTINGS / TASKS' },
  'activity-heatmap': { title: 'Activity Heatmap', subtitle: 'Calendar view of framework audit activity.', breadcrumb: 'ADMIN / SETTINGS / ACTIVITY HEATMAP' },
}

function namespaceFromSectionKey(sectionKey: string | null) {
  if (!sectionKey || !sectionKey.includes('.')) return null
  return sectionKey.split('.').slice(0, -1).join('.')
}

const LEVEL_META = {
  system: {
    title: 'System',
    description: 'Instance-wide config: email, branding, storage, integrations, and developer settings.',
    icon: Cpu,
  },
  app: {
    title: 'Apps',
    description: 'Configuration for your installed product modules and tools.',
    icon: Boxes,
  },
  security: {
    title: 'Security',
    description: 'Access control, audit logs, and governance policies.',
    icon: Shield,
  },
} as const

function SettingsHub({
  namespaces,
  onOpenNamespace,
}: {
  namespaces: SettingsNamespace[]
  onOpenNamespace: (namespace: string) => void
}) {
  const [search, setSearch] = useState('')

  const filteredNamespaces = useMemo(() => {
    if (!search) return namespaces
    const s = search.toLowerCase()
    return namespaces.filter(
      (ns) => ns.name.toLowerCase().includes(s) || (ns.label || '').toLowerCase().includes(s)
    )
  }, [namespaces, search])

  const groups = (['system', 'app', 'security'] as const)
    .map((level) => ({
      level,
      namespaces: filteredNamespaces.filter((item) => (item.level || 'app') === level),
    }))
    .filter((group) => group.namespaces.length > 0)

  return (
    <div className="flex max-w-[1100px] flex-col gap-8 pb-16">
      <section className="rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6 shadow-sm">
        <div className="flex flex-col justify-between gap-6 md:flex-row md:items-center">
          <div className="min-w-0 flex-1">
            <div className="arc-id arc-dim2">admin</div>
            <h2 className="mt-1 text-[26px] font-semibold text-[var(--text)]">Administration Hub</h2>
            <p className="mt-2 max-w-[600px] text-[14px] leading-6 text-[var(--text-2)]">
              Fine-tune your platform behavior across organization, products, security, and engine infrastructure. 
              Settings are isolated by company to support multi-tenant environments.
            </p>
          </div>
          <div className="relative w-full md:w-72">
            <Settings className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" size={16} />
            <input
              type="text"
              placeholder="Search settings..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-11 w-full rounded-[var(--aras-radius)] border border-[var(--line)] bg-[var(--surface-2)] pl-10 pr-4 text-[13px] text-[var(--text)] outline-none transition-all focus:border-[var(--accent)] focus:bg-[var(--surface)]"
            />
          </div>
        </div>
      </section>

      {groups.length === 0 ? (
        <div className="rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-12 text-center">
          <p className="text-[14px] text-[var(--text-3)]">No settings found matching "{search}"</p>
          <button
            type="button"
            onClick={() => setSearch('')}
            className="mt-3 text-[13px] font-medium text-[var(--accent)] hover:underline"
          >
            Clear search
          </button>
        </div>
      ) : (
        groups.map(({ level, namespaces: items }) => {
          const meta = LEVEL_META[level]
          const HeaderIcon = meta.icon
          return (
            <section key={level}>
              <div className="mb-3 flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-[var(--aras-radius)] bg-[var(--surface-2)] text-[var(--accent)]">
                  <HeaderIcon size={18} />
                </span>
                <div>
                  <h3 className="text-[18px] font-semibold text-[var(--text)]">{meta.title}</h3>
                  <p className="text-[13px] text-[var(--text-3)]">{meta.description}</p>
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {items.map((namespace) => {
                  const Icon = namespace.icon ? resolveIcon(namespace.icon) : Settings
                  return (
                    <Link
                      key={namespace.name}
                      to={`/admin/settings?ns=${encodeURIComponent(namespace.name)}`}
                      onClick={(event) => {
                        event.preventDefault()
                        onOpenNamespace(namespace.name)
                      }}
                      className="group rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-5 shadow-sm transition-transform transition-colors hover:-translate-y-0.5 hover:border-[var(--accent)] hover:bg-[var(--surface-2)]"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-[var(--aras-radius)] bg-[var(--surface-2)] text-[var(--accent)] transition-colors group-hover:bg-[var(--accent)] group-hover:text-white">
                          <Icon size={18} />
                        </span>
                        <span className="arc-mono rounded-full border border-[var(--line)] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[var(--text-3)]">
                          {namespace.section_count || 0} sections
                        </span>
                      </div>
                      <div className="mt-4">
                        <h4 className="text-[16px] font-semibold text-[var(--text)]">
                          {namespace.label || namespace.name}
                        </h4>
                        <p className="arc-mono mt-1 text-[10px] uppercase tracking-[0.12em] text-[var(--text-3)]">
                          {namespace.name}
                        </p>
                      </div>
                    </Link>
                  )
                })}
              </div>
            </section>
          )
        })
      )}
    </div>
  )
}

export default function SettingsPage() {
  const outlet = useOutlet()
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // Legacy redirects. Organization identity moved to the multi-org model at
  // /core-config/core-organizations (single source of truth). The short-lived `platform`
  // namespace was folded back into `core` (instance-wide config). Keep old links working.
  useEffect(() => {
    const ns = searchParams.get('ns')
    if (ns === 'core_config') {
      navigate('/core-config/core-organizations', { replace: true })
    } else if (ns === 'platform') {
      navigate('/admin/settings?ns=core', { replace: true })
    }
  }, [searchParams, navigate])
  const setPageTitle = useUIStore((state) => state.setPageTitle)
  const [namespaces, setNamespaces] = useState<SettingsNamespace[]>([])
  const [selectedNamespace, setSelectedNamespace] = useState<string | null>(
    searchParams.get('ns') || namespaceFromSectionKey(searchParams.get('section'))
  )
  const [dirty, setDirty] = useState(false)
  const { confirm } = useAras()
  const focusedSectionKey = searchParams.get('section')

  const outletSegment = useMemo(
    () => location.pathname.replace(/^\/admin\/settings\/?/, '').split('/')[0] || null,
    [location.pathname]
  )
  const outletMeta = outletSegment ? OUTLET_META[outletSegment] : null

  const setRouteSelection = useCallback((namespace: string, sectionKey?: string | null, replace = false) => {
    const nextParams = new URLSearchParams(searchParams)
    if (namespace) nextParams.set('ns', namespace)
    else nextParams.delete('ns')
    if (sectionKey) nextParams.set('section', sectionKey)
    else nextParams.delete('section')
    setSearchParams(nextParams, { replace })
  }, [searchParams, setSearchParams])

  // Shell owns the page header for every Settings route. Child views must not set it.
  useEffect(() => {
    if (outletMeta) {
      setPageTitle(outletMeta.title, outletMeta.subtitle, outletMeta.breadcrumb)
    } else {
      setPageTitle('Administration', 'Configure framework and app settings from one surface.', 'ADMIN / SETTINGS')
    }
    return () => setPageTitle('', '', '')
  }, [setPageTitle, outletMeta])

  useEffect(() => {
    const next = searchParams.get('ns') || namespaceFromSectionKey(searchParams.get('section'))
    if (next !== selectedNamespace) setSelectedNamespace(next)
  }, [searchParams, selectedNamespace])

  const handleLoaded = useCallback((items: SettingsNamespace[]) => {
    setNamespaces(items)
    const nextSearch = new URLSearchParams(window.location.search)
    const currentSection = nextSearch.get('section')
    const current = nextSearch.get('ns') || namespaceFromSectionKey(currentSection)
    if (current && !items.some((item) => item.name === current)) {
      setSelectedNamespace(null)
      setSearchParams((prev) => { const p = new URLSearchParams(prev); p.delete('ns'); p.delete('section'); return p }, { replace: true })
    }
  }, [setSearchParams])

  const selectNamespace = async (namespace: string) => {
    if (namespace === selectedNamespace) return
    if (dirty && !await confirm({ title: 'Discard changes?', message: 'Discard unsaved settings changes?', confirmText: 'Discard', type: 'danger' })) return
    setSelectedNamespace(namespace)
    setRouteSelection(namespace, null)
  }

  const selected = useMemo(
    () => namespaces.find((item) => item.name === selectedNamespace),
    [namespaces, selectedNamespace]
  )

  const clearSelection = useCallback(async () => {
    if (dirty && !await confirm({ title: 'Discard changes?', message: 'Discard unsaved settings changes?', confirmText: 'Discard', type: 'danger' })) return
    setSelectedNamespace(null)
    const nextParams = new URLSearchParams(searchParams)
    nextParams.delete('ns')
    nextParams.delete('section')
    setSearchParams(nextParams)
  }, [confirm, dirty, searchParams, setSearchParams])

  return (
    <div className="flex min-h-full bg-[var(--bg)]">
      {/* Single nav surface — the sidebar already carries namespaces + Access/Audit/Files/Dashboard. */}
      <aside className="hidden w-72 shrink-0 border-r border-[var(--line)] bg-[var(--bg-2)] md:block">
        <div className="border-b border-[var(--line)] px-5 py-4">
          <div className="arc-id arc-dim2">admin</div>
          <h1 className="mt-1 text-[16px] font-semibold text-[var(--text)]">Administration</h1>
        </div>
        <SettingsNamespaceList selectedNamespace={selectedNamespace} onSelect={selectNamespace} onLoaded={handleLoaded} />
      </aside>

      <main className="min-w-0 flex-1 overflow-y-auto px-4 py-5 md:px-8">
        <div className="mb-5 md:hidden">
          <SettingsNamespaceList selectedNamespace={selectedNamespace} onSelect={selectNamespace} onLoaded={handleLoaded} />
        </div>

        {outlet ? (
          <Outlet />
        ) : (
          <>
            {selectedNamespace ? (
              <>
                <div className="mb-6 flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={clearSelection}
                    className="inline-flex items-center gap-2 rounded-[var(--aras-radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-2 text-[12px] font-semibold text-[var(--text-2)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
                  >
                    <ArrowLeft size={14} />
                    All settings
                  </button>
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="grid h-10 w-10 place-items-center rounded-[var(--aras-radius)] bg-[var(--surface-2)] text-[var(--accent)]">
                      <Settings size={19} />
                    </span>
                    <div className="min-w-0">
                      <h2 className="truncate text-[20px] font-semibold text-[var(--text)]">{selected?.label || selectedNamespace}</h2>
                      <p className="arc-mono mt-0.5 truncate text-[10px] uppercase tracking-[0.14em] text-[var(--text-3)]">
                        {selectedNamespace ? `namespace/${selectedNamespace}` : 'select a namespace'}
                      </p>
                    </div>
                  </div>
                </div>

                <SettingsForm
                  key={selectedNamespace}
                  namespace={selectedNamespace}
                  focusSectionKey={focusedSectionKey}
                  onDirtyChange={setDirty}
                />
              </>
            ) : (
              <SettingsHub namespaces={namespaces} onOpenNamespace={selectNamespace} />
            )}
          </>
        )}
      </main>
    </div>
  )
}

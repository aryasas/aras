// claude-opus-4-7
// ARC app-home: dot-grid hero + dense module/resource list (file-tree feel).
import { useEffect, useMemo, useState } from 'react'
import { Link, useOutletContext, useParams } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import api from '../lib/api'
import { useUIStore } from '../store/uiStore'
import type { SidebarItem, AppMenuData, MenuItem } from '../layouts/types'
import { useVocabulary } from '../context/VocabularyContext'
import { resolveIcon } from '../lib/iconUtils'
import { filterMenuElements, filterMenuItems, isVisibleMenuItem } from '../lib/menuUtils'
import { LoadingState } from '../components/LoadingState'
import { EmptyState } from '../components/EmptyState'

interface OutletContext { sidebarData: SidebarItem[] }

export default function AppHome() {
  const vocabulary = useVocabulary()
  const params = useParams()
  const { sidebarData } = useOutletContext<OutletContext>()
  const [remoteMenu, setRemoteMenu] = useState<AppMenuData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const setPageTitle = useUIStore(state => state.setPageTitle)

  const appPath = useMemo(() => {
    const splat = params['*'] || ''
    return [params.segment1, ...splat.split('/').filter(Boolean)].filter(Boolean).join('/')
  }, [params])

  const sidebarApp = useMemo(
    () => sidebarData.find((item) => (item.path || `/${item.name}`).replace(/^\//, '') === appPath),
    [appPath, sidebarData]
  )

  useEffect(() => {
    const appLabel = remoteMenu?.app_label || sidebarApp?.label || appPath
    if (appLabel) {
      setPageTitle(vocabulary.get(appLabel), 'Select a module or resource to continue.', appPath.replace(/\//g, ' / ').toUpperCase())
    }
    return () => setPageTitle('', '', '')
  }, [remoteMenu, sidebarApp, appPath, vocabulary, setPageTitle])

  useEffect(() => {
    let cancelled = false
    if (!appPath) { setRemoteMenu(null); return }
    setIsLoading(true)
    api.get(`/app-menu/${appPath}`)
      .then((res) => { if (!cancelled) setRemoteMenu(res.data) })
      .catch(() => { if (!cancelled) setRemoteMenu(null) })
      .finally(() => { if (!cancelled) setIsLoading(false) })
    return () => { cancelled = true }
  }, [appPath])

  if (!appPath || isLoading) return <LoadingState label="Loading application..." className="arc-card border-dashed" />
  if (!remoteMenu && !sidebarApp) return <EmptyState title="Application not found" />

  const appInfo = remoteMenu || { app_label: sidebarApp?.label || appPath, icon: sidebarApp?.icon || 'Package', menu: [], sub_apps: [] }
  const moduleItems = (appInfo.sub_apps || []).filter(isVisibleMenuItem)
  const resourceItems = filterMenuElements(appInfo.menu || []).flatMap((element: any) => {
    if (element.type === 'group') {
      return filterMenuItems(element.items).map((item: MenuItem) => ({ ...item, groupLabel: element.label }))
    }
    return [{ ...element, groupLabel: 'Resources' }]
  })
  const grouped = resourceItems.reduce<Record<string, typeof resourceItems>>((acc, item) => {
    const k = item.groupLabel || 'Resources'
    if (!acc[k]) acc[k] = []
    acc[k].push(item)
    return acc
  }, {})
  const hasContent = moduleItems.length > 0 || resourceItems.length > 0
  const AppIcon = resolveIcon(appInfo.icon || sidebarApp?.icon || 'Package')

  const renderRow = (item: MenuItem & { groupLabel?: string }) => {
    const ItemIcon = resolveIcon(item.icon || 'FileText')
    return (
      <Link key={item.name} to={item.path} className="group flex items-center gap-2 px-3 py-2 border-t border-[var(--line)] hover:bg-[var(--surface-2)] transition-colors">
        <ItemIcon size={13} className="text-[var(--text-3)] group-hover:text-[var(--accent)] shrink-0" />
        <span className="text-[12.5px] font-medium text-[var(--text)] truncate flex-1">{vocabulary.get(item.label || item.name)}</span>
        <ChevronRight size={11} className="text-[var(--text-3)] group-hover:text-[var(--accent)] shrink-0 opacity-0 group-hover:opacity-100" />
      </Link>
    )
  }

  const renderSection = (groupLabel: string, items: typeof resourceItems, key: string) => (
    <section key={key} className="arc-card overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
        <span className="arc-id" style={{ fontSize: 10 }}><b>{vocabulary.get(groupLabel).toLowerCase().replace(/\s+/g, '-')}</b></span>
        <span className="arc-id arc-dim2" style={{ fontSize: 10 }}>{items.length}</span>
      </div>
      {items.map((item) => renderRow(item))}
    </section>
  )

  // Split groups across 3 columns, preserving group order
  const allSections: Array<{ key: string; label: string; items: typeof resourceItems }> = [
    ...(moduleItems.length > 0 ? [{ key: '__modules__', label: 'modules', items: moduleItems.map((s: any) => ({ ...s, groupLabel: 'Module' })) }] : []),
    ...Object.entries(grouped).map(([label, items]) => ({ key: label, label, items })),
  ]

  const cols: typeof allSections[] = [[], [], []]
  allSections.forEach((s, i) => cols[i % 3].push(s))

  return (
    <div className="arc flex flex-col gap-4">
      {/* Hero */}
      <div className="arc-card arc-dotgrid px-5 py-4 flex items-center gap-4" style={{ background: 'var(--bg-2)' }}>
        <div className="grid place-items-center w-10 h-10 rounded-[var(--radius)]"
             style={{ background: 'color-mix(in oklch, var(--accent) 18%, var(--surface))', color: 'var(--accent)', border: '1px solid color-mix(in oklch, var(--accent) 35%, var(--line))' }}>
          <AppIcon size={20} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="arc-id" style={{ fontSize: 10 }}><b>app</b>/{appPath}</div>
          <h1 className="text-[17px] font-semibold text-[var(--text)] tracking-tight">{vocabulary.get(appInfo.app_label || appPath)}</h1>
        </div>
        <span className="arc-id arc-dim2" style={{ fontSize: 11 }}>{moduleItems.length} modules · {resourceItems.length} resources</span>
      </div>

      {/* 3-column grid of groups */}
      {hasContent ? (
        <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(3, 1fr)', alignItems: 'start' }}>
          {cols.map((col, ci) => (
            <div key={ci} className="flex flex-col gap-4">
              {col.map((s) => renderSection(s.label, s.items, s.key))}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No resources available" description="This application has no visible resources." />
      )}
    </div>
  )
}

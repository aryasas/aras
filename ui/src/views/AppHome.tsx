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
      <Link key={item.name} to={item.path} className="group flex items-center gap-3 px-4 py-2.5 border-t border-[var(--line)] hover:bg-[var(--surface-2)] transition-colors">
        <ItemIcon size={14} className="text-[var(--text-3)] group-hover:text-[var(--accent)] shrink-0" />
        <span className="text-[13px] font-medium text-[var(--text)] truncate flex-1">{vocabulary.get(item.label || item.name)}</span>
        <span className="arc-id arc-dim2 truncate">{item.path}</span>
        <ChevronRight size={13} className="text-[var(--text-3)] group-hover:text-[var(--accent)] shrink-0" />
      </Link>
    )
  }

  return (
    <div className="arc flex flex-col gap-5">
      {/* Hero */}
      <div className="arc-card arc-dotgrid p-6 flex items-center gap-5" style={{ background: 'var(--bg-2)' }}>
        <div className="grid place-items-center w-14 h-14 rounded-[var(--radius-lg)]"
             style={{ background: 'color-mix(in oklch, var(--accent) 18%, var(--surface))', color: 'var(--accent)', border: '1px solid color-mix(in oklch, var(--accent) 35%, var(--line))' }}>
          <AppIcon size={26} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="arc-id"><b>app</b>/{appPath}</div>
          <h1 className="text-[20px] font-semibold text-[var(--text)] tracking-tight mt-0.5">{vocabulary.get(appInfo.app_label || appPath)}</h1>
          <div className="arc-dim text-[12px] mt-0.5">
            {moduleItems.length} modules · {resourceItems.length} resources
          </div>
        </div>
      </div>

      {moduleItems.length > 0 && (
        <section className="arc-card overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
            <span className="arc-id"><b>modules</b></span>
            <span className="arc-id arc-dim2">{moduleItems.length}</span>
          </div>
          {moduleItems.map((sub: any) => renderRow({ ...sub, groupLabel: 'Module' }))}
        </section>
      )}

      {Object.entries(grouped).map(([groupLabel, items]) => (
        <section key={groupLabel} className="arc-card overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
            <span className="arc-id"><b>{vocabulary.get(groupLabel).toLowerCase().replace(/\s+/g, '-')}</b></span>
            <span className="arc-id arc-dim2">{items.length}</span>
          </div>
          {items.map((item) => renderRow(item))}
        </section>
      ))}

      {!hasContent && <EmptyState title="No resources available" description="This application has no visible resources." />}
    </div>
  )
}

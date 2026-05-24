import { useEffect, useMemo, useState } from 'react'
import { Link, useOutletContext, useParams } from 'react-router-dom'
import api from '../lib/api'
import { useUIStore } from '../store/uiStore'
import type { SidebarItem, AppMenuData, MenuItem } from '../layouts/types'
import { useVocabulary } from '../context/VocabularyContext'
import { resolveIcon } from '../lib/iconUtils'
import { filterMenuElements, filterMenuItems, isVisibleMenuItem } from '../lib/menuUtils'
import { LoadingState } from '../components/LoadingState'
import { EmptyState } from '../components/EmptyState'

interface OutletContext {
  sidebarData: SidebarItem[]
}

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
    () => sidebarData.find((item) => {
      const itemPath = (item.path || `/${item.name}`).replace(/^\//, '')
      return itemPath === appPath
    }),
    [appPath, sidebarData]
  )

  useEffect(() => {
    const appLabel = remoteMenu?.app_label || sidebarApp?.label || appPath
    if (appLabel) {
      setPageTitle(
        vocabulary.get(appLabel),
        'Select a module or resource to continue.',
        appPath.replace(/\//g, ' / ').toUpperCase()
      )
    }
    return () => setPageTitle('', '', '')
  }, [remoteMenu, sidebarApp, appPath, vocabulary, setPageTitle])

  useEffect(() => {
    let cancelled = false
    if (!appPath) {
      setRemoteMenu(null)
      return
    }
    setIsLoading(true)
    api.get(`/app-menu/${appPath}`)
      .then((res) => { if (!cancelled) setRemoteMenu(res.data) })
      .catch(() => { if (!cancelled) setRemoteMenu(null) })
      .finally(() => { if (!cancelled) setIsLoading(false) })
    return () => { cancelled = true }
  }, [appPath])

  if (!appPath || isLoading) {
    return (
      <LoadingState label="Loading application..." className="bg-white rounded-2xl border border-dashed border-slate-200" />
    )
  }

  if (!remoteMenu && !sidebarApp) {
    return <EmptyState title="Application not found" />
  }

  const appInfo = remoteMenu || {
    app_label: sidebarApp?.label || appPath,
    icon: sidebarApp?.icon || 'Package',
    menu: [],
    sub_apps: []
  }

  const moduleItems = (appInfo.sub_apps || []).filter(isVisibleMenuItem)

  const resourceItems = filterMenuElements(appInfo.menu || []).flatMap((element: any) => {
    if (element.type === 'group') {
      return filterMenuItems(element.items).map((item: MenuItem) => ({
        ...item,
        groupLabel: element.label
      }))
    }
    return [{ ...element, groupLabel: 'Resources' }]
  })

  const hasContent = moduleItems.length > 0 || resourceItems.length > 0

  const renderRow = (item: MenuItem & { groupLabel?: string }) => {
    const ItemIcon = resolveIcon(item.icon || 'FileText')
    const label = vocabulary.get(item.label || item.name)
    return (
      <Link
        key={item.name}
        to={item.path}
        className="aras-app-row group"
      >
        <div className="aras-app-row__icon">
          <ItemIcon size={15} strokeWidth={2.2} />
        </div>
        <span className="aras-app-row__label">{label}</span>
      </Link>
    )
  }

  const groupedResources = resourceItems.reduce<Record<string, typeof resourceItems>>((acc, item) => {
    const key = item.groupLabel || 'Resources'
    if (!acc[key]) acc[key] = []
    acc[key].push(item)
    return acc
  }, {})

  return (
    <div className="aras-app-home animate-in fade-in slide-in-from-bottom-2 duration-300">
      {moduleItems.length > 0 && (
        <section className="aras-app-section" aria-labelledby="app-home-modules">
          <div className="aras-app-section__heading">
            <div>
              <p>{vocabulary.get(appInfo.app_label || appPath)}</p>
              <h2 id="app-home-modules">Modules</h2>
            </div>
          </div>
          <div className="aras-app-list">
            {moduleItems.map((sub: any) => renderRow({ ...sub, groupLabel: 'Module' }))}
          </div>
        </section>
      )}

      {Object.entries(groupedResources).map(([groupLabel, items]) => (
        <section key={groupLabel} className="aras-app-section" aria-labelledby={`group-${groupLabel}`}>
          <div className="aras-app-section__heading">
            <div>
              <p>Work Objects</p>
              <h2 id={`group-${groupLabel}`}>{vocabulary.get(groupLabel)}</h2>
            </div>
          </div>
          <div className="aras-app-list">
            {items.map((item) => renderRow(item))}
          </div>
        </section>
      ))}

      {!hasContent && (
        <EmptyState title="No resources available" description="This application has no visible resources." />
      )}
    </div>
  )
}

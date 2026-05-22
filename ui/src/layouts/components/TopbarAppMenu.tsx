import { useEffect, useMemo, useState, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronDown, MoreHorizontal } from 'lucide-react'
import api from '../../lib/api'
import type { AppMenuData, MenuItem, SidebarApp, MenuElement } from '../types'
import { useVocabulary } from '../../context/VocabularyContext'
import { resolveIcon } from '../../lib/iconUtils'
import { filterMenuElements, filterMenuItems, isVisibleMenuItem } from '../../lib/menuUtils'

const hiddenTopbarRoutes = new Set(['dashboard', 'settings'])

interface TopbarProps {
  sidebarData?: SidebarApp[]
}

export function TopbarAppMenu({ sidebarData = [] }: TopbarProps) {
  const vocabulary = useVocabulary()
  const location = useLocation()
  const [menuData, setMenuData] = useState<AppMenuData | null>(null)
  const [failedApp, setFailedApp] = useState<string | null>(null)
  const [moreOpen, setMoreOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const appName = useMemo(() => {
    const [firstSegment] = location.pathname.split('/').filter(Boolean)
    return firstSegment || null
  }, [location.pathname])

  const rootAppName = useMemo(() => {
    if (!appName) return null
    for (const app of sidebarData) {
      if (app.name === appName) return app.name
      if (app.sub_apps?.some(sub => sub.name === appName)) {
        return app.name
      }
    }
    return appName
  }, [appName, sidebarData])

  useEffect(() => {
    let cancelled = false

    if (!rootAppName || hiddenTopbarRoutes.has(rootAppName)) {
      setMenuData(null)
      setFailedApp(null)
      return
    }

    setFailedApp(null)
    api.get(`/app-menu/${rootAppName}`)
      .then((res) => {
        if (!cancelled) setMenuData(res.data)
      })
      .catch(() => {
        if (!cancelled) {
          setMenuData(null)
          setFailedApp(rootAppName)
        }
      })

    return () => {
      cancelled = true
    }
  }, [rootAppName])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setMoreOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (!appName || failedApp === rootAppName || !menuData) {
    return null
  }

  const renderMenuItem = (item: MenuItem, isDropdownItem = false) => {
    const isHome = item.path === `/${rootAppName}`
    const isActive = isHome
      ? location.pathname === item.path
      : location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)

    if (isDropdownItem) {
      const Icon = resolveIcon(item.icon || 'FileText')
      return (
        <Link
          key={item.name}
          to={item.path}
          onClick={() => setMoreOpen(false)}
          className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all ${
            isActive 
              ? 'font-semibold'
              : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)] hover:text-[var(--aras-text)]'
          }`}
          style={isActive ? { color: 'var(--aras-accent)', backgroundColor: 'color-mix(in srgb, var(--aras-accent) 10%, transparent)' } : undefined}
        >
          <Icon size={18} className={isActive ? 'text-[var(--aras-accent)]' : 'text-[var(--aras-muted)]'} />
          {vocabulary.get(item.label || item.name)}
        </Link>
      )
    }

    return (
      <Link
        key={item.name}
        to={item.path}
        onClick={() => setMoreOpen(false)}
        className={`relative flex h-10 shrink-0 items-center gap-2 px-3 rounded-xl text-[13px] font-bold transition-all ${
          isActive
            ? 'bg-[var(--aras-accent)] text-white shadow-sm'
            : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)] hover:text-[var(--aras-text)]'
        }`}
      >
        {item.icon && (() => {
          const Icon = resolveIcon(item.icon)
          return <Icon size={16} className="shrink-0" />
        })()}
        {vocabulary.get(item.label || item.name)}
      </Link>
    )
  }

  const rootElements = filterMenuElements(menuData.menu || [])
  const directRootItems = rootElements.filter((element) => element.type !== 'group') as MenuItem[]
  const rootGroups = rootElements.filter((element) => element.type === 'group') as MenuElement[]
  const visibleRootItems = directRootItems.slice(0, 2)
  const activeModule = (menuData.sub_apps || [])
    .filter(isVisibleMenuItem)
    .find((sub) => location.pathname === sub.path || location.pathname.startsWith(`${sub.path}/`))
  const moduleElements = activeModule?.menu ? filterMenuElements(activeModule.menu) : []
  const moduleItems = moduleElements.flatMap((element) => element.type === 'group' ? filterMenuItems(element.items) : [element as MenuItem])
  const visibleModuleItems = moduleItems.slice(0, 5)
  const overflowRootItems = directRootItems.slice(2)
  const overflowModuleItems = moduleItems.slice(5)
  const hasMore = rootGroups.length > 0 || overflowRootItems.length > 0 || overflowModuleItems.length > 0

  return (
    <nav className="max-w-full overflow-x-auto hide-scroll" aria-label="Module resources">
      <div ref={dropdownRef} className="flex w-fit max-w-full flex-nowrap items-center gap-1 rounded-[calc(var(--aras-radius-lg)*0.5)] bg-[var(--aras-panel-soft)] p-1 shadow-sm ring-1 ring-[var(--aras-border)]">
        <span className="px-3 text-[10px] font-black uppercase tracking-[0.14em] text-[var(--aras-muted)]">
          {activeModule ? vocabulary.get(activeModule.label) : vocabulary.get(menuData.app_label)}
        </span>
        {menuData.have_home && renderMenuItem({
          type: 'model',
          name: '__home__',
          label: 'Home',
          path: `/${rootAppName}`
        })}
        
        {visibleRootItems.map((element) => renderMenuItem(element))}
        {visibleModuleItems.map((element) => renderMenuItem(element))}

        {hasMore && (
          <div className="relative">
            <button
              type="button"
              onClick={() => setMoreOpen(!moreOpen)}
              className="flex h-10 shrink-0 items-center gap-1.5 rounded-xl px-3 text-[13px] font-bold text-[var(--aras-muted)] transition-all hover:bg-[var(--aras-panel-soft)] hover:text-[var(--aras-text)]"
            >
              <MoreHorizontal size={16} />
              More
              <ChevronDown size={14} className={`transition-transform duration-200 ${moreOpen ? 'rotate-180' : ''}`} />
            </button>
            {moreOpen && (
              <div className="absolute right-0 top-full z-50 mt-2 min-w-[280px] rounded-[calc(var(--aras-radius)*0.75)] border border-[var(--aras-border)] bg-[var(--aras-panel)] p-1.5 shadow-[0_18px_45px_-18px_rgba(15,23,42,0.35)] animate-in fade-in zoom-in-95 duration-100 max-h-[70vh] overflow-y-auto">
                {rootGroups.map((element) => {
                  if (element.type !== 'group') return null
                  return (
                    <div key={`more-root-${element.label}`} className="mt-1 first:mt-0">
                      <div className="px-3 py-1.5 text-[10px] font-black text-[var(--aras-muted)] uppercase tracking-wider">
                        {vocabulary.get(element.label)}
                      </div>
                      <div className="space-y-0.5">
                        {filterMenuItems(element.items).map(item => renderMenuItem(item, true))}
                      </div>
                    </div>
                  )
                })}
                {overflowRootItems.length > 0 && (
                  <div className="mt-1 first:mt-0">
                    <div className="px-3 py-1.5 text-[10px] font-black text-[var(--aras-muted)] uppercase tracking-wider">Resources</div>
                    <div className="space-y-0.5">
                      {overflowRootItems.map(item => renderMenuItem(item, true))}
                    </div>
                  </div>
                )}
                {overflowModuleItems.length > 0 && (
                  <div className="mt-1 first:mt-0">
                    <div className="px-3 py-1.5 text-[10px] font-black text-[var(--aras-muted)] uppercase tracking-wider">More Resources</div>
                    <div className="space-y-0.5">
                      {overflowModuleItems.map(item => renderMenuItem(item, true))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  )
}

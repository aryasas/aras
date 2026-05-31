import { useState, useEffect, useMemo } from 'react'
import { ChevronRight, CreditCard, HelpCircle, Hexagon, Menu, PanelLeftClose, PanelLeftOpen, Settings } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { SidebarApp, MenuItem } from '../types'
import { useVocabulary } from '../../context/VocabularyContext'
import { resolveIcon } from '../../lib/iconUtils'
import { isVisibleMenuItem, filterMenuItems, filterMenuElements } from '../../lib/menuUtils'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'
import api from '../../lib/api'
import { SortableList, DragHandle } from '../../aras-core/components/SortableList'

interface SidebarProps {
  sidebarData: SidebarApp[]
  currentPath: string
}

interface FlatMenuItem extends MenuItem { id: string; groupLabel?: string }

function normalizeRoutePath(path?: string) {
  if (!path) return '/'
  const normalized = path.startsWith('/') ? path : `/${path}`
  return normalized.length > 1 ? normalized.replace(/\/+$/, '') : normalized
}

function appRoutePath(item?: Pick<SidebarApp, 'name' | 'path'> | null) {
  if (!item) return '/'
  if (item.name === 'settings' || item.path === '/settings') return '/admin/settings'
  return normalizeRoutePath(item.path || `/${item.name}`)
}

function isRouteMatch(currentPath: string, targetPath?: string) {
  const current = normalizeRoutePath(currentPath)
  const target = normalizeRoutePath(targetPath)
  return current === target || current.startsWith(`${target}/`)
}

const getArasRole = () => {
  const injectedRole = (globalThis as any).__ARAS_ROLE__
  return String(injectedRole || import.meta.env.VITE_ARAS_ROLE || 'tenant')
}

export function Sidebar({ sidebarData, currentPath }: SidebarProps) {
  const vocabulary = useVocabulary()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const submenuOrder = useUIStore((s) => s.submenuOrder)
  const setSubmenuOrder = useUIStore((s) => s.setSubmenuOrder)
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)
  const iconRailCollapsed = useUIStore((s) => s.iconRailCollapsed)
  const toggleIconRail = useUIStore((s) => s.toggleIconRail)
  const mobileSidebarOpen = useUIStore((s) => s.mobileSidebarOpen)
  const setMobileSidebarOpen = useUIStore((s) => s.setMobileSidebarOpen)
  
  const [menuData, setMenuData] = useState<any>(null)
  const [isLoadingMenu, setIsLoadingMenu] = useState(false)
  const isControlPanel = getArasRole() === 'control-panel'

  const apps = useMemo(() => sidebarData.filter((item) => 
    isVisibleMenuItem(item) && 
    !item.hide_from_sidebar && 
    item.name !== 'settings' && 
    item.name !== 'help'
  ), [sidebarData])
  const initial = (user?.full_name || user?.username || 'A')[0].toUpperCase()

  // Derive active app directly from URL so the selector stays in sync with route changes.
  const activeApp = useMemo(() => {
    const current = normalizeRoutePath(currentPath)
    return apps
      .map((app) => ({ app, path: appRoutePath(app) }))
      .filter(({ path }) => isRouteMatch(current, path))
      .sort((a, b) => b.path.length - a.path.length)[0]?.app || null
  }, [currentPath, apps])

  // Fetch menu data when active app changes
  useEffect(() => {
    if (!activeApp) {
      setMenuData(null)
      return
    }
    
    let cancelled = false
    setIsLoadingMenu(true)
    if (activeApp.type === 'link') {
      setMenuData(null)
      setIsLoadingMenu(false)
      return
    }

    const menuPath = normalizeRoutePath(activeApp.path || `/${activeApp.name}`).replace(/^\//, '')
    api.get(`/app-menu/${menuPath}`)
      .then((res) => {
        if (!cancelled) setMenuData(res.data)
      })
      .catch(() => {
        if (!cancelled) setMenuData(null)
      })
      .finally(() => {
        if (!cancelled) setIsLoadingMenu(false)
      })
      
    return () => { cancelled = true }
  }, [activeApp?.name, activeApp?.path, activeApp?.type])

  // Flatten menu groups into a single ordered list (id = path) for DnD.
  const flatItems = useMemo<FlatMenuItem[]>(() => {
    if (!menuData) return []
    const elements = filterMenuElements(menuData.menu || [])
    
    // Add sub_apps as well if they are not already in menu (as app_links)
    const existingPaths = new Set(elements.map((e: any) => (e as any).path).filter(Boolean))
    const subApps = (menuData.sub_apps || []).filter((sa: any) => !existingPaths.has(sa.path))
    
    const allElements = [...elements, ...subApps.map((sa: any) => ({ ...sa, type: 'app_link' }))]
    const items: FlatMenuItem[] = []

    allElements.forEach((el: any) => {
      const label = (el.label || '').toLowerCase()
      const name = (el.name || '').toLowerCase()
      if (label.includes('setting') || name.includes('setting') || label.includes('admin') || name.includes('admin')) return

      if (el.type === 'group') {
        filterMenuItems(el.items || []).forEach((i: MenuItem) => {
          const il = (i.label || '').toLowerCase()
          const inm = (i.name || '').toLowerCase()
          if (il.includes('setting') || inm.includes('setting') || il.includes('admin') || inm.includes('admin')) return
          items.push({ ...i, id: i.path || i.name, groupLabel: el.label })
        })
      } else {
        items.push({ ...el, id: el.path || el.name, groupLabel: 'General' })
      }
    })
    return items
  }, [menuData])

  // Apply persisted order for this app.
  const orderedItems = useMemo<FlatMenuItem[]>(() => {
    if (!activeApp) return []
    const saved = submenuOrder[activeApp.name]
    if (!saved || !saved.length) return flatItems
    const byId = new Map(flatItems.map((it) => [it.id, it]))
    const reordered: FlatMenuItem[] = []
    saved.forEach((id) => { const it = byId.get(id); if (it) { reordered.push(it); byId.delete(id) } })
    byId.forEach((it) => reordered.push(it))
    return reordered
  }, [flatItems, submenuOrder, activeApp])

  // Auto-close mobile drawer on route change.
  useEffect(() => {
    if (mobileSidebarOpen) setMobileSidebarOpen(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPath])

  const handleReorder = (next: FlatMenuItem[]) => {
    if (!activeApp) return
    setSubmenuOrder(activeApp.name, next.map((it) => it.id))
  }

  const firstPathFromMenuData = (data: any) => {
    const elements = filterMenuElements(data?.menu || [])
    const existingPaths = new Set(elements.map((e: any) => (e as any).path).filter(Boolean))
    const subApps = (data?.sub_apps || []).filter((sa: any) => !existingPaths.has(sa.path))
    const allElements = [...elements, ...subApps.map((sa: any) => ({ ...sa, type: 'app_link' }))]

    for (const el of allElements) {
      const label = (el.label || '').toLowerCase()
      const name = (el.name || '').toLowerCase()
      if (label.includes('setting') || name.includes('setting') || label.includes('admin') || name.includes('admin')) continue

      if (el.type === 'group') {
        const firstItem = filterMenuItems(el.items || []).find((i: MenuItem) => {
          const il = (i.label || '').toLowerCase()
          const inm = (i.name || '').toLowerCase()
          return !il.includes('setting') && !inm.includes('setting') && !il.includes('admin') && !inm.includes('admin')
        })
        if (firstItem?.path) return normalizeRoutePath(firstItem.path)
      } else if (el.path) {
        return normalizeRoutePath(el.path)
      }
    }

    return null
  }

  const handleAppClick = async (item: SidebarApp) => {
    const appRoot = appRoutePath(item)
    if (item.name === 'settings' || item.path === '/settings') {
      navigate(appRoot)
      return
    }
    if (item.type === 'link') {
      navigate(appRoot)
      return
    }

    const currentAppRoot = appRoutePath(activeApp)
    if (appRoot === currentAppRoot && orderedItems[0]?.path) {
      navigate(normalizeRoutePath(orderedItems[0].path))
      return
    }

    const saved = submenuOrder[item.name]?.[0]
    if (saved) {
      navigate(normalizeRoutePath(saved))
      return
    }

    try {
      const menuPath = appRoot.replace(/^\//, '')
      const res = await api.get(`/app-menu/${menuPath}`)
      navigate(firstPathFromMenuData(res.data) || appRoot)
    } catch {
      navigate(appRoot)
    }
  }

  return (
    <>
      {/* Mobile backdrop */}
      {mobileSidebarOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/40"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}
    <div
      className={`flex h-full max-md:fixed max-md:inset-y-0 max-md:left-0 max-md:z-50 max-md:shadow-xl max-md:transition-transform max-md:duration-200 ${mobileSidebarOpen ? 'max-md:translate-x-0' : 'max-md:-translate-x-full'}`}
    >
      {/* App rail (Icons or Icons + Text) */}
      <aside
        className="flex flex-col shrink-0 z-40 transition-[width] duration-300"
        style={{
          width: iconRailCollapsed ? 0 : (sidebarCollapsed ? 56 : 180),
          background: 'var(--bg-2)',
          borderRight: iconRailCollapsed ? 'none' : '1px solid var(--line)',
          overflow: iconRailCollapsed ? 'hidden' : undefined,
        }}
      >
        <div
          className="flex items-center px-4"
          style={{ 
            height: 52, 
            borderBottom: '1px solid var(--line)',
            justifyContent: sidebarCollapsed ? 'center' : 'space-between',
            padding: sidebarCollapsed ? '0' : '0 12px'
          }}
        >
          <div className="flex items-center" style={{ minWidth: 0 }}>
            <Hexagon size={20} className="text-[var(--accent)] shrink-0" />
            {!sidebarCollapsed && !iconRailCollapsed && (
              <span className="ml-2.5 font-bold text-sm truncate uppercase tracking-wider text-[var(--text)]">
                Aras
              </span>
            )}
          </div>
          {!sidebarCollapsed && (
            <div className="flex items-center gap-0.5">
              <button
                onClick={toggleIconRail}
                title="Hide Rail"
                className="p-1.5 hover:bg-[var(--surface-2)] rounded-md text-[var(--text-3)] hover:text-[var(--text)] transition-colors"
              >
                <Menu size={16} />
              </button>
              <button
                onClick={toggleSidebar}
                title="Collapse"
                className="p-1.5 hover:bg-[var(--surface-2)] rounded-md text-[var(--text-3)] hover:text-[var(--text)] transition-colors"
              >
                <PanelLeftClose size={16} />
              </button>
            </div>
          )}
        </div>

        <div className="flex-1 flex flex-col gap-1 py-3 overflow-y-auto arc-scroll px-2">
          {user?.is_admin && isControlPanel && (
            <button
              type="button"
              title={sidebarCollapsed ? 'Control Panel' : undefined}
              onClick={() => navigate('/control-panel')}
              className="group relative flex items-center transition-all duration-200"
              style={{
                width: '100%',
                height: 38,
                padding: sidebarCollapsed ? '0' : '0 10px',
                justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                borderRadius: 'var(--radius)',
                background: isRouteMatch(currentPath, '/control-panel') ? 'var(--surface-2)' : 'transparent',
                border: isRouteMatch(currentPath, '/control-panel') ? '1px solid var(--line)' : '1px solid transparent',
                color: isRouteMatch(currentPath, '/control-panel') ? 'var(--text)' : 'var(--text-3)',
              }}
            >
              <CreditCard size={17} className="shrink-0" />
              {!sidebarCollapsed && (
                <span className="ml-3 text-[13px] font-medium truncate opacity-90 group-hover:opacity-100">
                  Control Panel
                </span>
              )}
              {isRouteMatch(currentPath, '/control-panel') && (
                <span style={{
                  position: 'absolute', left: -2, top: 8, bottom: 8, width: 2,
                  background: 'var(--accent)', borderRadius: 2,
                }} />
              )}
            </button>
          )}
          {apps.map((item) => {
            const Icon = resolveIcon(item.icon)
            const itemPath = appRoutePath(item)
            const isActive = activeApp?.name === item.name || isRouteMatch(currentPath, itemPath)
            const label = vocabulary.get(item.label)
            
            return (
              <button
                type="button"
                key={item.name}
                title={sidebarCollapsed ? label : undefined}
                onClick={() => handleAppClick(item)}
                className="group relative flex items-center transition-all duration-200"
                style={{
                  width: '100%',
                  height: 38,
                  padding: sidebarCollapsed ? '0' : '0 10px',
                  justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                  borderRadius: 'var(--radius)',
                  background: isActive ? 'var(--surface-2)' : 'transparent',
                  border: isActive ? '1px solid var(--line)' : '1px solid transparent',
                  color: isActive ? 'var(--text)' : 'var(--text-3)',
                }}
              >
                <Icon size={17} className="shrink-0" />
                {!sidebarCollapsed && (
                  <span className="ml-3 text-[13px] font-medium truncate opacity-90 group-hover:opacity-100">
                    {label}
                  </span>
                )}
                {isActive && (
                  <span style={{
                    position: 'absolute', left: -2, top: 8, bottom: 8, width: 2,
                    background: 'var(--accent)', borderRadius: 2,
                  }} />
                )}
              </button>
            )
          })}
        </div>

        <div className="flex flex-col gap-2 py-3 px-2" style={{ borderTop: '1px solid var(--line)' }}>
          {sidebarCollapsed && (
            <button
              onClick={toggleSidebar}
              title="Expand"
              className="flex items-center justify-center hover:text-[var(--text)] text-[var(--text-3)] transition-colors mb-2"
              style={{ width: '100%', height: 32, borderRadius: 8 }}
            >
              <PanelLeftOpen size={16} />
            </button>
          )}
          <button
            onClick={() => navigate('/admin/settings')}
            title="Settings"
            className="flex items-center hover:text-[var(--text)] text-[var(--text-3)] transition-colors"
            style={{ 
              width: '100%', 
              height: 32, 
              borderRadius: 8,
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
              padding: sidebarCollapsed ? '0' : '0 10px'
            }}
          >
            <Settings size={16} className="shrink-0" />
            {!sidebarCollapsed && <span className="ml-3 text-xs font-medium">Settings</span>}
          </button>
          <button
            onClick={() => navigate('/help')}
            title="Help"
            className="flex items-center hover:text-[var(--text)] text-[var(--text-3)] transition-colors"
            style={{ 
              width: '100%', 
              height: 32, 
              borderRadius: 8,
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
              padding: sidebarCollapsed ? '0' : '0 10px'
            }}
          >
            <HelpCircle size={16} className="shrink-0" />
            {!sidebarCollapsed && <span className="ml-3 text-xs font-medium">Help</span>}
          </button>
          <div className="flex items-center" style={{ 
              width: '100%', 
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
              padding: sidebarCollapsed ? '0' : '0 10px',
              marginTop: 4
            }}>
            <div className="arc-av shrink-0" style={{
              width: 28, height: 28,
              background: 'color-mix(in oklch, var(--accent) 22%, var(--surface))',
              color: 'var(--accent)',
              boxShadow: '0 0 0 1.5px var(--accent), 0 0 0 3px var(--bg)',
            }}>
              <span className="arc-mono">{initial}</span>
            </div>
            {!sidebarCollapsed && (
              <div className="ml-3 min-w-0">
                <div className="text-[11px] font-bold truncate text-[var(--text)]">{user?.full_name || user?.username}</div>
                <div className="text-[9px] text-[var(--text-3)] truncate uppercase tracking-tighter">Administrator</div>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* 200px Section panel — hidden on phones unless drawer open */}
      {activeApp?.type !== 'link' && activeApp && !sidebarCollapsed && !iconRailCollapsed && (
        <aside
          className={`flex-col shrink-0 z-30 ${mobileSidebarOpen ? 'flex' : 'max-md:hidden flex'}`}
          style={{ width: 200, background: 'var(--bg-2)', borderRight: '1px solid var(--line)' }}
        >
          <div style={{ padding: '20px 14px 12px' }}>
            <div className="arc-id arc-dim2" style={{ textTransform: 'uppercase', letterSpacing: '.16em', paddingLeft: 4, fontSize: 10 }}>
              Sections
            </div>
          </div>

          <div className="flex-1 overflow-y-auto arc-scroll" style={{ padding: '0 8px 12px' }}>
            {isLoadingMenu ? (
              <div className="py-6 text-center"><div className="arc-id arc-dim2">loading…</div></div>
            ) : orderedItems.length === 0 ? (
              <div className="py-6 text-center"><div className="arc-id arc-dim2">empty</div></div>
            ) : (
              <SortableList
                items={orderedItems}
                onReorder={handleReorder}
                renderItem={(item) => {
                  const target = normalizeRoutePath(item.path)
                  const isActive = isRouteMatch(currentPath, target)
                  const n = String(orderedItems.findIndex((i) => i.id === item.id) + 1).padStart(2, '0')
                  return (
                    <div className="group relative w-full">
                      <button
                        type="button"
                        onClick={() => navigate(target)}
                        className="w-full flex items-center gap-2 text-left transition-colors"
                        style={{
                          padding: '8px 34px 8px 10px', borderRadius: 'var(--radius)',
                          background: isActive ? 'var(--surface)' : 'transparent',
                          border: isActive ? '1px solid var(--line)' : '1px solid transparent',
                          color: isActive ? 'var(--text)' : 'var(--text-2)',
                          fontSize: 13, fontWeight: 500,
                        }}
                      >
                        <span className="arc-mono" style={{ fontSize: 10.5, color: isActive ? 'var(--accent)' : 'var(--text-3)' }}>{n}</span>
                        <span className="truncate flex-1">{vocabulary.get(item.label || item.name)}</span>
                        {isActive && <ChevronRight size={13} className="text-[var(--text-3)]" />}
                      </button>
                      <span className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <DragHandle />
                      </span>
                    </div>
                  )
                }}
              />
            )}
          </div>
        </aside>
      )}
    </div>
    </>
  )
}

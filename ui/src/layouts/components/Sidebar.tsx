// claude-opus-4-7
// ARC sidebar: 56px icon rail (apps) + 200px section panel (active app submenu).
// Section panel items are user-reorderable via DnD (persisted in uiStore.submenuOrder).
// Clicking an app navigates directly to its first submenu item (skips AppHome).
import { useState, useEffect, useMemo } from 'react'
import { Bell, ChevronRight, Hexagon, Menu, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
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
  const [activeApp, setActiveApp] = useState<SidebarApp | null>(null)
  const [menuData, setMenuData] = useState<any>(null)
  const [isLoadingMenu, setIsLoadingMenu] = useState(false)

  const apps = sidebarData.filter(isVisibleMenuItem)
  const initial = (user?.full_name || user?.username || 'A')[0].toUpperCase()

  useEffect(() => {
    const [appName] = currentPath.split('/').filter(Boolean)
    if (appName) {
      const app = apps.find((a) => a.name === appName)
      if (app && app.name !== activeApp?.name) setActiveApp(app)
    }
  }, [currentPath, apps, activeApp?.name])

  useEffect(() => {
    if (!activeApp) { setMenuData(null); return }
    setIsLoadingMenu(true)
    api.get(`/app-menu/${activeApp.name}`)
      .then((res) => setMenuData(res.data))
      .catch(() => setMenuData(null))
      .finally(() => setIsLoadingMenu(false))
  }, [activeApp])

  // Flatten menu groups into a single ordered list (id = path) for DnD.
  const flatItems = useMemo<FlatMenuItem[]>(() => {
    if (!menuData) return []
    const groups = filterMenuElements(menuData.menu || []).filter((g: any) => {
      const label = (g.label || '').toLowerCase()
      const name = (g.name || '').toLowerCase()
      return !label.includes('setting') && !name.includes('setting') && !label.includes('admin') && !name.includes('admin')
    })
    const items: FlatMenuItem[] = []
    groups.forEach((g: any) => {
      filterMenuItems(g.items || []).forEach((i: MenuItem) => {
        const il = (i.label || '').toLowerCase()
        const inm = (i.name || '').toLowerCase()
        if (il.includes('setting') || inm.includes('setting') || il.includes('admin') || inm.includes('admin')) return
        items.push({ ...i, id: i.path || i.name, groupLabel: g.label })
      })
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

  // Auto-navigate to first item when app changes and current path is just /<app>.
  useEffect(() => {
    if (!activeApp || !orderedItems.length) return
    const segs = currentPath.split('/').filter(Boolean)
    if (segs.length <= 1 && segs[0] === activeApp.name) {
      navigate(orderedItems[0].path)
    }
  }, [activeApp, orderedItems, currentPath, navigate])

  const handleAppClick = (app: SidebarApp) => {
    setActiveApp(app)
    const saved = submenuOrder[app.name]
    const target = saved?.[0] || app.path || `/${app.name}`
    if (target === currentPath) {
      navigate(target, { replace: true, state: { _t: Date.now() } })
    } else {
      navigate(target)
    }
  }

  // Auto-close mobile drawer on route change.
  useEffect(() => {
    if (mobileSidebarOpen) setMobileSidebarOpen(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPath])

  const handleReorder = (next: FlatMenuItem[]) => {
    if (!activeApp) return
    setSubmenuOrder(activeApp.name, next.map((it) => it.id))
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
      {/* 56px icon rail */}
      <aside
        className="flex flex-col shrink-0 z-40"
        style={{
          width: iconRailCollapsed ? 0 : 56,
          background: 'var(--bg-2)',
          borderRight: iconRailCollapsed ? 'none' : '1px solid var(--line)',
          overflow: iconRailCollapsed ? 'hidden' : undefined,
        }}
      >
        <div
          className="flex items-center justify-center"
          style={{ height: 52, borderBottom: '1px solid var(--line)' }}
        >
          <Hexagon size={20} className="text-[var(--accent)]" />
        </div>

        <div className="flex-1 flex flex-col items-center gap-1 py-3 overflow-y-auto arc-scroll">
          {apps.map((item) => {
            const Icon = resolveIcon(item.icon)
            const isActive = activeApp?.name === item.name
            return (
              <button
                key={item.name}
                onClick={() => handleAppClick(item)}
                title={vocabulary.get(item.label)}
                className="relative flex items-center justify-center transition-colors"
                style={{
                  width: 38, height: 38, borderRadius: 'var(--radius)',
                  background: isActive ? 'var(--surface-2)' : 'transparent',
                  border: isActive ? '1px solid var(--line)' : '1px solid transparent',
                  color: isActive ? 'var(--text)' : 'var(--text-3)',
                }}
              >
                <Icon size={17} />
                {isActive && (
                  <span style={{
                    position: 'absolute', left: -8, top: 8, bottom: 8, width: 2,
                    background: 'var(--accent)', borderRadius: 2,
                  }} />
                )}
              </button>
            )
          })}
        </div>

        <div className="flex flex-col items-center gap-2 py-3" style={{ borderTop: '1px solid var(--line)' }}>
          <button
            onClick={toggleIconRail}
            aria-label="Hide sidebar"
            className="flex items-center justify-center hover:text-[var(--text)] text-[var(--text-3)] transition-colors"
            style={{ width: 32, height: 32, borderRadius: 8 }}
          >
            <Menu size={16} />
          </button>
          <button
            onClick={toggleSidebar}
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="flex items-center justify-center hover:text-[var(--text)] text-[var(--text-3)] transition-colors"
            style={{ width: 32, height: 32, borderRadius: 8 }}
          >
            {sidebarCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
          </button>
          <Bell size={17} className="text-[var(--text-3)]" />
          <div className="arc-av" style={{
            width: 28, height: 28,
            background: 'color-mix(in oklch, var(--accent) 22%, var(--surface))',
            color: 'var(--accent)',
            boxShadow: '0 0 0 1.5px var(--accent), 0 0 0 3px var(--bg)',
          }}>
            <span className="arc-mono">{initial}</span>
          </div>
        </div>
      </aside>

      {/* 200px Section panel — hidden on phones unless drawer open */}
      {activeApp && !sidebarCollapsed && !iconRailCollapsed && (
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
                  const isActive = currentPath === item.path || currentPath.startsWith(`${item.path}/`)
                  const n = String(orderedItems.findIndex((i) => i.id === item.id) + 1).padStart(2, '0')
                  return (
                    <button
                      onClick={() => navigate(item.path)}
                      className="group w-full flex items-center gap-2 text-left transition-colors relative"
                      style={{
                        padding: '8px 10px', borderRadius: 'var(--radius)',
                        background: isActive ? 'var(--surface)' : 'transparent',
                        border: isActive ? '1px solid var(--line)' : '1px solid transparent',
                        color: isActive ? 'var(--text)' : 'var(--text-2)',
                        fontSize: 13, fontWeight: 500,
                      }}
                    >
                      <span className="arc-mono" style={{ fontSize: 10.5, color: isActive ? 'var(--accent)' : 'var(--text-3)' }}>{n}</span>
                      <span className="truncate flex-1">{vocabulary.get(item.label || item.name)}</span>
                      {isActive && <ChevronRight size={13} className="text-[var(--text-3)]" />}
                      <span className="opacity-0 group-hover:opacity-100 transition-opacity">
                        <DragHandle />
                      </span>
                    </button>
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

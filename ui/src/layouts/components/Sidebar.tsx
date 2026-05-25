// claude-opus-4-7
// ARC sidebar: single ARC card with brand at top, app list, optional submenu, profile/logout at bottom.
// Collapsed mode shows just icons. Active state uses coral accent.
import { useState, useEffect } from 'react'
import { LogOut, Hexagon, ChevronRight } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import type { SidebarApp, MenuItem } from '../types'
import { useVocabulary } from '../../context/VocabularyContext'
import { resolveIcon } from '../../lib/iconUtils'
import { isVisibleMenuItem, filterMenuItems, filterMenuElements } from '../../lib/menuUtils'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'
import api from '../../lib/api'

interface SidebarProps {
  sidebarData: SidebarApp[]
  currentPath: string
  onLogout: () => void
}

export function Sidebar({ sidebarData, currentPath, onLogout }: SidebarProps) {
  const vocabulary = useVocabulary()
  const location = useLocation()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const { sidebarCollapsed, toggleSidebar } = useUIStore()
  const [activeApp, setActiveApp] = useState<SidebarApp | null>(null)
  const [menuData, setMenuData] = useState<any>(null)
  const [panelOpen, setPanelOpen] = useState(true)
  const [isLoadingMenu, setIsLoadingMenu] = useState(false)

  const apps = sidebarData.filter(isVisibleMenuItem)

  useEffect(() => {
    const [appName] = location.pathname.split('/').filter(Boolean)
    if (appName) {
      const app = apps.find((a) => a.name === appName)
      if (app) setActiveApp(app)
    }
  }, [location.pathname, apps])

  useEffect(() => {
    if (!activeApp) return
    setIsLoadingMenu(true)
    api.get(`/app-menu/${activeApp.name}`)
      .then((res) => setMenuData(res.data))
      .catch(() => setMenuData(null))
      .finally(() => setIsLoadingMenu(false))
  }, [activeApp])

  const handleAppClick = (app: SidebarApp) => {
    setActiveApp(app)
    if (!panelOpen) setPanelOpen(true)
    navigate(app.path || `/${app.name}`)
  }

  const groups = menuData
    ? filterMenuElements(menuData.menu || [])
        .filter((g: any) => {
          const label = (g.label || '').toLowerCase()
          const name = (g.name || '').toLowerCase()
          return !label.includes('setting') && !name.includes('setting') && !label.includes('admin') && !name.includes('admin')
        })
        .map((g: any) => ({
          ...g,
          items: (g.items || []).filter((i: any) => {
            const il = (i.label || '').toLowerCase()
            const inm = (i.name || '').toLowerCase()
            return !il.includes('setting') && !inm.includes('setting') && !il.includes('admin') && !inm.includes('admin')
          }),
        }))
        .filter((g: any) => g.items.length > 0 || g.type !== 'group')
    : []

  const initial = (user?.full_name || user?.username || 'A')[0].toUpperCase()

  return (
    <div className="flex h-full gap-2 transition-all duration-200">
      {/* App rail */}
      <aside className={`flex flex-col shrink-0 z-40 arc-card overflow-hidden transition-[width] duration-200 ${sidebarCollapsed ? 'w-[58px]' : 'w-[208px]'}`}>
        {/* Brand */}
        <div className={`h-[52px] min-h-[52px] shrink-0 flex items-center border-b border-[var(--line)] ${sidebarCollapsed ? 'justify-center' : 'px-3 justify-between'}`}>
          <button
            onClick={toggleSidebar}
            aria-label="Toggle sidebar"
            className={`flex items-center group gap-2 ${sidebarCollapsed ? 'w-9 h-9 justify-center rounded-[var(--radius)] hover:bg-[var(--surface-2)]' : 'w-full h-9 px-2 rounded-[var(--radius)] hover:bg-[var(--surface-2)]'}`}
          >
            <Hexagon size={18} className="text-[var(--accent)] group-hover:rotate-180 transition-transform duration-500" />
            {!sidebarCollapsed && <span className="text-[14px] font-semibold tracking-tight text-[var(--text)]">Aras</span>}
            {!sidebarCollapsed && <span className="arc-id arc-dim2 ml-auto">v1.2</span>}
          </button>
        </div>

        {/* App list */}
        <div className={`flex flex-col gap-0.5 w-full overflow-y-auto arc-scroll flex-1 ${sidebarCollapsed ? 'p-2' : 'p-2'}`}>
          {apps.map((item) => {
            const Icon = resolveIcon(item.icon)
            const isActive = activeApp?.name === item.name
            const label = vocabulary.get(item.label)
            return (
              <button
                key={item.name}
                onClick={() => handleAppClick(item)}
                title={sidebarCollapsed ? label : undefined}
                className={`flex items-center transition-colors relative group shrink-0 rounded-[var(--radius)] ${
                  sidebarCollapsed ? 'w-9 h-9 justify-center mx-auto' : 'w-full px-2.5 h-9 gap-2.5'
                } ${
                  isActive
                    ? 'bg-[color-mix(in_oklch,var(--accent)_14%,var(--surface))] text-[var(--accent)]'
                    : 'text-[var(--text-2)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]'
                }`}
              >
                <Icon size={15} strokeWidth={isActive ? 2.2 : 1.8} className="shrink-0" />
                {!sidebarCollapsed && <span className="text-[12.5px] font-medium truncate">{label}</span>}
                {isActive && !sidebarCollapsed && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />}
              </button>
            )
          })}
        </div>

        {/* User / logout */}
        <div className={`shrink-0 border-t border-[var(--line)] flex items-center ${sidebarCollapsed ? 'flex-col gap-2 py-3 justify-center' : 'gap-2 p-2.5'}`}>
          {sidebarCollapsed ? (
            <>
              <div className="arc-av" style={{ background: 'color-mix(in oklch, var(--accent) 16%, var(--surface))', color: 'var(--accent)', borderColor: 'var(--line)' }}>
                <span className="arc-mono">{initial}</span>
              </div>
              <button onClick={onLogout} aria-label="Logout" className="arc-btn ghost" style={{ height: 28, width: 28, padding: 0, justifyContent: 'center' }}>
                <LogOut size={13} />
              </button>
            </>
          ) : (
            <>
              <div className="arc-av" style={{ background: 'color-mix(in oklch, var(--accent) 16%, var(--surface))', color: 'var(--accent)', borderColor: 'var(--line)' }}>
                <span className="arc-mono">{initial}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[12px] font-medium text-[var(--text)] truncate">{user?.full_name || 'Admin'}</div>
                <div className="arc-id arc-dim2 truncate">{user?.username || '—'}</div>
              </div>
              <button onClick={onLogout} aria-label="Logout" className="arc-btn ghost" style={{ height: 28, width: 28, padding: 0, justifyContent: 'center' }}>
                <LogOut size={13} />
              </button>
            </>
          )}
        </div>
      </aside>

      {/* Submenu panel */}
      {activeApp && panelOpen && (
        <aside className="w-[212px] flex flex-col shrink-0 z-30 arc-card overflow-hidden">
          <div className="h-[52px] min-h-[52px] shrink-0 px-3 border-b border-[var(--line)] flex items-center justify-between">
            <div className="min-w-0">
              <div className="arc-id"><b>app</b>/{activeApp.name}</div>
              <div className="text-[13px] font-medium text-[var(--text)] truncate">{vocabulary.get(activeApp.label)}</div>
            </div>
            <button onClick={() => setPanelOpen(false)} aria-label="Collapse panel" className="arc-btn ghost" style={{ height: 24, width: 24, padding: 0, justifyContent: 'center' }}>
              <ChevronRight className="rotate-180" size={13} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto arc-scroll p-2 flex flex-col gap-3">
            {isLoadingMenu ? (
              <div className="py-6 text-center">
                <div className="arc-id arc-dim2">loading…</div>
              </div>
            ) : groups.length > 0 ? (
              groups.map((group: any) => (
                <div key={group.label} className="flex flex-col gap-0.5">
                  <div className="px-2 pb-1">
                    <span className="arc-id arc-dim2">{vocabulary.get(group.label).toLowerCase().replace(/\s+/g, '-')}</span>
                  </div>
                  {filterMenuItems(group.items || []).map((item: MenuItem) => {
                    const ItemIcon = resolveIcon(item.icon || 'FileText')
                    const isActive = currentPath === item.path || currentPath.startsWith(`${item.path}/`)
                    return (
                      <Link
                        key={item.name}
                        to={item.path}
                        className={`flex items-center gap-2 px-2.5 h-8 rounded-[var(--radius)] transition-colors ${
                          isActive
                            ? 'bg-[color-mix(in_oklch,var(--accent)_12%,var(--surface))] text-[var(--accent)]'
                            : 'text-[var(--text-2)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]'
                        }`}
                      >
                        <ItemIcon size={13} strokeWidth={isActive ? 2.2 : 1.8} className="shrink-0" />
                        <span className="text-[12.5px] truncate">{vocabulary.get(item.label || item.name)}</span>
                      </Link>
                    )
                  })}
                </div>
              ))
            ) : (
              <div className="py-6 text-center flex flex-col items-center gap-2">
                <span className="arc-id arc-dim2">empty</span>
                <p className="arc-dim text-[12px]">No sub-modules.</p>
                <Link to={`/${activeApp.name}`} className="arc-btn sm">Open app home</Link>
              </div>
            )}
          </div>
        </aside>
      )}
    </div>
  )
}

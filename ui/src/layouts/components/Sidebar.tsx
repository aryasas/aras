import { useEffect, useMemo } from 'react'
import { CreditCard, HelpCircle, Hexagon, Menu, PanelLeftClose, PanelLeftOpen, Settings } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { SidebarApp } from '../types'
import { useVocabulary } from '../../context/VocabularyContext'
import { resolveIcon } from '../../lib/iconUtils'
import { isVisibleMenuItem } from '../../lib/menuUtils'
import { appRoutePath, firstPathFromMenuData, isRouteMatch, normalizeRoutePath } from '../../lib/navUtils'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'
import api from '../../lib/api'
import { useAppMenu } from '../hooks/useAppMenu'

interface SidebarProps {
  sidebarData: SidebarApp[]
  currentPath: string
}

const getArasRole = () => {
  const injectedRole = (globalThis as any).__ARAS_ROLE__
  return String(injectedRole || import.meta.env.VITE_ARAS_ROLE || 'tenant')
}

export function Sidebar({ sidebarData, currentPath }: SidebarProps) {
  const vocabulary = useVocabulary()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const submenuOrder = useUIStore((state) => state.submenuOrder)
  const sidebarCollapsed = useUIStore((state) => state.sidebarCollapsed)
  const toggleSidebar = useUIStore((state) => state.toggleSidebar)
  const iconRailCollapsed = useUIStore((state) => state.iconRailCollapsed)
  const toggleIconRail = useUIStore((state) => state.toggleIconRail)
  const mobileSidebarOpen = useUIStore((state) => state.mobileSidebarOpen)
  const setMobileSidebarOpen = useUIStore((state) => state.setMobileSidebarOpen)
  const isControlPanel = getArasRole() === 'control-panel'

  const apps = useMemo(() => sidebarData.filter((item) => (
    isVisibleMenuItem(item) &&
    !item.hide_from_sidebar &&
    item.name !== 'settings' &&
    item.name !== 'help'
  )), [sidebarData])
  const { activeApp, menuData, orderedItems } = useAppMenu(apps, currentPath)
  const initial = (user?.full_name || user?.username || 'A')[0].toUpperCase()

  useEffect(() => {
    if (mobileSidebarOpen) setMobileSidebarOpen(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPath])

  const handleAppClick = async (item: SidebarApp) => {
    const appRoot = appRoutePath(item)
    if (item.name === 'settings' || item.path === '/settings') {
      navigate(appRoot)
      return
    }
    if (item.type === 'link' || item.have_home) {
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
      const data = item.name === activeApp?.name ? menuData : (await api.get(`/app-menu/${menuPath}`)).data
      navigate(firstPathFromMenuData(data) || appRoot)
    } catch {
      navigate(appRoot)
    }
  }

  return (
    <>
      {mobileSidebarOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/40"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}
      <div
        className={`flex h-full max-md:fixed max-md:inset-y-0 max-md:left-0 max-md:z-50 max-md:shadow-xl max-md:transition-transform max-md:duration-200 ${mobileSidebarOpen ? 'max-md:translate-x-0' : 'max-md:-translate-x-full'}`}
      >
        <aside
          className="flex flex-col shrink-0 z-40 transition-[width] duration-300"
          style={{
            width: iconRailCollapsed ? 0 : (sidebarCollapsed ? 62 : 242),
            background: 'var(--bg-2)',
            borderRight: iconRailCollapsed ? 'none' : '1px solid var(--line)',
            overflow: iconRailCollapsed ? 'hidden' : undefined,
          }}
        >
          <div
            className="flex items-center px-4"
            style={{
              height: 57,
              borderBottom: '1px solid var(--line)',
              justifyContent: sidebarCollapsed ? 'center' : 'space-between',
              padding: sidebarCollapsed ? '0' : '0 12px',
            }}
          >
            <div className="flex items-center" style={{ minWidth: 0 }}>
              <Hexagon size={22} className="text-[var(--accent)] shrink-0" />
              {!sidebarCollapsed && !iconRailCollapsed ? (
                <span className="ml-2.5 font-bold text-sm truncate uppercase tracking-wider text-[var(--text)]">
                  Aras
                </span>
              ) : null}
            </div>
            {!sidebarCollapsed ? (
              <div className="flex items-center gap-0.5">
                <button
                  onClick={toggleIconRail}
                  title="Hide Rail"
                  className="p-1.5 hover:bg-[var(--surface-2)] rounded-md text-[var(--text-3)] hover:text-[var(--text)] transition-colors"
                >
                  <Menu size={18} />
                </button>
                <button
                  onClick={toggleSidebar}
                  title="Collapse"
                  className="p-1.5 hover:bg-[var(--surface-2)] rounded-md text-[var(--text-3)] hover:text-[var(--text)] transition-colors"
                >
                  <PanelLeftClose size={18} />
                </button>
              </div>
            ) : null}
          </div>

          <div className="flex-1 flex flex-col gap-1 py-3 overflow-y-auto arc-scroll px-2">
            {user?.is_admin && isControlPanel ? (
              <button
                type="button"
                title={sidebarCollapsed ? 'Control Panel' : undefined}
                onClick={() => navigate('/control-panel')}
                className="group relative flex items-center transition-all duration-200"
                style={{
                  width: '100%',
                  height: 42,
                  padding: sidebarCollapsed ? '0' : '0 10px',
                  justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                  borderRadius: 'var(--radius)',
                  background: isRouteMatch(currentPath, '/control-panel') ? 'var(--surface-2)' : 'transparent',
                  border: isRouteMatch(currentPath, '/control-panel') ? '1px solid var(--line)' : '1px solid transparent',
                  color: isRouteMatch(currentPath, '/control-panel') ? 'var(--text)' : 'var(--text-3)',
                }}
              >
                <CreditCard size={19} className="shrink-0" />
                {!sidebarCollapsed ? (
                  <span className="ml-3 text-[13px] font-medium truncate opacity-90 group-hover:opacity-100">
                    Control Panel
                  </span>
                ) : null}
                {isRouteMatch(currentPath, '/control-panel') ? (
                  <span style={{
                    position: 'absolute', left: -2, top: 8, bottom: 8, width: 2,
                    background: 'var(--accent)', borderRadius: 2,
                  }} />
                ) : null}
              </button>
            ) : null}

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
                  onClick={() => void handleAppClick(item)}
                  className="group relative flex items-center transition-all duration-200"
                  style={{
                    width: '100%',
                    height: 42,
                    padding: sidebarCollapsed ? '0' : '0 10px',
                    justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                    borderRadius: 'var(--radius)',
                    background: isActive ? 'var(--surface-2)' : 'transparent',
                    border: isActive ? '1px solid var(--line)' : '1px solid transparent',
                    color: isActive ? 'var(--text)' : 'var(--text-3)',
                  }}
                >
                  <Icon size={19} className="shrink-0" />
                  {!sidebarCollapsed ? (
                    <span className="ml-3 text-[13px] font-medium truncate opacity-90 group-hover:opacity-100">
                      {label}
                    </span>
                  ) : null}
                  {isActive ? (
                    <span style={{
                      position: 'absolute', left: -2, top: 8, bottom: 8, width: 2,
                      background: 'var(--accent)', borderRadius: 2,
                    }} />
                  ) : null}
                </button>
              )
            })}
          </div>

          <div className="flex flex-col gap-2 py-3 px-2" style={{ borderTop: '1px solid var(--line)' }}>
            {sidebarCollapsed ? (
              <button
                onClick={toggleSidebar}
                title="Expand"
                className="flex items-center justify-center hover:text-[var(--text)] text-[var(--text-3)] transition-colors mb-2"
                style={{ width: '100%', height: 35, borderRadius: 8 }}
              >
                <PanelLeftOpen size={18} />
              </button>
            ) : null}
            <button
              onClick={() => navigate('/admin/settings')}
              title="Settings"
              className="flex items-center hover:text-[var(--text)] text-[var(--text-3)] transition-colors"
              style={{
                width: '100%',
                height: 35,
                borderRadius: 8,
                justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                padding: sidebarCollapsed ? '0' : '0 10px',
              }}
            >
              <Settings size={18} className="shrink-0" />
              {!sidebarCollapsed ? <span className="ml-3 text-xs font-medium">Settings</span> : null}
            </button>
            <button
              onClick={() => navigate('/help')}
              title="Help"
              className="flex items-center hover:text-[var(--text)] text-[var(--text-3)] transition-colors"
              style={{
                width: '100%',
                height: 35,
                borderRadius: 8,
                justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                padding: sidebarCollapsed ? '0' : '0 10px',
              }}
            >
              <HelpCircle size={18} className="shrink-0" />
              {!sidebarCollapsed ? <span className="ml-3 text-xs font-medium">Help</span> : null}
            </button>
            <div
              className="flex items-center"
              style={{
                width: '100%',
                justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                padding: sidebarCollapsed ? '0' : '0 10px',
                marginTop: 4,
              }}
            >
              <div className="arc-av shrink-0" style={{
                width: 31, height: 31,
                background: 'color-mix(in oklch, var(--accent) 22%, var(--surface))',
                color: 'var(--accent)',
                boxShadow: '0 0 0 1.5px var(--accent), 0 0 0 3px var(--bg)',
              }}>
                <span className="arc-mono">{initial}</span>
              </div>
              {!sidebarCollapsed ? (
                <div className="ml-3 min-w-0">
                  <div className="text-[11px] font-bold truncate text-[var(--text)]">{user?.full_name || user?.username}</div>
                  <div className="text-[9px] text-[var(--text-3)] truncate uppercase tracking-tighter">Administrator</div>
                </div>
              ) : null}
            </div>
          </div>
        </aside>
      </div>
    </>
  )
}

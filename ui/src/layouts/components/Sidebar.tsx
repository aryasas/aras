import React, { useState, useEffect } from 'react'
import { LogOut, Hexagon, User, ChevronRight, Pin, PinOff } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import type { SidebarApp, MenuItem, MenuElement } from '../types'
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
  const [isPanelPinned, setIsPanelPinned] = useState(true)
  const [isLoadingMenu, setIsLoadingMenu] = useState(false)

  const normalizedSidebarData = sidebarData.filter(isVisibleMenuItem)

  // Find app name from path to set initial active app
  useEffect(() => {
    const [appName] = location.pathname.split('/').filter(Boolean)
    if (appName) {
      const app = normalizedSidebarData.find(a => a.name === appName)
      if (app) setActiveApp(app)
    }
  }, [location.pathname, normalizedSidebarData])

  // Fetch sub-menu when active app changes
  useEffect(() => {
    if (!activeApp) return
    setIsLoadingMenu(true)
    api.get(`/app-menu/${activeApp.name}`)
      .then(res => setMenuData(res.data))
      .catch(() => setMenuData(null))
      .finally(() => setIsLoadingMenu(false))
  }, [activeApp])

  const handleAppClick = (app: SidebarApp) => {
    setActiveApp(app)
    if (!isPanelPinned) setIsPanelPinned(true)
    navigate(app.path || `/${app.name}`)
  }

  const menuGroups = menuData ? filterMenuElements(menuData.menu || []).filter(
    (g: any) => {
      const label = (g.label || '').toLowerCase()
      const name = (g.name || '').toLowerCase()
      const isSettings = label.includes('setting') || name.includes('setting')
      const isAdmin = label.includes('admin') || name.includes('admin')
      return !isSettings && !isAdmin
    }
  ).map((g: any) => ({
    ...g,
    items: (g.items || []).filter((i: any) => {
      const iLabel = (i.label || '').toLowerCase()
      const iName = (i.name || '').toLowerCase()
      const iIsSettings = iLabel.includes('setting') || iName.includes('setting')
      const iIsAdmin = iLabel.includes('admin') || iName.includes('admin')
      return !iIsSettings && !iIsAdmin
    })
  })).filter((g: any) => g.items.length > 0 || g.type !== 'group') : []

  return (
    <div className="flex h-full gap-3 transition-all duration-300">
      {/* Stage 1: Global App Switcher */}
      <aside className={`flex flex-col shrink-0 z-40 bg-[var(--app-panel)] border border-[var(--app-border)] rounded-[var(--app-radius-lg)] overflow-hidden transition-all duration-300 ease-in-out shadow-sm ${sidebarCollapsed ? 'w-[4.5rem] py-5 items-center' : 'w-60 items-stretch'}`}>
        <div className={`flex flex-col w-full flex-1 overflow-hidden ${sidebarCollapsed ? 'items-center gap-6' : ''}`}>
          
          <div className={`h-[64px] min-h-[64px] max-h-[64px] shrink-0 border-b border-[var(--app-border)] bg-[var(--app-panel)] flex items-center box-border ${sidebarCollapsed ? 'justify-center border-none' : 'px-6 justify-between'}`}>
            <button 
              onClick={toggleSidebar}
              className={`flex items-center justify-center text-[var(--app-primary-action)] hover:opacity-80 group shrink-0 transition-all rounded-xl bg-[var(--app-panel-soft)] border border-[var(--app-border)] ${sidebarCollapsed ? 'w-10 h-10' : 'w-full h-11 px-3 gap-3 justify-start'}`}
            >
              <Hexagon className="w-6 h-6 group-hover:rotate-180 transition-transform duration-500" />
              {!sidebarCollapsed && <span className="text-lg font-black tracking-tight text-[var(--app-text)]">Aras</span>}
            </button>
          </div>
          
          <div className={`flex flex-col gap-1 w-full overflow-y-auto hide-scroll ${sidebarCollapsed ? 'px-2' : 'p-3'}`}>
            {normalizedSidebarData.map((item) => {
              const Icon = resolveIcon(item.icon)
              const isActive = activeApp?.name === item.name
              const label = vocabulary.get(item.label)

              return (
                <button
                  key={item.name}
                  onClick={() => handleAppClick(item)}
                  className={`flex items-center transition-all relative group shrink-0 ${
                    sidebarCollapsed 
                      ? 'w-12 h-12 justify-center rounded-xl mx-auto' 
                      : 'w-full px-3 py-2 gap-3 rounded-xl'
                  } ${
                    isActive 
                      ? 'bg-[var(--app-primary-action)] text-white shadow-lg shadow-[var(--app-accent-glow)]' 
                      : 'text-[var(--app-muted)] hover:bg-[var(--app-panel-soft)] hover:text-[var(--app-text)]'
                  }`}
                  title={sidebarCollapsed ? label : ''}
                >
                  <Icon size={20} strokeWidth={isActive ? 2.5 : 2.2} className="shrink-0" />
                  {!sidebarCollapsed && (
                    <span className={`text-[13px] font-normal truncate ${isActive ? 'text-white' : ''}`}>
                      {label}
                    </span>
                  )}
                  {isActive && sidebarCollapsed && (
                    <div className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-white rounded-r-full" />
                  )}
                </button>
              )
            })}
          </div>
        </div>

        <div className={`flex flex-col gap-4 w-full shrink-0 mt-4 pt-4 border-t border-[var(--app-border)] ${sidebarCollapsed ? 'pb-5 items-center' : 'p-4 bg-[var(--app-panel-soft)]/50'}`}>
          {sidebarCollapsed ? (
            <button
              onClick={onLogout}
              className="w-10 h-10 flex items-center justify-center rounded-full bg-[var(--app-panel-soft)] hover:bg-rose-50 text-[var(--app-muted)] hover:text-rose-500 transition-all border border-[var(--app-border)]"
              title="Logout"
            >
              <User size={18} strokeWidth={2.5} />
            </button>
          ) : (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[var(--app-primary-action)] text-white text-[10px] font-medium flex items-center justify-center shrink-0">
                {user?.full_name?.[0] || 'A'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[12px] font-semibold text-[var(--app-text)] truncate">{user?.full_name || 'Admin'}</p>
              </div>
              <button
                onClick={onLogout}
                className="p-1.5 rounded-lg text-[var(--app-muted)] hover:text-rose-500 hover:bg-white transition-all shrink-0"
              >
                <LogOut size={16} />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Stage 2: App-Specific Sub Menu Panel */}
      {activeApp && isPanelPinned && (
        <aside className="w-60 flex flex-col shrink-0 z-30 bg-[var(--app-panel)] border border-[var(--app-border)] rounded-[var(--app-radius-lg)] overflow-hidden shadow-sm">
          <div className="h-[64px] min-h-[64px] max-h-[64px] shrink-0 px-6 border-b border-[var(--app-border)] bg-[var(--app-panel)] flex items-center justify-between box-border">
            <div className="flex flex-col min-w-0">
              <span className="text-[10px] font-black uppercase tracking-widest text-[var(--app-muted)] opacity-70">Application</span>
              <h2 className="text-[14px] font-semibold text-[var(--app-text)] truncate">{vocabulary.get(activeApp.label)}</h2>
            </div>
            <button 
              onClick={() => setIsPanelPinned(false)}
              className="p-1.5 text-[var(--app-muted)] hover:text-[var(--app-text)] hover:bg-white rounded-lg transition-all"
            >
              <ChevronRight className="rotate-180" size={16} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto hide-scroll p-3 space-y-6">
            {isLoadingMenu ? (
              <div className="py-10 text-center animate-pulse space-y-2">
                <div className="h-4 w-2/3 bg-[var(--app-panel-soft)] rounded mx-auto" />
                <div className="h-3 w-1/2 bg-[var(--app-panel-soft)] rounded mx-auto opacity-50" />
              </div>
            ) : menuGroups.length > 0 ? (
              menuGroups.map((group: any) => (
                <div key={group.label} className="space-y-1">
                  <div className="px-3 mb-2 flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--app-muted)] opacity-60">
                      {vocabulary.get(group.label)}
                    </span>
                  </div>
                  <div className="space-y-0.5">
                    {filterMenuItems(group.items || []).map((item: MenuItem) => {
                      const ItemIcon = resolveIcon(item.icon || 'FileText')
                      const isActive = currentPath === item.path || currentPath.startsWith(`${item.path}/`)
                      return (
                        <Link
                          key={item.name}
                          to={item.path}
                          className={`flex items-center gap-3 px-3 py-2 rounded-xl transition-all group ${
                            isActive 
                              ? 'bg-[var(--app-primary-action)]/10 text-[var(--app-primary-action)] font-medium' 
                              : 'text-[var(--app-muted)] hover:bg-[var(--app-panel-soft)] hover:text-[var(--app-text)] font-normal'
                          }`}
                        >
                          <ItemIcon size={16} strokeWidth={isActive ? 2.5 : 2} className="shrink-0" />
                          <span className="text-[13px] truncate">{vocabulary.get(item.label || item.name)}</span>
                        </Link>
                      )
                    })}
                  </div>
                </div>
              ))
            ) : (
              <div className="py-10 text-center flex flex-col items-center gap-2">
                <resolveIcon icon="Layout" size={24} className="text-[var(--app-muted)] opacity-20" />
                <p className="text-[11px] font-bold text-[var(--app-muted)]">No sub-modules found</p>
                <Link to={`/${activeApp.name}`} className="text-[11px] text-[var(--app-primary-action)] font-black uppercase hover:underline mt-2">Open App Home</Link>
              </div>
            )}
          </div>
        </aside>
      )}
    </div>
  )
}


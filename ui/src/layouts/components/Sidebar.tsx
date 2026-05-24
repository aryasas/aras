import React from 'react'
import { LogOut, PanelLeftClose, Hexagon, User } from 'lucide-react'
import { Link } from 'react-router-dom'
import { SidebarNavItem } from './SidebarNavItem'
import type { SidebarApp } from '../types'
import { useVocabulary } from '../../context/VocabularyContext'
import { resolveIcon } from '../../lib/iconUtils'
import { isVisibleMenuItem } from '../../lib/menuUtils'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'

interface SidebarProps {
  sidebarData: SidebarApp[]
  currentPath: string
  onLogout: () => void
}

// Maps sidebar item names to section labels for grouping
const SIDEBAR_SECTIONS: { label: string; names: string[] }[] = [
  { label: 'Workspace', names: ['dashboard', 'pos', 'reports'] },
  { label: 'Operations', names: ['erp', 'stock', 'accounting', 'crm', 'purchasing', 'sales', 'manufacturing', 'hr', 'payroll', 'project', 'helpdesk'] },
  { label: 'System', names: ['settings', 'help', 'admin'] },
]

export function Sidebar({ sidebarData, currentPath, onLogout }: SidebarProps) {
  const vocabulary = useVocabulary()
  const { sidebarCollapsed, toggleSidebar } = useUIStore()
  const { user } = useAuthStore()
  
  const normalizedSidebarData = sidebarData
    .filter(isVisibleMenuItem)
    .map((item) => ({
      ...item,
      label: vocabulary.get(item.label),
      sub_apps: item.sub_apps
        ?.filter(isVisibleMenuItem)
        .map((sub) => ({ ...sub, label: vocabulary.get(sub.label) })),
    }))

  const renderItem = (item: SidebarApp, depth = 0) => {
    const type = item.type || 'app'
    const IconComponent = resolveIcon(item.icon)
    const isSubApp = depth > 0

    if (type === 'link') {
      return (
        <SidebarNavItem 
          key={item.name} 
          to={item.path!} 
          icon={<IconComponent size={20} />} 
          label={item.label} 
          active={currentPath === item.path} 
          isOpen={false}
          collapsed={sidebarCollapsed}
        />
      )
    }

    if (type === 'app') {
      const appPath = item.path || `/${item.name}`
      const isSubAppActive = item.sub_apps?.some(sub => {
        const subPath = sub.path || `/${sub.name}`
        return currentPath === subPath || currentPath.startsWith(`${subPath}/`)
      })
      const isActive = currentPath === appPath || currentPath.startsWith(`${appPath}/`) || isSubAppActive
      
      return (
        <div key={`container-${item.name}`}>
          <SidebarNavItem
            to={appPath}
            icon={<IconComponent size={isSubApp ? 16 : 20} />}
            label={item.label}
            active={isActive}
            isOpen={false}
            collapsed={sidebarCollapsed}
          />
        </div>
      )
    }
    return null
  }

  return (
    <>
      {/* Desktop Sidebar (Floating Island) */}
      <aside className={`hidden md:flex flex-col shrink-0 z-30 bg-[var(--aras-panel)]/90 backdrop-blur-[16px] border border-[var(--aras-border)] shadow-[0_18px_45px_-24px_rgba(15,23,42,0.34)] rounded-[var(--aras-radius-lg)] py-5 justify-between transition-[width,padding] duration-300 ease-in-out ${sidebarCollapsed ? 'w-[5.5rem] items-center px-0' : 'w-[15.5rem] items-stretch px-4'}`}>
        <div className={`flex min-h-0 flex-1 flex-col gap-4 w-full ${sidebarCollapsed ? 'items-center' : ''}`}>
          
          <button 
            onClick={toggleSidebar} 
            className={`flex items-center justify-center bg-[var(--aras-button)] text-[var(--aras-button-text)] hover:opacity-90 shadow-md group shrink-0 transition-all rounded-[1rem] ${sidebarCollapsed ? 'w-12 h-12 flex-col gap-1 mx-auto' : 'w-full h-[3.25rem] flex-row gap-3 px-3 justify-start'}`}
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed ? (
              <Hexagon className="w-6 h-6 group-hover:scale-110 transition-transform" />
            ) : (
              <>
                <PanelLeftClose className="w-5 h-5 group-hover:scale-110 transition-transform" />
                <span className="text-sm font-bold">Aras</span>
              </>
            )}
          </button>
          
          <div className="flex min-h-0 flex-1 flex-col gap-1 w-full overflow-y-auto hide-scroll pr-0.5">
            {(() => {
              const rendered: React.ReactNode[] = []
              let lastSection = ''
              normalizedSidebarData.forEach((item, index) => {
                const section = SIDEBAR_SECTIONS.find(s => s.names.includes(item.name))?.label || ''
                if (section && section !== lastSection && !sidebarCollapsed) {
                  rendered.push(
                    <div key={`section-${section}`} className="px-2 pt-3 pb-1 first:pt-0">
                      <span className="text-[9px] font-black uppercase tracking-[0.12em] text-[var(--aras-muted)] opacity-60">{section}</span>
                    </div>
                  )
                  lastSection = section
                }
                rendered.push(
                  <div key={`root-${item.name || index}`}>
                    {renderItem(item)}
                  </div>
                )
              })
              return rendered
            })()}
          </div>
        </div>

        <div className={`flex flex-col gap-2 w-full shrink-0 mt-4 pt-4 border-t border-[var(--aras-border)] ${sidebarCollapsed ? 'items-center' : ''}`}>
          {sidebarCollapsed ? (
            <button
              onClick={onLogout}
              className="w-10 h-10 flex items-center justify-center rounded-[0.875rem] bg-[var(--aras-panel-soft)] hover:bg-rose-50 text-[var(--aras-muted)] hover:text-rose-500 transition-all mx-auto"
              title={user?.full_name || 'Logout'}
            >
              {user?.full_name ? (
                <span className="text-xs font-black">{user.full_name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()}</span>
              ) : (
                <User size={16} />
              )}
            </button>
          ) : (
            <div className="flex items-center gap-2.5 px-2 py-2 rounded-[1rem] bg-[var(--aras-panel-soft)]">
              <div className="w-8 h-8 rounded-[0.625rem] bg-[var(--aras-button)] text-[var(--aras-button-text)] flex items-center justify-center shrink-0">
                <span className="text-xs font-black">
                  {user?.full_name ? user.full_name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() : 'AD'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold truncate text-[var(--aras-text)]">{user?.full_name || user?.username || '—'}</p>
                <p className="text-[10px] text-[var(--aras-muted)] truncate">{user?.is_admin ? 'System Admin' : 'User'}</p>
              </div>
              <button
                onClick={onLogout}
                className="p-1.5 rounded-lg text-[var(--aras-muted)] hover:text-rose-500 hover:bg-rose-50 transition-all shrink-0"
                title="Logout"
              >
                <LogOut size={14} />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Mobile Bottom Tab Navigation */}
      <nav className="md:hidden fixed bottom-[max(1rem,env(safe-area-inset-bottom))] left-4 right-4 bg-[var(--aras-panel)]/92 backdrop-blur-[16px] p-2 flex justify-around items-center z-50 shadow-[0_20px_40px_-18px_rgba(15,23,42,0.35)] border border-[var(--aras-border)] rounded-[var(--aras-radius-lg)]">
        {normalizedSidebarData.slice(0, 4).map((item) => {
          const appPath = item.path || `/${item.name}`
          const IconComponent = resolveIcon(item.icon)
          const isActive = currentPath === appPath || currentPath.startsWith(`${appPath}/`)
          return (
            <Link
              key={item.name}
              to={appPath}
              className={`w-14 h-14 flex flex-col items-center justify-center gap-1 rounded-[var(--aras-radius)] ${isActive ? 'text-[var(--aras-accent)]' : 'text-[var(--aras-muted)] hover:text-[var(--aras-text)]'}`}
              style={isActive ? { backgroundColor: 'color-mix(in srgb, var(--aras-accent) 10%, transparent)' } : undefined}
            >
              <IconComponent size={24} className="shrink-0" />
              <span className="text-[10px] font-bold truncate w-full text-center px-1">{item.label}</span>
            </Link>
          )
        })}
        <button 
          onClick={onLogout}
          className="w-14 h-14 flex flex-col items-center justify-center gap-1 text-[var(--aras-muted)] hover:text-rose-500 rounded-[var(--aras-radius)]"
        >
          <LogOut size={24} className="shrink-0" />
          <span className="text-[10px] font-bold">Exit</span>
        </button>
      </nav>
    </>
  )
}

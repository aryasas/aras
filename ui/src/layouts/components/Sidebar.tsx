import { LogOut, Menu } from 'lucide-react'
import * as LucideIcons from 'lucide-react'
import { SidebarNavItem } from './SidebarNavItem'
import { SidebarBrand } from './SidebarBrand'
import type { SidebarApp } from '../types'

interface SidebarProps {
  isOpen: boolean
  setOpen: (open: boolean) => void
  sidebarData: SidebarApp[]
  currentPath: string
  onLogout: () => void
}

export function Sidebar({ isOpen, setOpen, sidebarData, currentPath, onLogout }: SidebarProps) {
  const renderItem = (item: SidebarApp, depth = 0) => {
    const type = item.type || 'app'
    const IconComponent = (LucideIcons as any)[item.icon] || LucideIcons.Package
    const isSubApp = depth > 0

    if (type === 'link') {
      return (
        <SidebarNavItem 
          key={item.name} 
          to={item.path!} 
          icon={<IconComponent size={20} />} 
          label={item.label} 
          active={currentPath === item.path} 
          isOpen={isOpen} 
        />
      )
    }

    if (type === 'app') {
      const firstModel = item.models?.[0]
      const appPath = item.have_home
        ? `/${item.name}`
        : firstModel?.path || (firstModel?.name ? `/${item.name}/${firstModel.name}` : `/${item.name}`)
      const isActive = currentPath === appPath || currentPath.startsWith(`/${item.name}/`)
      
      return (
        <div key={`container-${item.name}`} style={{ paddingLeft: isOpen ? `${depth * 12}px` : 0 }}>
          <SidebarNavItem
            to={appPath}
            icon={<IconComponent size={isSubApp ? 16 : 20} />}
            label={item.label}
            active={isActive}
            isOpen={isOpen}
          />
          {(item as any).sub_apps && (item as any).sub_apps.length > 0 && (
            <div className="mt-1">
              {(item as any).sub_apps.map((sub: SidebarApp) => renderItem(sub, depth + 1))}
            </div>
          )}
        </div>
      )
    }
    return null
  }

  return (
    <aside className={`${isOpen ? 'w-64' : 'w-20'} transition-all duration-300 bg-white border-r border-slate-200 flex flex-col shadow-sm z-20`}>
      <SidebarBrand isOpen={isOpen} />

      <nav className="flex-1 px-4 space-y-1 mt-4 overflow-y-auto">
        {sidebarData.map((item, index) => {
          const type = item.type || 'app'
          const prevItem = index > 0 ? sidebarData[index - 1] : null
          const shouldRenderHeader = type === 'app' && (!prevItem || prevItem.type === 'link')
          
          return (
            <div key={`root-${item.name || index}`}>
              {shouldRenderHeader && isOpen && (
                <div className="py-2">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-3 mb-2">Applications</p>
                </div>
              )}
              {renderItem(item)}
            </div>
          )
        })}
      </nav>

      <div className="p-4 border-t border-slate-100 space-y-2">
        <button 
          onClick={onLogout}
          className="w-full flex items-center gap-3 p-3 rounded-xl text-rose-500 hover:bg-rose-50 transition-all group"
        >
          <LogOut size={20} className="group-hover:rotate-12 transition-transform" />
          {isOpen && <span className="font-medium">Logout</span>}
        </button>
        <button 
          onClick={() => setOpen(!isOpen)}
          className="w-full flex items-center justify-center p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors"
        >
          <Menu size={20} />
        </button>
      </div>
    </aside>
  )
}

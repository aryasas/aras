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
  return (
    <aside className={`${isOpen ? 'w-64' : 'w-20'} transition-all duration-300 bg-white border-r border-slate-200 flex flex-col shadow-sm z-20`}>
      <SidebarBrand isOpen={isOpen} />

      <nav className="flex-1 px-4 space-y-1 mt-4 overflow-y-auto">
        {sidebarData.map((item, index) => {
          // Backward compatibility check if 'type' is missing
          const type = item.type || 'app'
          
          if (type === 'link') {
            const IconComponent = (LucideIcons as any)[item.icon] || LucideIcons.Package
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
            const prevItem = index > 0 ? sidebarData[index - 1] : null
            const shouldRenderHeader = prevItem?.type === 'link'
            const IconComponent = (LucideIcons as any)[item.icon] || LucideIcons.Package
            const firstModel = item.models?.[0]
            const appPath = item.have_home
              ? `/${item.name}`
              : firstModel?.path || (firstModel?.name ? `/${item.name}/${firstModel.name}` : `/${item.name}`)
            const isActive = currentPath === appPath || currentPath.startsWith(`/${item.name}/`)
            
            return (
              <div key={`container-${item.name}`}>
                {shouldRenderHeader && isOpen && (
                  <div className="py-2">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-3 mb-2">Applications</p>
                  </div>
                )}
                <SidebarNavItem
                  to={appPath}
                  icon={<IconComponent size={20} />}
                  label={item.label}
                  active={isActive}
                  isOpen={isOpen}
                />
              </div>
            )
          }

          return null
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

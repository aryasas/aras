import { LayoutDashboard, Settings, LogOut, Menu, Terminal, Package } from 'lucide-react'
import { SidebarNavItem } from './SidebarNavItem'
import { SidebarAppMenu } from './SidebarAppMenu'
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
        <SidebarNavItem to="/" icon={<LayoutDashboard size={20} />} label="Dashboard" active={currentPath === '/'} isOpen={isOpen} />
        
        <SidebarNavItem to="/apps" icon={<Package size={20} />} label="App Manager" active={currentPath === '/apps'} isOpen={isOpen} />
        <SidebarNavItem to="/dev" icon={<Terminal size={20} />} label="Dev Tools" active={currentPath === '/dev'} isOpen={isOpen} />
        
        <div className="py-2">
          {isOpen && <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-3 mb-2">Applications</p>}
          {sidebarData.map(app => (
            <SidebarAppMenu key={app.name} app={app} isOpen={isOpen} currentPath={currentPath} />
          ))}
        </div>

        <SidebarNavItem to="/settings" icon={<Settings size={20} />} label="Settings" active={currentPath === '/settings'} isOpen={isOpen} />
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

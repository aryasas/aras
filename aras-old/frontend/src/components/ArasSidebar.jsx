import React from 'react'
import { useLocation } from 'react-router-dom'

export default function ArasSidebar({ menu = [], currentApp, currentResource }) {
  const location = useLocation()

  const apps = menu.filter(m => m.source === 'db' || m.source === 'manifest')
  const system = menu.filter(m => m.app_slug === 'admin' || m.app_slug === 'trash')

  const NavItem = ({ item }) => {
    const isActive = location.pathname === item.url || (location.pathname + '/') === item.url || (location.pathname.startsWith(item.url) && item.url !== '/')

    return (
      <div className="flex flex-col">
        <div className="flex items-center">
          <a 
            href={`${item.url}${item.url.includes('?') ? '&' : '?'}view_engine=react`}
            className={`flex-1 flex items-center px-3 py-2 text-xs font-medium transition-all duration-200 group ${
              isActive
                ? 'text-white bg-white/10 border-l-2 border-aras-accent pl-[10px]' 
                : 'text-white/60 hover:text-white hover:bg-white/5 border-l-2 border-transparent'
            }`}
          >
            <i className={`fa ${item.icon || 'fa-cubes'} w-4 text-center opacity-50 group-hover:opacity-100 transition-opacity mr-3`}></i>
            <span className="truncate">{item.title}</span>
          </a>
        </div>
      </div>
    )
  }

  return (
    <aside className="w-[240px] bg-aras-primary border-r border-white/10 flex-shrink-0 flex flex-col z-30 overflow-y-auto">
      {/* BRAND / LOGO */}
      <div className="h-14 flex items-center px-6 bg-black/10">
        <a href="/admin/?view_engine=react" className="text-white font-studio-serif font-bold tracking-wider text-lg">ARAS</a>
      </div>

      <nav className="flex-1 py-6 space-y-8">
        {apps.length > 0 && (
          <div className="px-4">
            <p className="text-[9px] font-bold text-white/20 uppercase tracking-[0.2em] mb-4 px-2">Applications</p>
            <div className="space-y-1">
              {apps.map((app, i) => <NavItem key={i} item={app} />)}
            </div>
          </div>
        )}
        
        {system.length > 0 && (
          <div className="px-4">
            <p className="text-[9px] font-bold text-white/20 uppercase tracking-[0.2em] mb-4 px-2">System</p>
            <div className="space-y-1">
              {system.map((item, i) => <NavItem key={i} item={item} />)}
            </div>
          </div>
        )}
      </nav>

      {/* USER PROFILE */}
      <div className="p-4 border-t border-white/10 bg-black/10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
            <i className="fa fa-user text-white/60"></i>
          </div>
          <div className="overflow-hidden">
            <p className="text-[11px] font-bold text-white truncate uppercase tracking-wider">Admin User</p>
            <p className="text-[10px] text-white/40 truncate">System Administrator</p>
          </div>
        </div>
      </div>
    </aside>
  )
}

import { useEffect, useMemo, useState, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronDown } from 'lucide-react'
import * as LucideIcons from 'lucide-react'
import api from '../../lib/api'
import type { AppMenuData, MenuItem, SidebarApp, MenuElement } from '../types'

const hiddenTopbarRoutes = new Set(['dashboard', 'settings'])

interface TopbarProps {
  sidebarData?: SidebarApp[]
}

export function TopbarAppMenu({ sidebarData = [] }: TopbarProps) {
  const location = useLocation()
  const [menuData, setMenuData] = useState<AppMenuData | null>(null)
  const [failedApp, setFailedApp] = useState<string | null>(null)
  const [activeGroup, setActiveGroup] = useState<string | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const appName = useMemo(() => {
    const [firstSegment] = location.pathname.split('/').filter(Boolean)
    return firstSegment || null
  }, [location.pathname])

  const rootAppName = useMemo(() => {
    if (!appName) return null
    for (const app of sidebarData) {
      if (app.name === appName) return app.name
      if (app.sub_apps?.some(sub => sub.name === appName)) {
        return app.name
      }
    }
    return appName
  }, [appName, sidebarData])

  useEffect(() => {
    let cancelled = false

    if (!rootAppName || hiddenTopbarRoutes.has(rootAppName)) {
      setMenuData(null)
      setFailedApp(null)
      return
    }

    setFailedApp(null)
    api.get(`/app-menu/${rootAppName}`)
      .then((res) => {
        if (!cancelled) setMenuData(res.data)
      })
      .catch(() => {
        if (!cancelled) {
          setMenuData(null)
          setFailedApp(rootAppName)
        }
      })

    return () => {
      cancelled = true
    }
  }, [rootAppName])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setActiveGroup(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (!appName || failedApp === rootAppName || !menuData) {
    return null
  }

  const renderMenuItem = (item: MenuItem, isDropdownItem = false) => {
    const isHome = item.path === `/${rootAppName}`
    const isActive = isHome
      ? location.pathname === item.path
      : location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)

    if (isDropdownItem) {
      const Icon = (LucideIcons as any)[item.icon || 'FileText'] || LucideIcons.FileText
      return (
        <Link
          key={item.name}
          to={item.path}
          onClick={() => setActiveGroup(null)}
          className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all ${
            isActive 
              ? 'bg-indigo-50 text-indigo-700 font-semibold' 
              : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
          }`}
        >
          <Icon size={18} className={isActive ? 'text-indigo-600' : 'text-slate-400'} />
          {item.label || item.name}
        </Link>
      )
    }

    return (
      <Link
        key={item.name}
        to={item.path}
        onClick={() => setActiveGroup(null)}
        className={`relative flex h-10 shrink-0 items-center px-4 text-sm font-medium transition-colors ${
          isActive
            ? 'text-indigo-600'
            : 'text-slate-500 hover:text-slate-900'
        }`}
      >
        {item.label || item.name}
        {isActive && (
          <span className="absolute inset-x-3 bottom-0 h-0.5 rounded-full bg-indigo-600" />
        )}
      </Link>
    )
  }

  const renderTopLevelGroup = (label: string, elements: MenuElement[]) => {
    const isOpen = activeGroup === label
    const hasActiveChild = elements.some(el => {
      if (el.type === 'group') {
        return el.items.some(item => location.pathname === item.path || location.pathname.startsWith(`${item.path}/`))
      }
      return location.pathname === (el as MenuItem).path || location.pathname.startsWith(`${(el as MenuItem).path}/`)
    })

    return (
      <div key={label} className="relative">
        <button
          onClick={() => setActiveGroup(isOpen ? null : label)}
          className={`flex h-10 items-center gap-1.5 px-4 text-sm font-medium transition-colors ${
            hasActiveChild ? 'text-indigo-600' : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          {label}
          <ChevronDown size={14} className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
          {hasActiveChild && (
            <span className="absolute inset-x-3 bottom-0 h-0.5 rounded-full bg-indigo-600" />
          )}
        </button>

        {isOpen && (
          <div className="absolute left-0 top-full z-50 mt-1 min-w-[240px] rounded-xl border border-slate-200 bg-white p-1.5 shadow-xl ring-1 ring-black/5 animate-in fade-in zoom-in-95 duration-100 max-h-[70vh] overflow-y-auto">
            {elements.length === 0 && (
               <div className="px-3 py-2 text-sm text-slate-400 italic">No items</div>
            )}
            {elements.map((element, idx) => {
              if (element.type === 'group') {
                return (
                  <div key={`nested-group-${idx}`} className={idx > 0 ? "mt-3" : ""}>
                    <div className="px-3 py-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      {element.label}
                    </div>
                    <div className="space-y-0.5">
                      {element.items.map(item => renderMenuItem(item, true))}
                    </div>
                  </div>
                )
              }
              return (
                <div key={`nested-item-${idx}`} className={idx > 0 ? "mt-1" : ""}>
                  {renderMenuItem(element as MenuItem, true)}
                </div>
              )
            })}
          </div>
        )}
      </div>
    )
  }

  return (
    <nav className="bg-white border-b border-slate-200 px-8 sticky top-0 z-30">
      <div ref={dropdownRef} className="flex flex-wrap min-h-[44px] items-end gap-1">
        {menuData.have_home && renderMenuItem({
          type: 'model',
          name: '__home__',
          label: 'Home',
          path: `/${rootAppName}`
        })}
        
        {/* Render Root App's own direct menu if any */}
        {menuData.menu?.map((element) => {
          if (element.type === 'group') {
            return renderTopLevelGroup(element.label, element.items)
          }
          return renderMenuItem(element as MenuItem)
        })}

        {/* Render Modules (Sub Apps) as Top Level Groups */}
        {menuData.sub_apps?.map(sub => {
          // If a sub_app has a menu, we render it as a group
          if (sub.menu && sub.menu.length > 0) {
            return renderTopLevelGroup(sub.label, sub.menu)
          }
          // Otherwise, just a link to the sub_app home
          return renderMenuItem({
             type: 'app_link',
             name: sub.name,
             label: sub.label,
             path: sub.path,
             icon: sub.icon
          })
        })}
      </div>
    </nav>
  )
}

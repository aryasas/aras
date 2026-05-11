import React from 'react'
import { useLocation } from 'react-router-dom'

export default function ArasTopMenu({ menu = [], currentApp, currentResource }) {
  const location = useLocation()
  
  // Find the current top-level app in the menu
  const app = menu.find(m => m.app_slug === currentApp)
  
  // Get children (e.g. Accounting, Stock, Configuration) for the secondary nav bar
  const items = app?.children || []

  const isActive = (item) => {
    if (!item.url) return false
    const currentPath = location.pathname.toLowerCase().replace(/\/+$/, '')
    const itemPath = item.url.toLowerCase().replace(/\/+$/, '')
    return currentPath === itemPath || currentPath.startsWith(itemPath + '/')
  }

  if (items.length === 0) return null

  return (
    <div className="h-12 bg-white border-b border-[#dde3e7] flex items-center px-6 gap-8 flex-shrink-0 z-10 overflow-x-auto no-scrollbar">
      {/* SECONDARY NAVIGATION LINKS (Module Home / Groups) */}
      <nav className="flex items-center gap-1 h-full">
        {items.map((item, idx) => (
          <a
            key={idx}
            href={`${item.url}${item.url.includes('?') ? '&' : '?'}view_engine=react`}
            className={`h-full flex items-center px-4 text-[10px] font-bold uppercase tracking-[0.2em] border-b-2 transition-all duration-200 ${
              isActive(item)
                ? 'border-aras-accent text-aras-accent bg-aras-accent/5'
                : 'border-transparent text-aras-primary/40 hover:text-aras-primary hover:bg-[#f8fafb]'
            }`}
          >
            {item.title}
          </a>
        ))}
      </nav>
    </div>
  )
}

import React from 'react'
import { Link, useLocation } from 'react-router-dom'

export default function ArasTopMenu({ menu, currentApp }) {
  const location = useLocation()
  const app = menu.find(m => m.slug === currentApp)
  const items = app?.children || []

  const isActive = (item) => {
    if (!item.url) return false
    return location.pathname.startsWith(item.url)
  }

  return (
    <header className="h-14 bg-white border-b border-[#dde3e7] flex items-center px-6 gap-6 flex-shrink-0 z-20">
      {/* APP TITLE */}
...
      </div>

      {/* MODULE NAVIGATION LINKS */}
      <nav className="flex items-center gap-1 h-full">
        {items.map((item, idx) => (
          <Link
            key={idx}
            to={item.url}
            className={`h-full flex items-center px-3 text-xs font-bold uppercase tracking-widest border-b-2 transition-colors ${
              isActive(item)
                ? 'border-aras-accent text-aras-accent'
                : 'border-transparent text-aras-primary/60 hover:text-aras-primary'
            }`}
          >
            {item.title}
          </Link>
        ))}
      </nav>
    </header>
  )
}

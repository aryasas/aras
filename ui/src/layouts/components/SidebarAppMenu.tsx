import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import * as LucideIcons from 'lucide-react'
import type { SidebarItem } from '../types'

interface SidebarAppMenuProps {
  app: SidebarItem
  isOpen: boolean
  currentPath: string
}

export function SidebarAppMenu({ app, isOpen, currentPath }: SidebarAppMenuProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const IconComponent = (LucideIcons as any)[app.icon] || LucideIcons.Package
  
  const models = app.models || []
  const isActive = models.some(m => currentPath === (m.name ? `/${app.name}/${m.name}` : `/${app.name}`))

  if (!isOpen) {
    const firstModelPath = models.length > 0 ? (models[0]?.name ? `/${app.name}/${models[0]?.name}` : `/${app.name}`) : `/${app.name}`
    return (
      <div className="relative group">
        <Link 
          to={firstModelPath}
          className={`p-3 rounded-xl mx-auto block mb-1 transition-all ${isActive ? 'bg-indigo-50 text-indigo-600' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-900'}`}
        >
          <IconComponent size={20} />
        </Link>
        
        {/* Tooltip on hover */}
        <div className="absolute left-full ml-4 px-3 py-2 bg-slate-900 text-white text-xs font-bold rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
          {app.label}
        </div>
      </div>
    )
  }

  return (
    <div className="mb-1">
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className={`w-full flex items-center justify-between p-3 rounded-xl transition-all ${isActive || isExpanded ? 'bg-slate-50 text-slate-900' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}
      >
        <div className="flex items-center gap-3 font-medium">
          <IconComponent size={20} className={isActive ? 'text-indigo-600' : ''} />
          <span>{app.label}</span>
        </div>
        <ChevronRight size={16} className={`transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`} />
      </button>
      
      {isExpanded && (
        <div className="ml-9 mt-1 space-y-1 border-l border-slate-100 pl-4 py-1 animate-in slide-in-from-top-1 duration-200">
          {models.map(model => {
            const targetPath = model.name ? `/${app.name}/${model.name}` : `/${app.name}`
            return (
              <Link 
                key={model.name || 'home'}
                to={targetPath}
                className={`block py-2 text-sm transition-all ${currentPath === targetPath ? 'text-indigo-600 font-bold' : 'text-slate-500 hover:text-slate-900'}`}
              >
                {model.label}
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}

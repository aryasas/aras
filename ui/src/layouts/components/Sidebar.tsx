import { LogOut, Menu } from 'lucide-react'
import { SidebarNavItem } from './SidebarNavItem'
import { SidebarBrand } from './SidebarBrand'
import type { SidebarApp } from '../types'
import { useVocabulary } from '../../context/VocabularyContext'
import { resolveIcon } from '../../lib/iconUtils'
import { isVisibleMenuItem } from '../../lib/menuUtils'

interface SidebarProps {
  isOpen: boolean
  setOpen: (open: boolean) => void
  sidebarData: SidebarApp[]
  currentPath: string
  onLogout: () => void
}

export function Sidebar({ isOpen, setOpen, sidebarData, currentPath, onLogout }: SidebarProps) {
  const vocabulary = useVocabulary()
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
          isOpen={isOpen} 
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
        <div key={`container-${item.name}`} style={{ paddingLeft: isOpen ? `${depth * 12}px` : 0 }}>
          <SidebarNavItem
            to={appPath}
            icon={<IconComponent size={isSubApp ? 16 : 20} />}
            label={item.label}
            active={isActive}
            isOpen={isOpen}
          />
        </div>
      )
    }
    return null
  }

  return (
    <aside className={`${isOpen ? 'w-64' : 'w-20'} transition-all duration-300 bg-white border-r border-slate-200 flex flex-col shadow-sm z-20`}>
      <SidebarBrand isOpen={isOpen} />

      <nav className="flex-1 px-4 space-y-1 mt-4 overflow-y-auto">
        {normalizedSidebarData.map((item, index) => {
          const type = item.type || 'app'
          const prevItem = index > 0 ? normalizedSidebarData[index - 1] : null
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

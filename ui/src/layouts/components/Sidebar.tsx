import { LogOut } from 'lucide-react'
import { SidebarNavItem } from './SidebarNavItem'
import type { SidebarApp } from '../types'
import { useVocabulary } from '../../context/VocabularyContext'
import { resolveIcon } from '../../lib/iconUtils'
import { isVisibleMenuItem } from '../../lib/menuUtils'

interface SidebarProps {
  sidebarData: SidebarApp[]
  currentPath: string
  onLogout: () => void
}

export function Sidebar({ sidebarData, currentPath, onLogout }: SidebarProps) {
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
          isOpen={false}
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
          />
        </div>
      )
    }
    return null
  }

  return (
    <aside className="col-start-1 row-start-2 z-20 flex min-h-0 flex-col border-r border-[var(--aras-border)] bg-[var(--aras-panel)] shadow-sm max-sm:flex-row max-sm:overflow-x-auto max-sm:border-b max-sm:border-r-0">
      <nav className="flex-1 overflow-y-auto pt-7 max-sm:flex max-sm:overflow-x-auto max-sm:overflow-y-hidden max-sm:pt-0">
        {normalizedSidebarData.map((item, index) => {
          const type = item.type || 'app'
          const prevItem = index > 0 ? normalizedSidebarData[index - 1] : null
          const shouldRenderHeader = type === 'app' && (!prevItem || prevItem.type === 'link')
          
          return (
            <div key={`root-${item.name || index}`}>
              {shouldRenderHeader && null}
              {renderItem(item)}
            </div>
          )
        })}
      </nav>

      <div className="border-t border-[var(--aras-border)] max-sm:border-l max-sm:border-t-0">
        <button 
          onClick={onLogout}
          className="flex h-[72px] w-full items-center justify-center text-rose-500 transition-all hover:bg-rose-50 max-sm:h-[58px] max-sm:min-w-[62px]"
          title="Logout"
          aria-label="Logout"
        >
          <LogOut size={20} className="group-hover:rotate-12 transition-transform" />
        </button>
      </div>
    </aside>
  )
}

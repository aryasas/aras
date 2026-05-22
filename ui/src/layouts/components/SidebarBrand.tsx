import { ArasLogo } from '../../components/ArasLogo'
import { useUIStore } from '../../store/uiStore'

export function SidebarBrand() {
  const { sidebarCollapsed } = useUIStore()

  return (
    <header className={`col-start-1 row-start-1 flex h-16 items-center border-b border-[var(--aras-border)] bg-[var(--aras-panel)] shadow-sm max-sm:h-[58px] max-sm:justify-start max-sm:px-4 transition-all duration-300 ${sidebarCollapsed ? 'justify-center w-[68px]' : 'px-6 w-[240px]'}`}>
      <ArasLogo size="md" showWordmark={!sidebarCollapsed} />
    </header>
  )
}

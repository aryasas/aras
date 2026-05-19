import { Link } from 'react-router-dom'

interface SidebarNavItemProps {
  to: string
  icon: React.ReactNode
  label: string
  active?: boolean
  isOpen?: boolean
}

export function SidebarNavItem({ to, icon, label, active = false, isOpen = true }: SidebarNavItemProps) {
  return (
    <Link to={to} title={label} aria-label={label} className={`
      group relative flex h-[72px] items-center justify-center border-l-4 border-transparent transition-all max-sm:h-[58px] max-sm:min-w-[62px] max-sm:border-b-4 max-sm:border-l-0
      ${active 
        ? 'font-bold bg-[var(--aras-panel)]'
        : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)] hover:text-[var(--aras-text)]'}
    `} style={active ? { color: 'var(--aras-accent)', borderLeftColor: 'var(--aras-accent)', borderBottomColor: 'var(--aras-accent)' } : undefined}>
      <span className={active ? 'text-[var(--aras-text)]' : 'text-[var(--aras-muted)] group-hover:text-[var(--aras-text)]'}>{icon}</span>
      {isOpen && <span className="sr-only">{label}</span>}
    </Link>
  )
}

import { Link } from 'react-router-dom'

interface SidebarNavItemProps {
  to: string
  icon: React.ReactNode
  label: string
  active?: boolean
  isOpen?: boolean
  collapsed?: boolean
}

export function SidebarNavItem({ to, icon, label, active = false, collapsed = true }: SidebarNavItemProps) {
  return (
    <Link 
      to={to} 
      title={label} 
      aria-label={label} 
      className={`
        group relative flex h-[48px] items-center transition-all duration-300 max-sm:h-[54px] max-sm:min-w-[58px] my-1 rounded-[14px]
        ${collapsed ? 'justify-center w-[48px] mx-auto' : 'justify-start px-3 w-full'}
        ${active 
          ? 'font-bold bg-[var(--aras-accent)] text-white shadow-[0_10px_20px_-14px_var(--aras-accent)]'
          : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)] hover:text-[var(--aras-text)]'}
      `} 
    >
      <span className={`shrink-0 transition-transform group-hover:scale-110 ${active ? 'text-white' : 'text-[var(--aras-muted)] group-hover:text-[var(--aras-text)]'}`}>
        {icon}
      </span>
      {!collapsed && (
        <span className={`ml-3 text-[13px] truncate transition-opacity duration-300 ${active ? 'text-white' : 'text-[var(--aras-muted)] group-hover:text-[var(--aras-text)]'}`}>
          {label}
        </span>
      )}
      {active && collapsed && (
        <div className="absolute left-0 h-6 w-1 rounded-r-full bg-white" />
      )}
    </Link>
  )
}

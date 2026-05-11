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
    <Link to={to} className={`
      flex items-center gap-3 p-3 rounded-xl transition-all group
      ${active 
        ? 'bg-indigo-50 text-indigo-600 font-bold shadow-sm shadow-indigo-50/50' 
        : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}
    `}>
      <span className={active ? 'text-indigo-600' : 'text-slate-400 group-hover:text-slate-900'}>{icon}</span>
      {isOpen && <span>{label}</span>}
    </Link>
  )
}

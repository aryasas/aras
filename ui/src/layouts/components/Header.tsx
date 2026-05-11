import { HeaderSearch } from './HeaderSearch'
import { HeaderActions } from './HeaderActions'

export function Header() {
  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 z-10 shadow-sm">
      <HeaderSearch />
      <HeaderActions />
    </header>
  )
}

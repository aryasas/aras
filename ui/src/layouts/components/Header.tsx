import type { ReactNode } from 'react'
import { HeaderActions } from './HeaderActions'

export function Header({ children }: { children?: ReactNode }) {
  return (
    <header className="flex min-h-16 items-center justify-end gap-3 border-b border-[var(--aras-border)] bg-[var(--aras-panel)] px-0 py-0 shadow-sm max-sm:min-h-[58px] max-sm:overflow-x-auto">
      <div className="flex items-center gap-3">
        {children}
        <HeaderActions />
      </div>
    </header>
  )
}

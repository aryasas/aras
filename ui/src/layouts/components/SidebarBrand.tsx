import { ArasLogo } from '../../components/ArasLogo'

export function SidebarBrand() {
  return (
    <header className="col-start-1 row-start-1 flex h-16 items-center justify-center border-b border-[var(--aras-border)] bg-[var(--aras-panel)] shadow-sm max-sm:h-[58px] max-sm:justify-start max-sm:px-4">
      <ArasLogo size="md" showWordmark />
    </header>
  )
}

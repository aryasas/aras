import { Search } from 'lucide-react'

export function CommandPaletteTrigger() {
  const openSearch = () => {
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))
  }

  return (
    <button
      onClick={openSearch}
      className="flex h-[44px] w-full items-center gap-3 rounded-[var(--aras-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel)] px-4 text-[var(--aras-muted)] transition-all hover:border-[var(--aras-border-strong)] hover:text-[var(--aras-text)]"
      title="Search (Cmd+K)"
    >
      <Search size={16} className="shrink-0" />
      <span className="flex-1 text-left text-sm">Search commands, records, or partners...</span>
      <span className="hidden rounded-md border border-[var(--aras-border)] bg-[var(--aras-panel-soft)] px-1.5 py-0.5 font-mono text-[10px] font-bold md:inline">⌘K</span>
    </button>
  )
}

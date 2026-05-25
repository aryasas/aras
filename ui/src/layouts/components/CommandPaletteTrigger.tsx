// claude-opus-4-7
// ARC command palette trigger: pill-shaped search bar with kbd ⌘K.
import { Search } from 'lucide-react'

export function CommandPaletteTrigger() {
  const openSearch = () => {
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))
  }

  return (
    <button
      onClick={openSearch}
      className="arc-cmd flex h-9 w-full items-center gap-2.5 rounded-full border border-[var(--line)] bg-[var(--surface)]/60 backdrop-blur px-4 text-[var(--text-3)] hover:border-[var(--text-3)] hover:text-[var(--text-2)] transition-colors"
      title="Search (Cmd+K)"
    >
      <Search size={13} className="shrink-0" />
      <span className="flex-1 text-left text-[12.5px] font-normal truncate">Find an item, command, or person…</span>
      <span className="hidden md:inline-flex items-center gap-0.5 shrink-0">
        <kbd className="inline-flex h-5 min-w-5 items-center justify-center rounded border border-[var(--line)] bg-[var(--surface-2)] px-1 font-mono text-[10px] font-semibold text-[var(--text-3)]">⌘</kbd>
        <kbd className="inline-flex h-5 min-w-5 items-center justify-center rounded border border-[var(--line)] bg-[var(--surface-2)] px-1 font-mono text-[10px] font-semibold text-[var(--text-3)]">K</kbd>
      </span>
    </button>
  )
}

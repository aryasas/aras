import React, { useState, useEffect, useRef } from 'react'
import * as LucideIcons from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '../../lib/api'
import { useAras } from '../hooks/useAras'

const SHORTCUTS = [
  { keys: ['⌘', 'K'], description: 'Open command palette / search' },
  { keys: ['?'], description: 'Show keyboard shortcuts' },
  { keys: ['Esc'], description: 'Close modal / palette / panel' },
  { keys: ['↑', '↓'], description: 'Navigate command palette results' },
  { keys: ['Enter'], description: 'Select command palette result' },
  { keys: ['Double-click'], description: 'Inline-edit a table cell' },
]

const ShortcutMap: React.FC<{ onClose: () => void }> = ({ onClose }) => (
  <div className="fixed inset-0 z-[110] flex items-center justify-center px-4 bg-black/50 backdrop-blur-sm">
    <div className="bg-[var(--aras-panel)] rounded-[var(--app-radius-lg)] shadow-2xl border border-[var(--aras-border)] w-full max-w-md overflow-hidden">
      <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-[var(--aras-border)]">
        <h2 className="text-base font-extrabold text-[var(--aras-text)]">Keyboard Shortcuts</h2>
        <button onClick={onClose} className="p-1.5 rounded-[var(--app-radius)] hover:bg-[var(--aras-panel-soft)] text-[var(--aras-muted)] transition-all">
          <LucideIcons.X size={18} />
        </button>
      </div>
      <div className="p-6 space-y-3">
        {SHORTCUTS.map((s, i) => (
          <div key={i} className="flex items-center justify-between">
            <span className="text-sm text-[var(--aras-text)]">{s.description}</span>
            <div className="flex items-center gap-1">
              {s.keys.map((k, ki) => (
                <kbd key={ki} className="bg-[var(--aras-panel-soft)] border border-[var(--aras-border)] rounded-[var(--app-radius)] px-2 py-0.5 text-xs font-bold text-[var(--aras-text)] shadow-sm">{k}</kbd>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="px-6 pb-5 text-center">
        <span className="text-xs text-[var(--aras-muted)]">Press <kbd className="bg-[var(--aras-panel-soft)] border border-[var(--aras-border)] rounded px-1 text-xs">Esc</kbd> or <kbd className="bg-[var(--aras-panel-soft)] border border-[var(--aras-border)] rounded px-1 text-xs">?</kbd> to close</span>
      </div>
    </div>
    <div className="fixed inset-0 -z-10" onClick={onClose} />
  </div>
)

export const CommandPalette: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [shortcutsOpen, setShortcutsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const { notify } = useAras()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName
      const isInput = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT'
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen(true)
      }
      if (e.key === 'Escape') { setIsOpen(false); setShortcutsOpen(false) }
      if (e.key === '?' && !isInput) {
        e.preventDefault()
        setShortcutsOpen(o => !o)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  useEffect(() => {
    if (isOpen && inputRef.current) inputRef.current.focus()
  }, [isOpen])

  useEffect(() => {
    if (query.length < 2) { setResults([]); return }
    const timer = setTimeout(async () => {
      try {
        const res = await api.get(`/search?q=${query}`)
        setResults(res.data)
        setSelectedIndex(0)
      } catch (err: any) {
        notify(err.message || 'Search failed', 'error')
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query, notify])

  const handleSelect = (result: any) => {
    navigate(`/${result.resource}/${result.id}`)
    setIsOpen(false)
    setQuery('')
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      setSelectedIndex((prev) => Math.max(prev - 1, 0))
    } else if (e.key === 'Enter' && results[selectedIndex]) {
      handleSelect(results[selectedIndex])
    }
  }

  return (
    <>
      {shortcutsOpen && <ShortcutMap onClose={() => setShortcutsOpen(false)} />}

      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-start justify-center pt-24 px-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-2xl bg-[var(--aras-panel)] rounded-[var(--app-radius-lg)] shadow-2xl border border-[var(--aras-border)] overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="relative">
              <LucideIcons.Search className="absolute left-5 top-1/2 -translate-y-1/2 text-[var(--aras-muted)]" size={18} />
              <input
                ref={inputRef}
                type="text"
                className="w-full pl-14 pr-5 py-5 text-base border-none focus:ring-0 bg-transparent text-[var(--aras-text)] placeholder:text-[var(--aras-muted)] font-medium outline-none"
                placeholder="Search records, apps, and actions... (CMD+K)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={onKeyDown}
              />
            </div>

            {results.length > 0 && (
              <div className="max-h-80 overflow-y-auto border-t border-[var(--aras-border)] p-2">
                {results.map((result, idx) => (
                  <div
                    key={`${result.resource}-${result.id}`}
                    className={`flex items-center gap-3 px-4 py-2.5 rounded-[var(--app-radius)] cursor-pointer transition-all ${
                      idx === selectedIndex ? 'bg-[var(--app-primary-action)] text-white' : 'text-[var(--app-text)] hover:bg-[var(--app-panel-soft)]'
                    }`}
                    onClick={() => handleSelect(result)}
                  >
                    <div className={`p-1.5 rounded-[var(--app-radius)] ${idx === selectedIndex ? 'bg-[var(--app-panel)]/20' : 'bg-[var(--aras-panel-soft)]'}`}>
                      <LucideIcons.Box size={16} />
                    </div>
                    <div className="flex-1">
                      <div className="font-semibold text-sm">{result.label}</div>
                      <div className="text-xs opacity-60 uppercase tracking-wider font-bold">{result.type}</div>
                    </div>
                    <LucideIcons.ChevronRight size={14} className="opacity-40" />
                  </div>
                ))}
              </div>
            )}

            {query.length >= 2 && results.length === 0 && (
              <div className="p-10 text-center text-[var(--aras-muted)] border-t border-[var(--aras-border)]">
                No results found for "{query}"
              </div>
            )}

            <div className="px-4 py-3 bg-[var(--aras-panel-soft)] border-t border-[var(--aras-border)] flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-[var(--aras-muted)]">
              <div className="flex gap-4">
                <span className="flex items-center gap-1"><kbd className="bg-[var(--aras-panel)] px-1.5 py-0.5 rounded border border-[var(--aras-border)] shadow-sm">↑↓</kbd> Navigate</span>
                <span className="flex items-center gap-1"><kbd className="bg-[var(--aras-panel)] px-1.5 py-0.5 rounded border border-[var(--aras-border)] shadow-sm">Enter</kbd> Select</span>
              </div>
              <button
                onClick={() => setShortcutsOpen(true)}
                className="flex items-center gap-1 hover:text-[var(--aras-text)] transition-colors"
                title="Show all shortcuts"
              >
                <kbd className="bg-[var(--aras-panel)] px-1.5 py-0.5 rounded border border-[var(--aras-border)] shadow-sm">?</kbd> All shortcuts
              </button>
            </div>
          </div>
          <div className="fixed inset-0 -z-10" onClick={() => setIsOpen(false)} />
        </div>
      )}
    </>
  )
}

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
  <div className="fixed inset-0 z-[110] flex items-center justify-center px-4 bg-slate-900/60 backdrop-blur-sm">
    <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden">
      <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-slate-100">
        <h2 className="text-lg font-extrabold text-slate-900">Keyboard Shortcuts</h2>
        <button onClick={onClose} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-500 transition-all">
          <LucideIcons.X size={18} />
        </button>
      </div>
      <div className="p-6 space-y-3">
        {SHORTCUTS.map((s, i) => (
          <div key={i} className="flex items-center justify-between">
            <span className="text-sm text-slate-600">{s.description}</span>
            <div className="flex items-center gap-1">
              {s.keys.map((k, ki) => (
                <kbd key={ki} className="bg-slate-50 border border-slate-200 rounded-lg px-2 py-0.5 text-xs font-bold text-slate-700 shadow-sm">{k}</kbd>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="px-6 pb-5 text-center">
        <span className="text-xs text-slate-400">Press <kbd className="bg-slate-50 border border-slate-200 rounded px-1 text-xs">Esc</kbd> or <kbd className="bg-slate-50 border border-slate-200 rounded px-1 text-xs">?</kbd> to close</span>
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
        <div className="fixed inset-0 z-[100] flex items-start justify-center pt-24 px-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="relative">
              <LucideIcons.Search className="absolute left-6 top-6 text-slate-400" size={20} />
              <input
                ref={inputRef}
                type="text"
                className="w-full pl-16 pr-6 py-6 text-lg border-none focus:ring-0 text-slate-900 placeholder-slate-400 font-medium"
                placeholder="Search records, apps, and actions... (CMD+K)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={onKeyDown}
              />
            </div>

            {results.length > 0 && (
              <div className="max-h-96 overflow-y-auto border-t border-slate-100 p-2">
                {results.map((result, idx) => (
                  <div
                    key={`${result.resource}-${result.id}`}
                    className={`flex items-center gap-4 px-4 py-3 rounded-2xl cursor-pointer transition-all ${
                      idx === selectedIndex ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'
                    }`}
                    onClick={() => handleSelect(result)}
                  >
                    <div className={`p-2 rounded-xl ${idx === selectedIndex ? 'bg-indigo-100' : 'bg-slate-100'}`}>
                      <LucideIcons.Box size={18} />
                    </div>
                    <div className="flex-1">
                      <div className="font-bold text-sm">{result.label}</div>
                      <div className="text-xs opacity-60 uppercase tracking-widest font-black">{result.type}</div>
                    </div>
                    <LucideIcons.ChevronRight size={16} className="opacity-40" />
                  </div>
                ))}
              </div>
            )}

            {query.length >= 2 && results.length === 0 && (
              <div className="p-12 text-center text-slate-400 border-t border-slate-100">
                No results found for "{query}"
              </div>
            )}

            <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-slate-400">
              <div className="flex gap-4">
                <span className="flex items-center gap-1"><kbd className="bg-white px-1.5 py-0.5 rounded border border-slate-200 shadow-sm">↑↓</kbd> Navigate</span>
                <span className="flex items-center gap-1"><kbd className="bg-white px-1.5 py-0.5 rounded border border-slate-200 shadow-sm">Enter</kbd> Select</span>
              </div>
              <button
                onClick={() => setShortcutsOpen(true)}
                className="flex items-center gap-1 hover:text-slate-600 transition-colors"
                title="Show all shortcuts"
              >
                <kbd className="bg-white px-1.5 py-0.5 rounded border border-slate-200 shadow-sm">?</kbd> All shortcuts
              </button>
            </div>
          </div>
          <div className="fixed inset-0 -z-10" onClick={() => setIsOpen(false)} />
        </div>
      )}
    </>
  )
}

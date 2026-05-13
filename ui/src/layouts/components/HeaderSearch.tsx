import { useState, useEffect, useRef } from 'react'
import { Search, FileText, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '../../lib/api'

export function HeaderSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const searchRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([])
      setIsOpen(false)
      return
    }

    const timer = setTimeout(async () => {
      try {
        setLoading(true)
        const res = await api.get('/query/search', { params: { q: query } })
        setResults(res.data)
        setIsOpen(true)
      } catch (err) {
        console.error("Global search failed", err)
      } finally {
        setLoading(false)
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [query])

  const handleSelect = (result: any) => {
    setIsOpen(false)
    setQuery('')
    // We need to find the app name. Since we don't have it in result, 
    // we use a generic path or assume the resource name is enough for DynamicView to resolve.
    // DynamicView handles :app/:model, so we might need to adjust or make DynamicView smarter.
    // For now, let's use a path that DynamicView can handle.
    navigate(`/core/${result.resource}/${result.id}`)
  }

  return (
    <div className="relative w-96" ref={searchRef}>
      <div className="relative">
        <Search className={`absolute left-3 top-1/2 -translate-y-1/2 transition-colors ${loading ? 'text-indigo-500 animate-pulse' : 'text-slate-400'}`} size={18} />
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
          placeholder="Search anything..." 
          className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-100 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none transition-all text-sm"
        />
      </div>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden z-[100] animate-in slide-in-from-top-2 duration-200">
          <div className="max-h-96 overflow-y-auto p-2">
            {results.length === 0 ? (
              <div className="p-4 text-center text-slate-400 text-sm italic">
                No results found for "{query}"
              </div>
            ) : (
              <div className="space-y-1">
                <div className="px-3 py-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  Found {results.length} results
                </div>
                {results.map((res, i) => (
                  <button
                    key={`${res.resource}-${res.id}-${i}`}
                    onClick={() => handleSelect(res)}
                    className="w-full flex items-center gap-3 p-3 hover:bg-indigo-50 rounded-xl transition-all text-left group"
                  >
                    <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center text-slate-500 group-hover:bg-white group-hover:text-indigo-600 transition-colors">
                      <FileText size={20} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-bold text-slate-900 truncate">{res.label}</div>
                      <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">{res.type}</div>
                    </div>
                    <ChevronRight size={16} className="text-slate-300 group-hover:text-indigo-400" />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

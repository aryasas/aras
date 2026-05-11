import React, { useState, useMemo, useRef, useEffect } from 'react'

export default function ArasSearchableSelect({ value, onChange, options = [], addUrl, placeholder, className = '' }) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const ref = useRef(null)

  // Normalize options to {id, label} format and filter out sentinels
  const normalizedOptions = useMemo(() => {
    return (options || [])
      .map(opt => {
        if (Array.isArray(opt)) {
          return { id: opt[0], label: opt[1] }
        }
        return opt
      })
      .filter(opt => {
        // Filter out "— Select —" sentinels (id 0 or placeholder labels)
        const idStr = String(opt.id)
        const lblStr = String(opt.label)
        return idStr !== '0' && idStr !== '' && !lblStr.includes('— Select') && !lblStr.includes('— Choose')
      })
  }, [options])

  const filteredOptions = useMemo(() => {
    return normalizedOptions.filter(opt => 
      String(opt.label).toLowerCase().includes(search.toLowerCase())
    )
  }, [normalizedOptions, search])

  const selectedOption = normalizedOptions.find(o => String(o.id) === String(value))

  useEffect(() => {
    function handleClickOutside(event) {
      if (ref.current && !ref.current.contains(event.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [ref])

  return (
    <div className={`relative ${className}`} ref={ref}>
      <div 
        className="w-full bg-[#fcfcfb] border border-[#dde3e7] rounded-md px-4 py-3 text-[14px] text-[#0f1b2d] font-studio-sans cursor-pointer shadow-inner flex items-center justify-between aras-engraved focus-within:ring-1 focus-within:ring-[#c9a568] focus-within:border-[#c9a568] transition-all"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className={selectedOption ? '' : 'text-[#9aacb8]'}>
          {selectedOption ? selectedOption.label : placeholder || 'Select option...'}
        </span>
        <svg className={`w-4 h-4 text-[#9aacb8] transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/></svg>
      </div>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-[#dde3e7] rounded-md shadow-2xl overflow-hidden animate-slide-up">
          <div className="p-2 border-b border-[#dde3e7] bg-[#faf8f3]">
            <input 
              type="text" 
              className="w-full bg-white border border-[#dde3e7] rounded px-3 py-2 text-[13px] font-studio-sans focus:outline-none focus:border-[#c9a568]"
              placeholder="Type to search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onClick={(e) => e.stopPropagation()}
            />
          </div>
          <ul className="max-h-60 overflow-y-auto py-1">
            <li 
              className="px-4 py-2 text-[13px] hover:bg-[#faf8f3] cursor-pointer text-[#9aacb8] italic"
              onClick={() => {
                onChange(null)
                setIsOpen(false)
              }}
            >
              — Clear Selection —
            </li>
            {filteredOptions.length === 0 ? (
              <li className="px-4 py-3 text-[13px] text-center text-[#9aacb8] italic">No options found.</li>
            ) : (
              filteredOptions.map(opt => (
                <li 
                  key={opt.id}
                  className={`px-4 py-2 text-[13px] cursor-pointer transition-colors ${String(opt.id) === String(value) ? 'bg-[#fcfcfb] text-[#c9a568] font-bold' : 'hover:bg-[#faf8f3] text-[#0f1b2d]'}`}
                  onClick={() => {
                    onChange(opt.id)
                    setIsOpen(false)
                  }}
                >
                  {opt.label}
                </li>
              ))
            )}
          </ul>
          {addUrl && (
            <div className="border-t border-[#dde3e7] bg-[#faf8f3]">
              <a href={addUrl} target="_blank" rel="noopener noreferrer" className="block px-4 py-2.5 text-[11px] font-bold text-[#c9a568] hover:text-[#0f1b2d] hover:bg-[#eef0f2] transition-colors uppercase tracking-widest text-center">
                + Create New Record
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

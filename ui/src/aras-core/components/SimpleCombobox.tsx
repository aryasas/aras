// claude-opus-4-7
// SimpleCombobox: lightweight chrome-only dropdown for outside-form usage
// (header switchers, toolbar selects). No async search, no add-new, no field
// metadata. Use Combobox for in-form usage that needs full features.
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Check, ChevronDown } from 'lucide-react'

export interface SimpleOption {
  label: string
  value: string | number
  disabled?: boolean
}

interface Props {
  options: SimpleOption[]
  value: string | number | null | undefined
  onChange: (value: string | number) => void
  placeholder?: string
  size?: 'sm' | 'md'
  align?: 'left' | 'right'
  className?: string
  width?: number | string
  title?: string
  disabled?: boolean
  searchable?: boolean
  searchPlaceholder?: string
  renderOption?: (option: SimpleOption, selected: boolean) => ReactNode
  renderValue?: (selected: SimpleOption | null) => ReactNode
}

export default function SimpleCombobox({
  options,
  value,
  onChange,
  placeholder = 'Select...',
  size = 'sm',
  align = 'left',
  className = '',
  width,
  title,
  disabled,
  searchable = false,
  searchPlaceholder = 'Search...',
  renderOption,
  renderValue,
}: Props) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const wrapRef = useRef<HTMLDivElement>(null)
  const btnRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [])

  const selected = options.find((o) => o.value === value) || null
  const filteredOptions = searchable
    ? options.filter((option) => option.label.toLowerCase().includes(query.trim().toLowerCase()))
    : options
  const heightCls = size === 'sm' ? 'h-7 text-[12px]' : 'h-8 text-[13px]'
  const padCls = size === 'sm' ? 'px-2.5' : 'px-3'

  return (
    <div ref={wrapRef} className={`relative inline-block ${className}`} style={width ? { width } : undefined}>
      <button
        ref={btnRef}
        type="button"
        title={title}
        disabled={disabled}
        onClick={() => !disabled && setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className={`${heightCls} ${padCls} inline-flex w-full items-center justify-between gap-1.5 rounded-full border border-[var(--line)] bg-transparent text-[var(--text-2)] hover:text-[var(--text)] hover:border-[var(--text-3)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed outline-none focus-visible:border-[var(--accent)]`}
      >
        <span className="truncate text-left flex-1">
          {selected ? (renderValue ? renderValue(selected) : selected.label) : <span className="text-[var(--text-3)]">{placeholder}</span>}
        </span>
        <ChevronDown size={12} className="shrink-0 opacity-70" />
      </button>

      {open && (
        <div
          role="listbox"
          className={`absolute top-full z-50 mt-1.5 min-w-full max-h-64 overflow-y-auto rounded-lg border border-[var(--line)] bg-[var(--surface)] py-1 shadow-lg ${align === 'right' ? 'right-0' : 'left-0'}`}
        >
          {searchable ? (
            <div className="px-2.5 pb-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={searchPlaceholder}
                className="h-8 w-full rounded-md border border-[var(--line)] bg-[var(--surface-2)] px-2.5 text-[12px] text-[var(--text)] outline-none focus:border-[var(--accent)]"
              />
            </div>
          ) : null}
          {filteredOptions.length === 0 && (
            <div className="px-3 py-2 text-[12px] text-[var(--text-3)]">No options</div>
          )}
          {filteredOptions.map((opt) => {
            const active = opt.value === value
            return (
              <button
                key={String(opt.value)}
                type="button"
                role="option"
                aria-selected={active}
                disabled={opt.disabled}
                onClick={() => { onChange(opt.value); setOpen(false); setQuery(''); btnRef.current?.focus() }}
                className={`w-full flex items-center gap-2 px-2.5 py-1.5 text-left text-[12px] font-medium transition-colors disabled:opacity-50 ${active ? 'text-[var(--accent)] bg-[var(--surface-2)]' : 'text-[var(--text)] hover:bg-[var(--surface-2)]'}`}
              >
                {renderOption ? (
                  <span className="flex w-full items-center gap-2">
                    <Check size={12} className={active ? 'opacity-100' : 'opacity-0'} />
                    <span className="flex-1 min-w-0">{renderOption(opt, active)}</span>
                  </span>
                ) : (
                  <>
                    <Check size={12} className={active ? 'opacity-100' : 'opacity-0'} />
                    <span className="flex-1 truncate">{opt.label}</span>
                  </>
                )}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

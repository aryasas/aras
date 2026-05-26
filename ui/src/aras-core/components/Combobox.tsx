import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { Search, Plus, Check, ChevronDown, X, Loader2, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { Field } from '../SchemaRegistry';

interface Option {
  label: string;
  value: string | number;
}

interface ComboboxItem {
  id: string | number;
  name: string;
  [key: string]: string | number;
}

interface ComboboxProps {
  resource?: string;
  options?: Option[];
  value: string | number | undefined | null;
  onChange: (value: string | number | undefined | null) => void;
  placeholder?: string;
  displayField?: string;
  disabled?: boolean;
  extraFilters?: Record<string, string | number | boolean>;
  field?: Field;
  variant?: 'lookup' | 'simple';
  /** compact=true renders a shorter trigger for inline table rows */
  compact?: boolean;
}

// claude-sonnet-4-6
const Combobox: React.FC<ComboboxProps> = ({
  resource,
  options,
  value,
  onChange,
  placeholder = "Select...",
  displayField = "name",
  disabled = false,
  extraFilters,
  field,
  variant = 'lookup',
  compact = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [items, setItems] = useState<ComboboxItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<ComboboxItem | null>(null);
  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [dropdownStyles, setDropdownStyles] = useState<React.CSSProperties>({});
  const navigate = useNavigate();
  const targetResource = field?.target_resource || resource;
  const isSimple = variant === 'simple';
  const isLookup = !isSimple && !!resource;

  const optionToItem = (opt: Option): ComboboxItem => ({
    id: opt.value,
    name: opt.label,
    [displayField]: opt.label,
  });

  const updateDropdownPosition = useCallback(() => {
    if (isOpen && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      const dropdownHeight = 320;
      const spaceBelow = windowHeight - rect.bottom;
      const showAbove = spaceBelow < dropdownHeight && rect.top > dropdownHeight;
      setDropdownStyles({
        position: 'fixed',
        top: showAbove ? 'auto' : `${rect.bottom + 4}px`,
        bottom: showAbove ? `${windowHeight - rect.top + 4}px` : 'auto',
        left: `${rect.left}px`,
        width: `${Math.max(rect.width, 220)}px`,
        zIndex: 9999,
      });
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current && !containerRef.current.contains(event.target as Node) &&
        dropdownRef.current && !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSearch('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => { updateDropdownPosition(); }, [isOpen, updateDropdownPosition]);

  useEffect(() => {
    if (!isOpen) return;
    window.addEventListener('scroll', updateDropdownPosition, true);
    window.addEventListener('resize', updateDropdownPosition);
    return () => {
      window.removeEventListener('scroll', updateDropdownPosition, true);
      window.removeEventListener('resize', updateDropdownPosition);
    };
  }, [isOpen, updateDropdownPosition]);

  useEffect(() => {
    const fetchAndSetSelectedItem = async () => {
      if (resource && value) {
        try {
          setInitialLoading(true);
          const res = await api.get(`/${cleanResourcePath(resource)}/${value}`);
          setSelectedItem(res.data);
        } catch {
          setSelectedItem(null);
        } finally {
          setInitialLoading(false);
        }
      } else if (options && value) {
        const opt = options.find(o => String(o.value) === String(value));
        setSelectedItem(opt ? optionToItem(opt) : null);
      } else if (!value) {
        setSelectedItem(null);
      }
    };
    fetchAndSetSelectedItem();
  }, [value, resource, options, displayField]);

  useEffect(() => {
    if (!isOpen || disabled || !resource) return;
    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        const cleanRes = cleanResourcePath(resource);
        const extraFilterList = extraFilters
          ? Object.entries(extraFilters).map(([f, v]) => ({ field: f, op: '=', value: v }))
          : [];
        const params = {
          search: search || undefined,
          per_page: 20,
          ...(extraFilterList.length ? { filters: JSON.stringify(extraFilterList) } : {}),
        };
        const res = await api.get(`/${cleanRes}/`, { params });
        setItems(res.data.items);
        setActiveIndex(-1);
      } catch {
        // silent
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [search, resource, isOpen, disabled, extraFilters]);

  useEffect(() => {
    if (options) {
      setItems(
        options
          .filter(opt => opt.label.toLowerCase().includes(search.toLowerCase()))
          .map(optionToItem)
      );
      setActiveIndex(-1);
    }
  }, [search, options, displayField]);

  const handleSelect = (item: ComboboxItem) => {
    setSelectedItem(item);
    onChange(item.id);
    setIsOpen(false);
    setSearch('');
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (disabled) return;
    setSelectedItem(null);
    onChange(null);
  };

  const handleAddNew = () => {
    if (disabled || !targetResource) return;
    navigate(`/${cleanResourcePath(targetResource)}/new`);
  };

  const handleOpenRecord = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!targetResource || !value) return;
    navigate(`/${cleanResourcePath(targetResource)}/${value}`);
  };

  const handleOpenItemRecord = (e: React.MouseEvent, item: ComboboxItem) => {
    e.preventDefault();
    e.stopPropagation();
    if (!targetResource || !item.id) return;
    setIsOpen(false);
    setSearch('');
    navigate(`/${cleanResourcePath(targetResource)}/${item.id}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter') {
        e.preventDefault();
        setIsOpen(true);
      }
      return;
    }
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex(prev => Math.min(prev + 1, items.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (activeIndex >= 0 && activeIndex < items.length) handleSelect(items[activeIndex]);
        else if (items.length > 0) handleSelect(items[0]);
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setSearch('');
        break;
      case 'Tab':
        setIsOpen(false);
        setSearch('');
        break;
    }
  };

  const triggerH = compact ? 'h-7' : 'h-9';
  const triggerText = compact ? 'text-[11.5px]' : 'text-[12.5px]';

  const dropdownMenu = (
    <div
      ref={dropdownRef}
      role="listbox"
      aria-labelledby={`cbx-btn-${field?.name || resource}`}
      style={dropdownStyles}
      data-combobox-dropdown
      className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius)] shadow-[0_16px_40px_-12px_rgba(15,23,42,0.22),0_4px_12px_-4px_rgba(15,23,42,0.10)] overflow-hidden"
    >
      {/* Search header */}
      <div className="p-1.5 border-b border-[var(--line)]">
        <div className="relative">
          <Search size={12} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
          <input
            ref={inputRef}
            autoFocus
            type="text"
            placeholder="Search..."
            className="w-full h-7 pl-7 pr-3 bg-[var(--surface-2)] border border-transparent rounded-[var(--radius-sm)] text-[12px] font-medium text-[var(--text)] placeholder:text-[var(--text-3)] outline-none focus:border-[var(--accent)] focus:bg-[var(--surface)] transition-all"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>
      </div>

      {/* List */}
      <div className="max-h-[220px] overflow-y-auto p-1">
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-5 text-[var(--text-3)]">
            <Loader2 size={13} className="animate-spin text-[var(--accent)]" />
            <span className="text-[11px] font-medium">Loading…</span>
          </div>
        ) : items.length === 0 ? (
          <div className="py-5 text-center text-[11px] text-[var(--text-3)]">No results</div>
        ) : (
          items.map((item, index) => {
            const isSelected = String(value) === String(item.id);
            const isActive = index === activeIndex;
            return (
              <div
                key={item.id}
                role="option"
                aria-selected={isSelected}
                onClick={() => handleSelect(item)}
                onMouseEnter={() => setActiveIndex(index)}
                className={`group/cbx-option flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-[var(--radius-sm)] cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-[var(--accent)] text-white'
                    : isActive
                      ? 'bg-[var(--surface-2)] text-[var(--text)]'
                      : 'text-[var(--text)] hover:bg-[var(--surface-2)]'
                }`}
              >
                <span className={`text-[12px] truncate ${isSelected ? 'font-semibold' : 'font-medium'}`}>
                  {item[displayField] || item.id}
                </span>
                <span className="flex shrink-0 items-center gap-1">
                  {isLookup && targetResource && (
                    <button
                      type="button"
                      tabIndex={-1}
                      onClick={(e) => handleOpenItemRecord(e, item)}
                      onMouseDown={(e) => { e.preventDefault(); e.stopPropagation(); }}
                      title="Open record"
                      className={`grid h-5 w-5 place-items-center rounded transition-all ${
                        isSelected
                          ? 'text-white/80 hover:bg-white/15 hover:text-white'
                          : 'text-[var(--text-3)] opacity-0 group-hover/cbx-option:opacity-100 group-focus-within/cbx-option:opacity-100 hover:bg-[color-mix(in_oklch,var(--accent)_10%,transparent)] hover:text-[var(--accent)]'
                      }`}
                    >
                      <ExternalLink size={11} />
                    </button>
                  )}
                  {isSelected && <Check size={12} className="opacity-90" />}
                </span>
              </div>
            );
          })
        )}
      </div>

      {/* Footer: add new */}
      {isLookup && targetResource && !disabled && (
        <div className="p-1 border-t border-[var(--line)]">
          <button
            type="button"
            onMouseDown={(e) => { e.preventDefault(); handleAddNew(); }}
            className="flex items-center gap-1.5 w-full px-2.5 py-1.5 text-[11.5px] font-semibold text-[var(--accent)] hover:bg-[var(--accent)] hover:text-white rounded-[var(--radius-sm)] transition-colors"
          >
            <Plus size={11} />
            Add new record
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div
      className={`group/cbx relative w-full ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
      ref={containerRef}
    >
      <div
        id={`cbx-btn-${field?.name || resource}`}
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        tabIndex={disabled ? -1 : 0}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        className={`
          flex items-center w-full ${triggerH} px-2.5 gap-1.5
          bg-[var(--surface-2)] border border-[var(--line)] rounded-[var(--radius-sm)]
          transition-all cursor-pointer select-none
          ${isOpen
            ? 'border-[var(--accent)] bg-[var(--surface)] shadow-[0_0_0_3px_color-mix(in_oklch,var(--accent)_18%,transparent)]'
            : 'hover:border-[var(--line-2)] hover:bg-[var(--surface)]'
          }
        `}
      >
        {/* Value label */}
        <div className={`flex-1 min-w-0 truncate ${triggerText}`}>
          {initialLoading ? (
            <span className="flex items-center gap-1.5 text-[var(--text-3)]">
              <Loader2 size={11} className="animate-spin text-[var(--accent)]" />
              Loading…
            </span>
          ) : selectedItem ? (
            <span className="font-medium text-[var(--text)] truncate">
              {selectedItem[displayField] || selectedItem.id}
            </span>
          ) : (
            <span className="text-[var(--text-3)]">{placeholder}</span>
          )}
        </div>

        {/* Action icons — always in trigger, visible on hover or when open/selected */}
        <div className="flex items-center gap-0.5 shrink-0">
          {/* FK shortcut: navigate to selected record */}
          {isLookup && value && !isOpen && (
            <button
              type="button"
              tabIndex={-1}
              onMouseDown={(e) => { e.preventDefault(); e.stopPropagation(); handleOpenRecord(e); }}
              title="Open record"
              className="h-5 w-5 grid place-items-center rounded text-[var(--text-3)] opacity-0 group-hover/cbx:opacity-100 hover:!text-[var(--accent)] hover:bg-[color-mix(in_oklch,var(--accent)_10%,transparent)] transition-all"
            >
              <ExternalLink size={11} />
            </button>
          )}

          {/* Clear */}
          {selectedItem && !disabled && (
            <button
              type="button"
              tabIndex={-1}
              onMouseDown={(e) => { e.preventDefault(); handleClear(e); }}
              title="Clear"
              className="h-5 w-5 grid place-items-center rounded text-[var(--text-3)] opacity-0 group-hover/cbx:opacity-100 hover:!text-[var(--danger)] hover:bg-[color-mix(in_oklch,var(--danger)_10%,transparent)] transition-all"
            >
              <X size={11} />
            </button>
          )}

          {/* Chevron */}
          <ChevronDown
            size={12}
            className={`text-[var(--text-3)] transition-transform shrink-0 ${isOpen ? 'rotate-180' : ''}`}
          />
        </div>
      </div>

      {isOpen && !disabled && createPortal(dropdownMenu, document.body)}
    </div>
  );
};

export default Combobox;

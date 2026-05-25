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
}

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
  variant = 'lookup'
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

  const optionToItem = (opt: Option): ComboboxItem => ({
    id: opt.value,
    name: opt.label,
    [displayField]: opt.label,
  });

  const updateDropdownPosition = useCallback(() => {
    if (isOpen && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      const dropdownHeight = 350;
      
      const spaceBelow = windowHeight - rect.bottom;
      const showAbove = spaceBelow < dropdownHeight && rect.top > dropdownHeight;

      setDropdownStyles({
        position: 'fixed',
        top: showAbove ? 'auto' : `${rect.bottom + 4}px`,
        bottom: showAbove ? `${windowHeight - rect.top + 4}px` : 'auto',
        left: `${rect.left}px`,
        width: `${rect.width}px`,
        zIndex: 9999,
      });
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node) && 
          dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    updateDropdownPosition();
  }, [isOpen, updateDropdownPosition]);

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
          const cleanRes = cleanResourcePath(resource);
          const res = await api.get(`/${cleanRes}/${value}`);
          setSelectedItem(res.data);
        } catch (err) {
          console.error("Failed to fetch selected item", err);
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
          ? Object.entries(extraFilters).map(([field, value]) => ({ field, op: '=', value }))
          : [];
        const params = {
          search: search || undefined,
          per_page: 20,
          ...(extraFilterList.length ? { filters: JSON.stringify(extraFilterList) } : {}),
        };
        const res = await api.get(`/${cleanRes}/`, { params });
        setItems(res.data.items);
        setActiveIndex(-1);
      } catch (err) {
        console.error("Failed to fetch items", err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [search, resource, isOpen, disabled, extraFilters]);

  useEffect(() => {
    if (options) {
      const filtered = options.filter(opt =>
        opt.label.toLowerCase().includes(search.toLowerCase())
      ).map(optionToItem);
      setItems(filtered);
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
    const cleanRes = cleanResourcePath(targetResource);
    navigate(`/${cleanRes}/new`);
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
        setActiveIndex(prev => (prev < items.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex(prev => (prev > 0 ? prev - 1 : 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (activeIndex >= 0 && activeIndex < items.length) {
          handleSelect(items[activeIndex]);
        } else if (items.length > 0 && activeIndex === -1) {
          handleSelect(items[0]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        break;
      case 'Tab':
        setIsOpen(false);
        break;
    }
  };

  const dropdownMenu = (
    <div 
      ref={dropdownRef}
      id={`combobox-listbox-${field?.name || resource}`}
      role="listbox"
      aria-labelledby={`combobox-button-${field?.name || resource}`}
      style={dropdownStyles}
      data-combobox-dropdown
      className="bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-[1rem] shadow-[0_18px_45px_-18px_rgba(15,23,42,0.35)] overflow-hidden animate-in fade-in zoom-in-95 duration-100"
    >
      {!isSimple && (
        <div className="p-2 border-b border-[var(--aras-border)] bg-[var(--aras-panel-soft)]/60">
          <div className="relative group">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--aras-muted)]" />
            <input 
              ref={inputRef}
              autoFocus
              type="text"
              placeholder="Search..."
              className="w-full min-h-10 pl-8 pr-3 py-2 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-[var(--aras-radius)] text-sm font-semibold outline-none focus:border-[var(--aras-accent)] transition-all text-[var(--aras-text)] placeholder:text-[var(--aras-muted)]"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </div>
        </div>
      )}

      <div className="max-h-[240px] overflow-y-auto p-1 scrollbar-thin scrollbar-thumb-[var(--aras-border-strong)] scrollbar-track-transparent">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-6 text-[var(--aras-muted)]">
            <Loader2 size={16} className="animate-spin mb-1.5 text-[var(--aras-accent)]" />
            <span className="text-[10px] font-medium">Loading...</span>
          </div>
        ) : items.length === 0 ? (
          <div className="py-6 text-center text-xs text-[var(--aras-muted)] italic">
            No results found
          </div>
        ) : (
          <div className="space-y-0.5">
            {items.map((item, index) => {
              const isSelected = String(value) === String(item.id);
              const isActive = index === activeIndex;
              return (
                <div 
                  key={item.id}
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setActiveIndex(index)}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-[var(--aras-radius)] cursor-pointer transition-all ${
                    isSelected 
                      ? 'bg-[var(--aras-accent)] text-white' 
                      : isActive 
                        ? 'bg-[var(--aras-panel-soft)] text-[var(--aras-text)]' 
                        : 'text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)]'
                  }`}
                >
                  <span className={`text-sm truncate ${isSelected ? 'font-bold' : 'font-semibold'}`}>
                    {item[displayField] || item.id}
                  </span>
                  {isSelected && <Check size={14} className="shrink-0 ml-2" />}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {!isSimple && targetResource && !disabled && (
        <div className="p-2 border-t border-[var(--aras-border)] bg-[var(--aras-panel-soft)]/50">
          <button 
            type="button"
            onMouseDown={(e) => { e.preventDefault(); handleAddNew(); }}
            className="flex items-center gap-2 w-full px-3 py-2 text-xs font-bold text-[var(--aras-accent)] hover:bg-[var(--aras-accent)] hover:text-white rounded-[var(--aras-radius)] transition-all"
          >
            <Plus size={12} /> 
            Add New Record
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div className={`relative w-full ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`} ref={containerRef}>
      <div
        id={`combobox-button-${field?.name || resource}`}
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={`combobox-listbox-${field?.name || resource}`}
        tabIndex={disabled ? -1 : 0}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        className={`aras-combobox-trigger flex items-center justify-between w-full min-h-[46px] px-4 bg-[var(--aras-panel-soft)] border rounded-[var(--aras-radius)] text-sm transition-all ${
          disabled 
            ? 'border-[var(--aras-border)] bg-[var(--aras-panel-soft)]' 
            : isOpen 
              ? 'border-[var(--aras-accent)] bg-[var(--aras-panel)] cursor-pointer shadow-[0_0_0_4px_color-mix(in_srgb,var(--aras-accent)_10%,transparent)]' 
              : 'border-[var(--aras-border)] hover:border-[var(--aras-border-strong)] cursor-pointer'
        }`}
      >
        <div className="flex-1 truncate text-left pr-2">
          {initialLoading ? (
            <div className="flex items-center gap-1.5">
              <Loader2 size={14} className="animate-spin text-[var(--aras-accent)]" />
              <span className="text-[var(--aras-muted)]">Loading...</span>
            </div>
          ) : selectedItem ? (
            <span className={`text-[var(--aras-text)] ${isSimple ? 'font-medium' : 'font-semibold'}`}>{selectedItem[displayField] || selectedItem.id}</span>
          ) : (
            <span className="text-[var(--aras-muted)]">{placeholder}</span>
          )}
        </div>
        
        <div className="flex items-center gap-1.5 shrink-0 ml-auto">
          {!isSimple && value && targetResource && !isOpen && (
            <button
              type="button"
              tabIndex={-1}
              onMouseDown={(e) => { e.preventDefault(); e.stopPropagation(); navigate(`/${cleanResourcePath(targetResource)}/${value}`); }}
              className="p-1 text-[var(--aras-muted)] hover:text-[var(--aras-accent)] rounded-[var(--app-radius)]"
              title="View Record"
            >
              <ExternalLink size={12} />
            </button>
          )}
          {selectedItem && !disabled && (
            <button 
              tabIndex={-1}
              onClick={handleClear} 
              className="p-1 text-[var(--aras-muted)] hover:text-red-500 rounded-[var(--app-radius)]"
            >
              <X size={12} />
            </button>
          )}
          <ChevronDown size={14} className={`text-[var(--aras-muted)] transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </div>

      {isOpen && !disabled && createPortal(dropdownMenu, document.body)}
    </div>
  );
};

export default Combobox;

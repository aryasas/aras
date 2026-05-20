import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { Search, Check, ChevronDown, X, Loader2 } from 'lucide-react';

interface MultiSelectComboboxProps {
  resource: string;
  value: any[];
  onChange: (value: any[]) => void;
  placeholder?: string;
  displayField?: string;
  disabled?: boolean;
}

const MultiSelectCombobox: React.FC<MultiSelectComboboxProps> = ({ 
  resource, 
  value = [], 
  onChange, 
  placeholder = "Select multiple...", 
  displayField = "name",
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedItems, setSelectedItems] = useState<any[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [dropdownStyles, setDropdownStyles] = useState<React.CSSProperties>({});

  const updateDropdownPosition = useCallback(() => {
    if (isOpen && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      const dropdownHeight = 300;
      
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
    if (value && value.length > 0 && selectedItems.length === 0) {
      const fetchSelected = async () => {
        try {
          const cleanRes = cleanResourcePath(resource);
          const promises = value.map(id => api.get(`/${cleanRes}/${id}`));
          const responses = await Promise.all(promises);
          setSelectedItems(responses.map(r => r.data));
        } catch (err) {
          console.error("Failed to fetch selected items", err);
        }
      };
      fetchSelected();
    } else if (!value || value.length === 0) {
      setSelectedItems([]);
    }
  }, [value, resource, selectedItems.length]);

  useEffect(() => {
    if (!isOpen || disabled) return;

    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        const cleanRes = cleanResourcePath(resource);
        const params = {
          search: search || undefined,
          per_page: 20
        };
        const res = await api.get(`/${cleanRes}/`, { params });
        setItems(res.data.items);
      } catch (err) {
        console.error("Failed to fetch items", err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [search, resource, isOpen, disabled]);

  const handleSelect = (item: any) => {
    const isSelected = value.includes(item.id);
    let newValue: any[];
    let newSelectedItems: any[];

    if (isSelected) {
      newValue = value.filter(id => id !== item.id);
      newSelectedItems = selectedItems.filter(i => i.id !== item.id);
    } else {
      newValue = [...value, item.id];
      newSelectedItems = [...selectedItems, item];
    }

    setSelectedItems(newSelectedItems);
    onChange(newValue);
  };

  const handleRemove = (e: React.MouseEvent, itemId: any) => {
    e.stopPropagation();
    if (disabled) return;
    const newValue = value.filter(id => id !== itemId);
    const newSelectedItems = selectedItems.filter(i => i.id !== itemId);
    setSelectedItems(newSelectedItems);
    onChange(newValue);
  };

  const dropdownMenu = (
    <div 
      ref={dropdownRef}
      style={dropdownStyles}
      className="bg-[var(--aras-panel)] border border-[var(--aras-border-strong)] rounded-lg shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-100 ring-1 ring-black/5"
    >
      <div className="p-1.5 border-b border-[var(--aras-border)] bg-[var(--aras-panel-soft)]/50">
        <div className="relative group">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--aras-muted)]" />
          <input 
            autoFocus
            type="text"
            placeholder="Search..."
            className="w-full pl-8 pr-3 py-1.5 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-md text-xs outline-none focus:border-[var(--aras-accent)] transition-all text-[var(--aras-text)] placeholder:text-[var(--aras-muted)]"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

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
            {items.map((item) => {
              const isSelected = value.includes(item.id);
              return (
                <div 
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  className={`flex items-center justify-between px-2.5 py-1.5 rounded-[var(--aras-radius)] cursor-pointer transition-all ${
                    isSelected 
                      ? 'bg-[var(--aras-accent)] text-white' 
                      : 'text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)]'
                  }`}
                >
                  <span className={`text-xs truncate ${isSelected ? 'font-bold' : 'font-medium'}`}>
                    {item[displayField] || item.id}
                  </span>
                  {isSelected && <Check size={14} className="shrink-0 ml-2" />}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className={`relative w-full ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`} ref={containerRef}>
      <div 
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={`flex flex-wrap items-center gap-1.5 w-full min-h-[36px] px-3 py-1 bg-[var(--aras-panel)] border rounded-[var(--aras-radius)] text-xs transition-all ${
          disabled 
            ? 'border-[var(--aras-border)] bg-[var(--aras-panel-soft)]' 
            : isOpen 
              ? 'border-[var(--aras-accent)] ring-2 ring-[var(--aras-accent)]/10 cursor-pointer shadow-sm' 
              : 'border-[var(--aras-border)] hover:border-[var(--aras-border-strong)] cursor-pointer'
        }`}
      >
        {selectedItems.length > 0 ? (
          selectedItems.map(item => (
            <span key={item.id} className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-[var(--aras-accent)]/10 text-[var(--aras-accent)] rounded-md text-[10px] font-bold">
              {item[displayField] || item.id}
              {!disabled && (
                <button 
                  onClick={(e) => handleRemove(e, item.id)}
                  className="hover:text-[var(--aras-accent)] opacity-60 hover:opacity-100"
                >
                  <X size={10} />
                </button>
              )}
            </span>
          ))
        ) : (
          <span className="text-[var(--aras-muted)] py-1">{placeholder}</span>
        )}
        <div className="flex-1" />
        <ChevronDown size={14} className={`text-[var(--aras-muted)] transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </div>

      {isOpen && !disabled && createPortal(dropdownMenu, document.body)}
    </div>
  );
};

export default MultiSelectCombobox;

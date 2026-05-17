import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { Search, Plus, Check, ChevronDown, X, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Option {
  label: string;
  value: any;
}

interface ComboboxProps {
  resource?: string;
  options?: Option[];
  value: any;
  onChange: (value: any) => void;
  placeholder?: string;
  displayField?: string;
  disabled?: boolean;
  extraFilters?: Record<string, any>;
}

const Combobox: React.FC<ComboboxProps> = ({
  resource,
  options,
  value,
  onChange,
  placeholder = "Select...",
  displayField = "name",
  disabled = false,
  extraFilters
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [dropdownStyles, setDropdownStyles] = useState<React.CSSProperties>({});
  const navigate = useNavigate();

  // Close when clicking outside
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

  // Update dropdown position when opened
  useEffect(() => {
    if (isOpen && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      const dropdownHeight = 300; // estimated max height
      
      const spaceBelow = windowHeight - rect.bottom;
      const showAbove = spaceBelow < dropdownHeight && rect.top > dropdownHeight;

      setDropdownStyles({
        position: 'fixed',
        top: showAbove ? 'auto' : `${rect.bottom + 8}px`,
        bottom: showAbove ? `${windowHeight - rect.top + 8}px` : 'auto',
        left: `${rect.left}px`,
        width: `${rect.width}px`,
        zIndex: 9999,
      });
    }
  }, [isOpen]);

  // Handle Scroll/Resize while open
  useEffect(() => {
    if (!isOpen) return;
    const updatePos = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDropdownStyles(prev => ({
          ...prev,
          top: prev.bottom === 'auto' ? `${rect.bottom + 8}px` : 'auto',
          bottom: prev.top === 'auto' ? `${window.innerHeight - rect.top + 8}px` : 'auto',
          left: `${rect.left}px`,
          width: `${rect.width}px`,
        }));
      }
    };
    window.addEventListener('scroll', updatePos, true);
    window.addEventListener('resize', updatePos);
    return () => {
      window.removeEventListener('scroll', updatePos, true);
      window.removeEventListener('resize', updatePos);
    };
  }, [isOpen]);

  // Fetch initial selected item if value exists (for resource-based lookups)
  useEffect(() => {
    if (resource && value && !selectedItem) {
      const fetchSelected = async () => {
        try {
          const cleanRes = cleanResourcePath(resource);
          const res = await api.get(`/${cleanRes}/${value}`);
          setSelectedItem(res.data);
        } catch (err) {
          console.error("Failed to fetch selected item", err);
        }
      };
      fetchSelected();
    } else if (options && value) {
      const opt = options.find(o => String(o.value) === String(value));
      if (opt) setSelectedItem({ [displayField]: opt.label, id: opt.value });
    } else if (!value) {
      setSelectedItem(null);
    }
  }, [value, resource, options, displayField]);

  // Fetch items based on search (for resource-based lookups)
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
      } catch (err) {
        console.error("Failed to fetch items", err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [search, resource, isOpen, disabled, extraFilters]);

  // Filter static options
  useEffect(() => {
    if (options) {
      const filtered = options.filter(opt => 
        opt.label.toLowerCase().includes(search.toLowerCase())
      ).map(opt => ({ [displayField]: opt.label, id: opt.value }));
      setItems(filtered);
    }
  }, [search, options, displayField]);

  const handleSelect = (item: any) => {
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
    if (disabled || !resource) return;
    const cleanRes = cleanResourcePath(resource);
    navigate(`/${cleanRes}/new`);
  };

  const dropdownMenu = (
    <div 
      ref={dropdownRef}
      style={dropdownStyles}
      className="bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-100"
    >
      <div className="p-2 border-b border-slate-100">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            autoFocus
            type="text"
            placeholder="Search..."
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border-none rounded-lg text-xs outline-none focus:ring-0"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="max-h-60 overflow-y-auto p-1">
        {loading ? (
          <div className="flex items-center justify-center p-6 text-slate-400">
            <Loader2 size={18} className="animate-spin mr-2" />
            <span className="text-xs font-medium">Searching...</span>
          </div>
        ) : items.length === 0 ? (
          <div className="p-6 text-center text-slate-400 text-xs italic">
            No results found.
          </div>
        ) : (
          items.map((item) => (
            <div 
              key={item.id}
              onClick={() => handleSelect(item)}
              className={`flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${String(value) === String(item.id) ? 'bg-indigo-50 text-indigo-700 font-bold' : 'hover:bg-slate-50 text-slate-700 font-medium'}`}
            >
              <span className="text-xs truncate">{item[displayField] || item.id}</span>
              {String(value) === String(item.id) && <Check size={14} />}
            </div>
          ))
        )}
      </div>

      {resource && (
        <div className="p-1 border-t border-slate-100 bg-slate-50/50">
          <button 
            onClick={handleAddNew}
            className="flex items-center gap-2 w-full px-3 py-2 text-indigo-600 hover:bg-indigo-50 rounded-lg text-xs font-bold transition-colors"
          >
            <Plus size={14} />
            <span>Add New {resource.split('/').pop()?.replace(/s$/, '').replace(/_/g, ' ')}</span>
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div className={`relative ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`} ref={containerRef}>
      <div 
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={`flex items-center justify-between w-full px-4 py-2.5 bg-slate-50 border rounded-xl text-sm transition-all ${disabled ? 'border-slate-200' : (isOpen ? 'border-indigo-500 ring-2 ring-indigo-500/10 cursor-pointer' : 'border-slate-200 hover:border-slate-300 cursor-pointer')}`}
      >
        <div className="flex-1 truncate">
          {selectedItem ? (
            <span className="text-slate-900 font-medium">{selectedItem[displayField] || selectedItem.id}</span>
          ) : (
            <span className="text-slate-400">{placeholder}</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {selectedItem && !disabled && (
            <button onClick={handleClear} className="p-1 hover:bg-slate-200 rounded-lg text-slate-400">
              <X size={14} />
            </button>
          )}
          <ChevronDown size={16} className={`text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </div>

      {isOpen && !disabled && createPortal(dropdownMenu, document.body)}
    </div>
  );
};

export default Combobox;


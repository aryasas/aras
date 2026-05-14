import React, { useState, useEffect, useRef } from 'react';
import api from '../../lib/api';
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

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch initial selected items if value exists
  useEffect(() => {
    if (value && value.length > 0 && selectedItems.length === 0) {
      const fetchSelected = async () => {
        try {
          // We could fetch them one by one or have a bulk API
          // For now, let's fetch individual if needed or assume we'll resolve labels elsewhere
          // Actually, for MultiSelect, we need the labels to display them in the tags.
          const promises = value.map(id => api.get(`/${resource}/${id}`));
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
  }, [value, resource]);

  // Fetch items based on search
  useEffect(() => {
    if (!isOpen || disabled) return;

    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        const params = {
          search: search || undefined,
          per_page: 20
        };
        const res = await api.get(`/${resource}/`, { params });
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

  return (
    <div className={`relative ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`} ref={containerRef}>
      <div 
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={`flex flex-wrap items-center gap-1.5 w-full min-h-[42px] px-3 py-1.5 bg-slate-50 border rounded-xl text-sm transition-all ${disabled ? 'border-slate-200' : (isOpen ? 'border-indigo-500 ring-2 ring-indigo-500/10 cursor-pointer' : 'border-slate-200 hover:border-slate-300 cursor-pointer')}`}
      >
        {selectedItems.length > 0 ? (
          selectedItems.map(item => (
            <span key={item.id} className="inline-flex items-center gap-1 px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-md text-xs font-bold">
              {item[displayField] || item.id}
              {!disabled && (
                <button 
                  onClick={(e) => handleRemove(e, item.id)}
                  className="hover:text-indigo-900"
                >
                  <X size={12} />
                </button>
              )}
            </span>
          ))
        ) : (
          <span className="text-slate-400 py-1">{placeholder}</span>
        )}
        <div className="flex-1" />
        <ChevronDown size={16} className={`text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </div>

      {isOpen && !disabled && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-100">
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
              items.map((item) => {
                const isSelected = value.includes(item.id);
                return (
                  <div 
                    key={item.id}
                    onClick={() => handleSelect(item)}
                    className={`flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${isSelected ? 'bg-indigo-50 text-indigo-700 font-bold' : 'hover:bg-slate-50 text-slate-700 font-medium'}`}
                  >
                    <span className="text-xs truncate">{item[displayField] || item.id}</span>
                    {isSelected && <Check size={14} />}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiSelectCombobox;

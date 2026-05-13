import React, { useState, useEffect, useRef } from 'react';
import api from '../../lib/api';
import { Search, Plus, Check, ChevronDown, X, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface ComboboxProps {
  resource: string;
  value: any;
  onChange: (value: any) => void;
  placeholder?: string;
  displayField?: string;
  disabled?: boolean;
}

const Combobox: React.FC<ComboboxProps> = ({ 
  resource, 
  value, 
  onChange, 
  placeholder = "Select...", 
  displayField = "name",
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

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

  // Fetch initial selected item if value exists
  useEffect(() => {
    if (value && !selectedItem) {
      const fetchSelected = async () => {
        try {
          const res = await api.get(`/${resource}/${value}`);
          setSelectedItem(res.data);
        } catch (err) {
          console.error("Failed to fetch selected item", err);
        }
      };
      fetchSelected();
    } else if (!value) {
      setSelectedItem(null);
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
    if (disabled) return;
    // Determine app from resource (assuming app_model format)
    const parts = resource.split('_');
    const app = parts[0];
    const model = parts.slice(1).join('_');
    navigate(`/${app}/${model}/new`);
  };

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
              items.map((item) => (
                <div 
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  className={`flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${value === item.id ? 'bg-indigo-50 text-indigo-700 font-bold' : 'hover:bg-slate-50 text-slate-700 font-medium'}`}
                >
                  <span className="text-xs truncate">{item[displayField] || item.id}</span>
                  {value === item.id && <Check size={14} />}
                </div>
              ))
            )}
          </div>

          <div className="p-1 border-t border-slate-100 bg-slate-50/50">
            <button 
              onClick={handleAddNew}
              className="flex items-center gap-2 w-full px-3 py-2 text-indigo-600 hover:bg-indigo-50 rounded-lg text-xs font-bold transition-colors"
            >
              <Plus size={14} />
              <span>Add New {resource.split('_').pop()?.replace(/s$/, '')}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Combobox;

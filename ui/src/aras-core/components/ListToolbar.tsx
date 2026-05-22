import React, { useState, useRef, useEffect } from 'react';
import {
  Search, Filter, Plus,
  Download, Upload, Settings, List, FileText, X, MoreHorizontal
  , Archive
} from 'lucide-react';

export type ViewMode = 'list' | 'tree' | 'report';

interface ListToolbarProps {
  title: string;
  search: string;
  onSearchChange: (value: string) => void;
  isFilterOpen: boolean;
  onFilterToggle: () => void;
  filterCount: number;
  selectedCount: number;
  onBulkEdit: () => void;
  onBulkDelete: () => void;
  onExport: () => void;
  isExporting: boolean;
  onImport: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onColumnPickerToggle: () => void;
  isColumnPickerOpen: boolean;
  onAdd: () => void;
  onArchive?: () => void;
  fields: any[];
  visibleColumns: string[];
  onVisibleColumnsChange: (columns: string[]) => void;
  viewMode?: ViewMode;
  onViewModeChange?: (mode: ViewMode) => void;
  hasTreeSupport?: boolean;
  onSaveFilter: () => void;
  onApplySavedFilter: (filterId: string) => void;
  onDeleteSavedFilter: (filterId: string) => void;
  savedFilters: { id: string; name: string; is_default: boolean }[];
}

export const ListToolbar: React.FC<ListToolbarProps> = ({
  title,
  search,
  onSearchChange,
  onFilterToggle,
  filterCount,
  onExport,
  isExporting,
  onImport,
  onColumnPickerToggle,
  onAdd,
  onArchive,
  viewMode = 'list',
  onViewModeChange
}) => {
  const [isActionsOpen, setIsActionsOpen] = useState(false);
  const actionsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (actionsRef.current && !actionsRef.current.contains(e.target as Node))
        setIsActionsOpen(false);
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  return (
    <div className="aras-list-toolbar flex flex-col md:flex-row items-center gap-3 bg-[var(--aras-panel)]/85 backdrop-blur-[16px] border border-[var(--aras-border)] p-2 rounded-[24px] shadow-sm mb-6 transition-all">
      {/* Add New Button on the left */}
      <button
        onClick={onAdd}
        className="flex h-11 items-center gap-2 px-6 bg-[var(--aras-accent)] text-white rounded-[18px] font-bold text-sm shadow-md hover:brightness-110 active:scale-95 transition-all whitespace-nowrap shrink-0 max-md:w-full justify-center"
      >
        <Plus size={18} />
        <span>Add New</span>
      </button>

      {/* Search Input Group */}
      <div className="relative flex-1 w-full min-w-[200px]">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
        <input
          type="text"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={`Search ${title}...`}
          className="w-full h-11 pl-12 pr-4 bg-slate-50/50 border border-transparent rounded-[18px] text-sm font-bold text-slate-700 outline-none focus:bg-white focus:border-[var(--aras-accent)] focus:ring-4 focus:ring-[var(--aras-accent)]/5 transition-all"
        />
        {search && (
          <button onClick={() => onSearchChange('')} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-600 p-1">
            <X size={14} />
          </button>
        )}
      </div>

      <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto hide-scroll pb-1 md:pb-0">
        {/* Filter Trigger */}
        <button
          onClick={onFilterToggle}
          className={`flex h-11 items-center gap-2 px-5 rounded-[18px] border font-bold text-sm transition-all whitespace-nowrap ${
            filterCount > 0
              ? 'bg-[var(--aras-accent)]/10 border-[var(--aras-accent)] text-[var(--aras-accent)] shadow-sm'
              : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
          }`}
        >
          <Filter size={18} />
          <span>Filters</span>
          {filterCount > 0 && (
            <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-[var(--aras-accent)] px-1.5 text-[10px] font-black text-white">
              {filterCount}
            </span>
          )}
        </button>

        {/* View Mode Switcher */}
        {onViewModeChange && (
          <div className="flex h-11 items-center border border-slate-200 rounded-[18px] bg-white overflow-hidden shrink-0">
            <button
              onClick={() => onViewModeChange('list')}
              className={`h-full px-3 flex items-center transition-colors ${viewMode === 'list' ? 'bg-slate-50 text-[var(--aras-accent)]' : 'text-slate-400 hover:bg-slate-50'}`}
              title="List View"
            >
              <List size={18} />
            </button>
            <button
              onClick={() => onViewModeChange('report')}
              className={`h-full px-3 flex items-center border-l border-slate-100 transition-colors ${viewMode === 'report' ? 'bg-slate-50 text-[var(--aras-accent)]' : 'text-slate-400 hover:bg-slate-50'}`}
              title="Report View"
            >
              <FileText size={18} />
            </button>
          </div>
        )}

        {/* More Actions Dropdown */}
        <div className="relative shrink-0" ref={actionsRef}>
          <button
            onClick={() => setIsActionsOpen(!isActionsOpen)}
            className="flex h-11 items-center gap-1.5 border border-slate-200 rounded-[18px] bg-white px-4 text-slate-600 hover:border-slate-300 transition-all font-bold text-sm"
          >
            <MoreHorizontal size={18} />
          </button>
          {isActionsOpen && (
            <div className="absolute right-0 top-full mt-3 w-56 bg-white border border-slate-200 rounded-2xl shadow-xl z-50 p-1.5 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
               <div className="px-3 py-2 text-[10px] font-black text-slate-400 uppercase tracking-widest border-b border-slate-50 mb-1">Actions</div>
               <button onClick={() => { onExport(); setIsActionsOpen(false); }} disabled={isExporting} className="flex items-center gap-2.5 w-full px-3 py-2.5 text-[13px] font-bold text-slate-700 hover:bg-slate-50 rounded-xl transition-colors">
                  <Download size={16} className="text-slate-400" /> Export CSV
               </button>
               <label className="flex items-center gap-2.5 w-full px-3 py-2.5 text-[13px] font-bold text-slate-700 hover:bg-slate-50 rounded-xl transition-colors cursor-pointer">
                  <Upload size={16} className="text-slate-400" /> Import CSV
                  <input type="file" accept=".csv" className="hidden" onChange={(e) => { onImport(e); setIsActionsOpen(false); }} />
               </label>
               {onArchive && (
                <button onClick={() => { onArchive(); setIsActionsOpen(false); }} className="flex items-center gap-2.5 w-full px-3 py-2.5 text-[13px] font-bold text-slate-700 hover:bg-slate-50 rounded-xl transition-colors">
                   <Archive size={16} className="text-slate-400" /> View Archive
                </button>
               )}
               <div className="mt-1 border-t border-slate-50 pt-1">
                 <button 
                  onClick={() => { onColumnPickerToggle(); setIsActionsOpen(false); }} 
                  className="flex items-center gap-2.5 w-full px-3 py-2.5 text-[13px] font-bold text-slate-700 hover:bg-slate-50 rounded-xl transition-colors"
                >
                    <Settings size={16} className="text-slate-400" /> Columns
                 </button>
               </div>

               <div className="absolute top-0 right-0 p-2 pointer-events-none">
                  {/* Just some empty space or decoration */}
               </div>

               {/* Column Picker Overlay (within dropdown for simplicity or absolute?) */}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ListToolbar;

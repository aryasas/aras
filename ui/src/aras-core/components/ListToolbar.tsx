import React, { useState, useRef, useEffect } from 'react';
import {
  Search, Filter, Plus, Edit3, Trash2,
  Download, Upload, Settings, List, LayoutGrid, FileText, ChevronDown, X, MoreHorizontal
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
  isFilterOpen,
  onFilterToggle,
  filterCount,
  selectedCount,
  onBulkEdit,
  onBulkDelete,
  onExport,
  isExporting,
  onImport,
  onColumnPickerToggle,
  isColumnPickerOpen,
  onAdd,
  onArchive,
  fields,
  visibleColumns,
  onVisibleColumnsChange,
  viewMode = 'list',
  onViewModeChange,
  hasTreeSupport = false,
  onSaveFilter,
  onApplySavedFilter,
  onDeleteSavedFilter,
  savedFilters
}) => {
  const [isSavedFiltersOpen, setIsSavedFiltersOpen] = useState(false);
  const [isActionsOpen, setIsActionsOpen] = useState(false);
  const savedFiltersRef = useRef<HTMLDivElement>(null);
  const actionsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (savedFiltersRef.current && !savedFiltersRef.current.contains(event.target as Node)) {
        setIsSavedFiltersOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (actionsRef.current && !actionsRef.current.contains(e.target as Node))
        setIsActionsOpen(false);
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  return (
    <div className="aras-list-toolbar p-0 pb-4 space-y-4">
      <div className="grid grid-cols-[auto_minmax(280px,1fr)_auto] items-center gap-3 max-lg:grid-cols-1">
        <button
          onClick={onAdd}
            className="flex h-[46px] items-center gap-2 px-[19px] bg-[var(--aras-button)] text-[var(--aras-button-text)] rounded-[var(--aras-radius)] text-sm font-bold transition-all shadow-md"
        >
          <Plus size={18} />
          <span>Add New</span>
        </button>

        <div className="flex min-w-0 flex-wrap items-center gap-3">

          {/* View Mode Switcher */}
          {onViewModeChange && (
            <div className="flex items-center bg-[var(--aras-panel-soft)] p-1 rounded-[var(--aras-radius)] border border-[var(--aras-border)]">
              <button
                onClick={() => onViewModeChange('list')}
                className={`p-1.5 rounded-lg transition-all ${viewMode === 'list' ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-500 hover:text-slate-700'}`}
                title="List View"
              >
                <List size={18} />
              </button>
              {hasTreeSupport && (
                <button
                  onClick={() => onViewModeChange('tree')}
                  className={`p-1.5 rounded-lg transition-all ${viewMode === 'tree' ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-500 hover:text-slate-700'}`}
                  title="Tree View"
                >
                  <LayoutGrid size={18} />
                </button>
              )}
              <button
                onClick={() => onViewModeChange('report')}
                className={`p-1.5 rounded-lg transition-all ${viewMode === 'report' ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-500 hover:text-slate-700'}`}
                title="Report View"
              >
                <FileText size={18} />
              </button>
            </div>
          )}

          <div className="relative min-w-[260px] flex-1 max-w-none">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--aras-muted)]" size={18} />
            <input
              type="text"
              placeholder={`Search in ${title}...`}
              className="h-[46px] w-full pl-10 pr-4 bg-[var(--aras-panel)] border border-[var(--aras-border-strong)] rounded-[var(--aras-radius)] text-[15px] text-[var(--aras-text)] focus:ring-2 focus:ring-[color:var(--aras-accent)]/15 focus:border-[var(--aras-accent)] outline-none transition-all"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
            />
          </div>
          <button
            onClick={onFilterToggle}
            className={`h-[46px] px-4 rounded-[var(--aras-radius)] border transition-all flex items-center gap-2 text-sm font-medium ${isFilterOpen ? 'bg-indigo-50 border-indigo-200 text-indigo-600' : 'bg-[var(--aras-panel)] border-[var(--aras-border-strong)] text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)]'}`}
          >
            <Filter size={18} />
            <span>Filters {filterCount > 0 && `(${filterCount})`}</span>
          </button>

          {filterCount > 0 && (
            <button
              onClick={onSaveFilter}
              className="p-2 rounded-xl border transition-all flex items-center gap-2 text-sm font-medium bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            >
              <Plus size={18} />
              <span>Save Filter</span>
            </button>
          )}

          {savedFilters && savedFilters.length > 0 && (
            <div className="relative" ref={savedFiltersRef}>
              <button
                onClick={() => setIsSavedFiltersOpen(!isSavedFiltersOpen)}
                className="p-2 rounded-xl border transition-all flex items-center gap-2 text-sm font-medium bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
              >
                <span>Saved Filters</span>
                <ChevronDown size={18} />
              </button>
              {isSavedFiltersOpen && (
                <div
                  className="absolute right-0 mt-3 w-64 bg-white border border-slate-200 shadow-xl rounded-2xl z-50 p-4"
                  onClick={(e) => e.stopPropagation()}
                >
                  <h4 className="text-xs font-bold text-slate-400 uppercase mb-3">Saved Filters</h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {savedFilters.map(sf => (
                      <div key={sf.id} className="flex items-center justify-between group">
                        <button
                          onClick={() => { onApplySavedFilter(sf.id); setIsSavedFiltersOpen(false); }}
                          className="flex-1 text-left text-sm text-slate-700 hover:text-indigo-600 p-1 rounded-lg transition-colors"
                        >
                          {sf.name} {sf.is_default && <span className="text-[10px] text-slate-400">(default)</span>}
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); onDeleteSavedFilter(sf.id); }}
                          className="p-1 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                          title="Delete saved filter"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-end gap-2">
          {selectedCount > 0 && (
            <>
              <button
                onClick={onBulkEdit}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-xl text-sm font-bold hover:bg-indigo-100 transition-all"
              >
                <Edit3 size={18} />
                <span>Edit ({selectedCount})</span>
              </button>
              <button
                onClick={onBulkDelete}
                className="flex items-center gap-2 px-4 py-2 bg-rose-50 text-rose-600 rounded-xl text-sm font-bold hover:bg-rose-100 transition-all"
              >
                <Trash2 size={18} />
                <span>Delete ({selectedCount})</span>
              </button>
            </>
          )}

          <div className="relative" ref={actionsRef}>
            <button
              onClick={() => setIsActionsOpen(v => !v)}
              className="flex h-[46px] items-center gap-1.5 border border-[var(--aras-border-strong)] rounded-[var(--aras-radius)] px-4 text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)] text-sm"
              title="Actions"
            >
              <MoreHorizontal size={18} />
              <ChevronDown size={14} />
            </button>
            {isActionsOpen && (
              <div className="absolute right-0 top-full mt-1 w-48 bg-white border border-slate-200 rounded-xl shadow-lg z-30 overflow-hidden">
                <button
                  onClick={() => { onExport(); setIsActionsOpen(false); }}
                  disabled={isExporting}
                  className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
                >
                  <Download size={15} /> Export CSV
                </button>
                <label className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 cursor-pointer">
                  <Upload size={15} /> Import CSV
                  <input type="file" accept=".csv" className="hidden" onChange={(e) => { onImport(e); setIsActionsOpen(false); }} />
                </label>
                {onArchive && (
                  <button
                    onClick={() => { onArchive(); setIsActionsOpen(false); }}
                    className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
                  >
                    <Archive size={15} /> View Archive
                  </button>
                )}
              </div>
            )}
          </div>

          <button
            className="relative grid h-[46px] w-[46px] place-items-center border border-[var(--aras-border-strong)] rounded-[var(--aras-radius)] text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)]"
            onClick={onColumnPickerToggle}
          >
            <Settings size={18} />
            {isColumnPickerOpen && (
              <div
                className="absolute right-0 mt-3 w-64 bg-white border border-slate-200 shadow-xl rounded-2xl z-50 p-4"
                onClick={(e) => e.stopPropagation()}
              >
                <h4 className="text-xs font-bold text-slate-400 uppercase mb-3">Visible Columns</h4>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {fields.map(f => (
                    <label key={f.name} className="flex items-center gap-2 cursor-pointer hover:bg-slate-50 p-1 rounded-lg">
                      <input
                        type="checkbox"
                        checked={visibleColumns.includes(f.name)}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          onVisibleColumnsChange(
                            checked ? [...visibleColumns, f.name] : visibleColumns.filter(c => c !== f.name)
                          )
                        }}
                        className="rounded text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="text-sm text-slate-700">{f.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </button>

        </div>
      </div>
    </div>
  );
};

export default ListToolbar;

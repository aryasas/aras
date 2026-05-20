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
          className="flex h-[46px] items-center gap-2 px-5 bg-[var(--aras-accent)] hover:opacity-90 text-white rounded-[var(--aras-radius)] text-sm font-semibold outline-none transition-opacity"
        >
          <Plus size={18} />
          <span>Add New</span>
        </button>

        <div className="flex min-w-0 flex-wrap items-center gap-3">

          {/* View Mode Switcher */}
          {onViewModeChange && (
            <div className="flex h-[46px] items-center border border-[var(--aras-border-strong)] rounded-[var(--aras-radius)] bg-[var(--aras-panel)] overflow-hidden">
              <button
                onClick={() => onViewModeChange('list')}
                className={`h-full px-2.5 flex items-center transition-colors ${viewMode === 'list' ? 'bg-[var(--aras-panel-soft)] text-[var(--aras-accent)]' : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)]'}`}
                title="List View"
                aria-pressed={viewMode === 'list'}
              >
                <List size={18} />
              </button>
              {hasTreeSupport && (
                <button
                  onClick={() => onViewModeChange('tree')}
                  className={`h-full px-2.5 flex items-center border-l border-[var(--aras-border)] transition-colors ${viewMode === 'tree' ? 'bg-[var(--aras-panel-soft)] text-[var(--aras-accent)]' : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)]'}`}
                  title="Tree View"
                  aria-pressed={viewMode === 'tree'}
                >
                  <LayoutGrid size={18} />
                </button>
              )}
              <button
                onClick={() => onViewModeChange('report')}
                className={`h-full px-2.5 flex items-center border-l border-[var(--aras-border)] transition-colors ${viewMode === 'report' ? 'bg-[var(--aras-panel-soft)] text-[var(--aras-accent)]' : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)]'}`}
                title="Report View"
                aria-pressed={viewMode === 'report'}
              >
                <FileText size={18} />
              </button>
            </div>
          )}

          <div className="relative min-w-[260px] flex-1 max-w-none group">
            <label htmlFor="list-search-input" className="sr-only">Search in {title}</label>
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--aras-muted)]" size={18} />
            <input
              id="list-search-input"
              type="text"
              placeholder={`Search in ${title}...`}
              className="h-[46px] w-full pl-10 pr-4 bg-[var(--aras-panel)] border border-[var(--aras-border-strong)] rounded-[var(--aras-radius)] text-[14px] text-[var(--aras-text)] placeholder:text-[var(--aras-muted)] focus:outline-none transition-colors"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              aria-label={`Search in ${title}`}
            />
          </div>
          <button
            onClick={onFilterToggle}
            className={`h-[46px] px-4 rounded-[var(--aras-radius)] border transition-colors flex items-center gap-2 text-sm font-medium ${isFilterOpen ? 'border-[var(--aras-accent)] text-[var(--aras-accent)] bg-[var(--aras-panel)]' : 'bg-[var(--aras-panel)] border-[var(--aras-border-strong)] text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)]'}`}
            aria-expanded={isFilterOpen}
            aria-controls="filter-conditions-panel"
          >
            <Filter size={18} />
            <span>Filters {filterCount > 0 && `(${filterCount})`}</span>
          </button>

          {filterCount > 0 && (
            <button
              onClick={onSaveFilter}
              className="h-[46px] px-4 rounded-[var(--aras-radius)] border transition-colors flex items-center gap-2 text-sm font-medium bg-[var(--aras-panel)] border-[var(--aras-border-strong)] text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)]"
            >
              <Plus size={18} />
              <span>Save Filter</span>
            </button>
          )}

          {savedFilters && savedFilters.length > 0 && (
            <div className="relative" ref={savedFiltersRef}>
              <button
                onClick={() => setIsSavedFiltersOpen(!isSavedFiltersOpen)}
                className="h-[46px] px-4 rounded-[var(--aras-radius)] border transition-colors flex items-center gap-2 text-sm font-medium bg-[var(--aras-panel)] border-[var(--aras-border-strong)] text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)]"
              >
                <span>Saved Filters</span>
                <ChevronDown size={18} />
              </button>
              {isSavedFiltersOpen && (
                <div
                  className="absolute right-0 mt-2 w-64 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-[var(--aras-radius)] z-50 p-3"
                  onClick={(e) => e.stopPropagation()}
                >
                  <h4 className="text-[11px] font-semibold text-[var(--aras-muted)] uppercase tracking-wider mb-2 px-1">Saved Filters</h4>
                  <div className="space-y-1 max-h-60 overflow-y-auto">
                    {savedFilters.map(sf => (
                      <div key={sf.id} className="flex items-center justify-between group">
                        <button
                          onClick={() => { onApplySavedFilter(sf.id); setIsSavedFiltersOpen(false); }}
                          className="flex-1 text-left text-sm text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)] px-2 py-1.5 rounded-[var(--aras-radius)] transition-colors"
                        >
                          {sf.name} {sf.is_default && <span className="text-[10px] text-[var(--aras-muted)]">(default)</span>}
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); onDeleteSavedFilter(sf.id); }}
                          className="p-1 text-[var(--aras-muted)] hover:text-rose-500 rounded-[var(--aras-radius)] transition-colors opacity-0 group-hover:opacity-100"
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
                className="flex h-[46px] items-center gap-2 px-4 rounded-[var(--aras-radius)] text-sm font-medium border border-[var(--aras-border-strong)] bg-[var(--aras-panel)] text-[var(--aras-accent)] hover:bg-[var(--aras-panel-soft)] transition-colors"
              >
                <Edit3 size={18} />
                <span>Edit ({selectedCount})</span>
              </button>
              <button
                onClick={onBulkDelete}
                className="flex h-[46px] items-center gap-2 px-4 rounded-[var(--aras-radius)] text-sm font-medium border border-[var(--aras-border-strong)] bg-[var(--aras-panel)] text-rose-600 hover:bg-rose-50 transition-colors"
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
              <div className="absolute right-0 top-full mt-2 w-48 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-[var(--aras-radius)] z-30 overflow-hidden">
                <button
                  onClick={() => { onExport(); setIsActionsOpen(false); }}
                  disabled={isExporting}
                  className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)]"
                >
                  <Download size={15} /> Export CSV
                </button>
                <label className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)] cursor-pointer">
                  <Upload size={15} /> Import CSV
                  <input type="file" accept=".csv" className="hidden" onChange={(e) => { onImport(e); setIsActionsOpen(false); }} />
                </label>
                {onArchive && (
                  <button
                    onClick={() => { onArchive(); setIsActionsOpen(false); }}
                    className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)]"
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
                className="absolute right-0 top-full mt-2 w-64 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-[var(--aras-radius)] z-50 p-3"
                onClick={(e) => e.stopPropagation()}
              >
                <h4 className="text-[11px] font-semibold text-[var(--aras-muted)] uppercase tracking-wider mb-2 px-1">Visible Columns</h4>
                <div className="space-y-1 max-h-60 overflow-y-auto">
                  {fields.map(f => (
                    <label key={f.name} className="flex items-center gap-2 cursor-pointer hover:bg-[var(--aras-panel-soft)] px-2 py-1.5 rounded-[var(--aras-radius)]">
                      <input
                        type="checkbox"
                        checked={visibleColumns.includes(f.name)}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          onVisibleColumnsChange(
                            checked ? [...visibleColumns, f.name] : visibleColumns.filter(c => c !== f.name)
                          )
                        }}
                        className="accent-[var(--aras-accent)]"
                      />
                      <span className="text-sm text-[var(--aras-text)]">{f.label}</span>
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

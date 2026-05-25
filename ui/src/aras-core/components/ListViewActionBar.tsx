import React, { useEffect, useRef, useState } from 'react';
import {
  Archive, ChevronDown, Download, Edit3, FileText, Filter, LayoutGrid,
  List, MoreHorizontal, Plus, Search, Settings, Trash2, Upload, X
} from 'lucide-react';
import { DesignContainer } from './design/DesignContainer';
import { DesignElement } from './design/DesignElement';

export type ViewMode = 'list' | 'tree' | 'report';

interface ListViewActionBarProps {
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

export const ListViewActionBar: React.FC<ListViewActionBarProps> = ({
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
  const [savedOpen, setSavedOpen] = useState(false);
  const [actionsOpen, setActionsOpen] = useState(false);
  const savedRef = useRef<HTMLDivElement>(null);
  const actionsRef = useRef<HTMLDivElement>(null);
  const columnsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDown = (event: MouseEvent) => {
      const target = event.target as Node;
      if (savedRef.current && !savedRef.current.contains(target)) setSavedOpen(false);
      if (actionsRef.current && !actionsRef.current.contains(target)) setActionsOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, []);

  const iconButton = `grid h-10 w-10 place-items-center rounded-[var(--app-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel)]/75 text-[var(--aras-muted)] transition-all hover:bg-[var(--aras-panel)] hover:text-[var(--aras-text)]`;
  const toolButton = `inline-flex h-10 items-center gap-2 rounded-[var(--app-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel)]/75 px-4 text-sm font-bold text-[var(--aras-text)] transition-all hover:bg-[var(--aras-panel)]`;

  return (
    <DesignContainer id="action-bar-layout" className="aras-list-action-bar glass-panel island mb-6 flex flex-col gap-3 p-4">
      <DesignContainer id="action-bar-top-row" className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <DesignContainer id="action-bar-left-group" className="flex shrink-0 items-center gap-2">
          <DesignElement id="btn-add-new" tagName="button" onClick={onAdd} className="inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-[var(--app-radius)] bg-[var(--aras-button)] px-6 text-sm font-extrabold text-[var(--aras-button-text)] transition-all hover:brightness-110 active:scale-[0.98]"><Plus size={17} />Add New</DesignElement>

          {selectedCount > 0 && (
            <div className="hidden items-center gap-1 rounded-[var(--app-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel-soft)] px-2 py-1 lg:flex">
              <span className="px-2 text-xs font-black text-[var(--aras-muted)]">{selectedCount} selected</span>
              <button type="button" onClick={onBulkEdit} className={iconButton} title={`Edit ${selectedCount} selected`}>
                <Edit3 size={16} />
              </button>
              <button type="button" onClick={onBulkDelete} className={`${iconButton} hover:text-rose-600`} title={`Delete ${selectedCount} selected`}>
                <Trash2 size={16} />
              </button>
            </div>
          )}
        </DesignContainer>

        <DesignContainer id="action-bar-right-group" className="flex flex-wrap items-center gap-2 lg:flex-1 lg:justify-end">
          <DesignElement id="search-box" className="relative w-full lg:w-64">
            <label htmlFor="list-search-input" className="sr-only">Search in {title}</label>
            <Search className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--aras-muted)]" size={17} />
            <input
              id="list-search-input"
              type="text"
              placeholder={`Search ${title}...`}
              className="h-10 w-full rounded-[var(--app-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel)]/75 pl-10 pr-4 text-sm font-semibold text-[var(--aras-text)] outline-none transition-all placeholder:text-[var(--aras-muted)] focus:bg-[var(--aras-panel)]"
              value={search}
              onChange={(event) => onSearchChange(event.target.value)}
            />
          </DesignElement>

          <button
            type="button"
            onClick={onFilterToggle}
            className={`${toolButton} ${isFilterOpen ? 'text-[var(--aras-accent)] bg-[var(--aras-panel)]' : ''}`}
            aria-expanded={isFilterOpen}
            aria-controls="filter-conditions-panel"
          >
          <Filter size={17} />
          Filter{filterCount > 0 ? ` ${filterCount}` : ''}
        </button>

        {filterCount > 0 && (
          <button type="button" onClick={onSaveFilter} className={iconButton} title="Save filter">
            <Plus size={17} />
          </button>
        )}

        {savedFilters.length > 0 && (
          <div className="relative" ref={savedRef}>
            <button type="button" onClick={() => setSavedOpen(!savedOpen)} className={toolButton}>
              Saved <ChevronDown size={15} />
            </button>
            {savedOpen && (
              <div className="absolute right-0 top-full z-50 mt-2 w-64 rounded-[1rem] border border-[var(--aras-border)] bg-[var(--aras-panel)] p-2 shadow-lg">
                {savedFilters.map((filter) => (
                  <div key={filter.id} className="group flex items-center gap-1 rounded-[var(--app-radius)] hover:bg-[var(--aras-panel-soft)]">
                    <button
                      type="button"
                      onClick={() => { onApplySavedFilter(filter.id); setSavedOpen(false); }}
                      className="min-w-0 flex-1 truncate px-3 py-2 text-left text-sm font-semibold text-[var(--aras-text)]"
                    >
                      {filter.name}{filter.is_default ? ' (default)' : ''}
                    </button>
                    <button
                      type="button"
                      onClick={(event) => { event.stopPropagation(); onDeleteSavedFilter(filter.id); }}
                      className="mr-1 grid h-7 w-7 place-items-center rounded-[var(--app-radius)] text-[var(--aras-muted)] opacity-0 transition-all hover:bg-rose-50 hover:text-rose-600 group-hover:opacity-100"
                      title="Delete saved filter"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {onViewModeChange && (
          <div className="flex h-10 overflow-hidden rounded-[var(--app-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel)]/75">
            <button type="button" onClick={() => onViewModeChange('list')} className={`grid w-10 place-items-center ${viewMode === 'list' ? 'bg-[var(--aras-panel)] text-[var(--aras-accent)]' : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel)]'}`} title="List view">
              <List size={17} />
            </button>
            {hasTreeSupport && (
              <button type="button" onClick={() => onViewModeChange('tree')} className={`grid w-10 place-items-center border-l border-[var(--aras-border)] ${viewMode === 'tree' ? 'bg-[var(--aras-panel)] text-[var(--aras-accent)]' : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel)]'}`} title="Tree view">
                <LayoutGrid size={17} />
              </button>
            )}
            <button type="button" onClick={() => onViewModeChange('report')} className={`grid w-10 place-items-center border-l border-[var(--aras-border)] ${viewMode === 'report' ? 'bg-[var(--aras-panel)] text-[var(--aras-accent)]' : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel)]'}`} title="Report view">
              <FileText size={17} />
            </button>
          </div>
        )}

        <div className="relative" ref={columnsRef}>
          <button type="button" className={iconButton} onClick={onColumnPickerToggle} title="Columns">
            <Settings size={17} />
          </button>
          {isColumnPickerOpen && (
            <div className="absolute right-0 top-full z-50 mt-2 w-64 rounded-[1rem] border border-[var(--aras-border)] bg-[var(--aras-panel)] p-3 shadow-lg">
              <div className="mb-2 px-1 text-[11px] font-extrabold uppercase tracking-widest text-[var(--aras-muted)]">Columns</div>
              <div className="max-h-64 space-y-1 overflow-y-auto">
                {fields.map((field) => (
                  <label key={field.name} className="flex cursor-pointer items-center gap-2 rounded-[var(--app-radius)] px-2 py-1.5 text-sm font-semibold text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)]">
                    <input
                      type="checkbox"
                      checked={visibleColumns.includes(field.name)}
                      onChange={(event) => {
                        onVisibleColumnsChange(
                          event.target.checked
                            ? [...visibleColumns, field.name]
                            : visibleColumns.filter((column) => column !== field.name)
                        );
                      }}
                      className="accent-[var(--aras-accent)]"
                    />
                    {field.label}
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="relative" ref={actionsRef}>
          <button type="button" onClick={() => setActionsOpen(!actionsOpen)} className={iconButton} title="More actions">
            <MoreHorizontal size={18} />
          </button>
          {actionsOpen && (
            <div className="absolute right-0 top-full z-50 mt-2 w-48 overflow-hidden rounded-[1rem] border border-[var(--aras-border)] bg-[var(--aras-panel)] shadow-lg">
              <button type="button" onClick={() => { onExport(); setActionsOpen(false); }} disabled={isExporting} className="flex w-full items-center gap-2 px-4 py-2.5 text-sm font-semibold text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)] disabled:opacity-50">
                <Download size={15} /> Export CSV
              </button>
              <label className="flex w-full cursor-pointer items-center gap-2 px-4 py-2.5 text-sm font-semibold text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)]">
                <Upload size={15} /> Import CSV
                <input type="file" accept=".csv" className="hidden" onChange={(event) => { onImport(event); setActionsOpen(false); }} />
              </label>
              {onArchive && (
                <button type="button" onClick={() => { onArchive(); setActionsOpen(false); }} className="flex w-full items-center gap-2 px-4 py-2.5 text-sm font-semibold text-[var(--aras-text)] hover:bg-[var(--aras-panel-soft)]">
                  <Archive size={15} /> View Archive
                </button>
              )}
            </div>
          )}
        </div>
        </DesignContainer>
      </DesignContainer>

      {selectedCount > 0 && (
        <div className="flex items-center justify-between rounded-[var(--app-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel-soft)] px-3 py-2 lg:hidden">
          <span className="text-xs font-black text-[var(--aras-muted)]">{selectedCount} selected</span>
          <div className="flex items-center gap-2">
            <button type="button" onClick={onBulkEdit} className={iconButton} title={`Edit ${selectedCount} selected`}>
              <Edit3 size={16} />
            </button>
            <button type="button" onClick={onBulkDelete} className={`${iconButton} hover:text-rose-600`} title={`Delete ${selectedCount} selected`}>
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      )}
    </DesignContainer>
  );
};

export default ListViewActionBar;

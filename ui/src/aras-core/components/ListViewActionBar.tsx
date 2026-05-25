// claude-opus-4-7
// ARC chip-strip toolbar: Filter button + active filter chips + right-side controls (Group / Columns / Export).
import React, { useEffect, useRef, useState } from 'react';
import {
  Archive, ChevronDown, Download, Edit3, FileText, Filter, LayoutGrid,
  List, MoreHorizontal, Plus, Search, Settings, Trash2, Upload, X
} from 'lucide-react';
import { DesignContainer } from './design/DesignContainer';
import { DesignElement } from './design/DesignElement';
import SimpleCombobox from './SimpleCombobox';

export type ViewMode = 'list' | 'tree' | 'report';

export interface FilterChip {
  label: string;
  onRemove?: () => void;
}

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
  // optional group-by
  groupField?: string | null;
  onGroupFieldChange?: (field: string | null) => void;
  groupableFields?: { name: string; label: string }[];
  // optional filter chips (active filter summary)
  filterChips?: FilterChip[];
  // pagination
  page?: number;
  perPage?: number;
  total?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  onPerPageChange?: (perPage: number) => void;
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
  savedFilters,
  groupField = null,
  onGroupFieldChange,
  groupableFields = [],
  filterChips = [],
  page,
  perPage,
  total,
  onPerPageChange,
}) => {
  const [savedOpen, setSavedOpen] = useState(false);
  const [actionsOpen, setActionsOpen] = useState(false);
  const [groupOpen, setGroupOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const savedRef = useRef<HTMLDivElement>(null);
  const actionsRef = useRef<HTMLDivElement>(null);
  const groupRef = useRef<HTMLDivElement>(null);
  const columnsRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDown = (event: MouseEvent) => {
      const target = event.target as Node;
      if (savedRef.current && !savedRef.current.contains(target)) setSavedOpen(false);
      if (actionsRef.current && !actionsRef.current.contains(target)) setActionsOpen(false);
      if (groupRef.current && !groupRef.current.contains(target)) setGroupOpen(false);
      if (searchRef.current && !searchRef.current.contains(target)) setSearchOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, []);

  const chip = "inline-flex items-center gap-1.5 h-7 px-2.5 rounded-full border border-[var(--line)] bg-transparent text-[12px] font-medium text-[var(--text-2)] hover:text-[var(--text)] hover:border-[var(--text-3)] transition-colors";
  const chipActive = "inline-flex items-center gap-1.5 h-7 px-2.5 rounded-full border border-[var(--accent)]/40 bg-[var(--accent)]/8 text-[12px] font-medium text-[var(--text)] transition-colors";
  const iconChip = "inline-flex items-center justify-center h-7 w-7 rounded-full border border-[var(--line)] text-[var(--text-3)] hover:text-[var(--text)] hover:border-[var(--text-3)] transition-colors";
  const groupLabel = (groupableFields.find((f) => f.name === groupField)?.label) || null;

  return (
    <DesignContainer id="action-bar-layout" className="aras-list-action-bar flex items-center gap-2 py-2 px-5 sm:px-7 lg:px-8 flex-wrap">
      {/* Left cluster: Filter + active chips + Add */}
      <DesignContainer id="action-bar-left-group" className="flex items-center gap-2 flex-wrap">
        <DesignElement id="btn-add-new" tagName="button" onClick={onAdd} className="inline-flex items-center gap-1.5 h-7 px-3 rounded-full bg-[var(--accent)] text-white text-[12px] font-semibold hover:brightness-110 transition-all">
          <Plus size={13} />New
        </DesignElement>

        <button
          type="button"
          onClick={onFilterToggle}
          className={isFilterOpen || filterCount > 0 ? chipActive : chip}
          aria-expanded={isFilterOpen}
          aria-controls="filter-conditions-panel"
        >
          <Filter size={12} />
          Filter{filterCount > 0 ? ` · ${filterCount}` : ''}
        </button>

        {filterChips.map((c, i) => (
          <span key={i} className={chipActive}>
            {c.label}
            {c.onRemove && (
              <button type="button" onClick={c.onRemove} className="opacity-60 hover:opacity-100">
                <X size={11} />
              </button>
            )}
          </span>
        ))}

        {filterCount > 0 && (
          <button type="button" onClick={onSaveFilter} className={iconChip} title="Save filter">
            <Plus size={12} />
          </button>
        )}

        {savedFilters.length > 0 && (
          <div className="relative" ref={savedRef}>
            <button type="button" onClick={() => setSavedOpen(!savedOpen)} className={chip}>
              Saved <ChevronDown size={11} />
            </button>
            {savedOpen && (
              <div className="absolute left-0 top-full z-50 mt-1.5 w-60 rounded-lg border border-[var(--line)] bg-[var(--surface)] p-1.5 shadow-lg">
                {savedFilters.map((filter) => (
                  <div key={filter.id} className="group flex items-center gap-1 rounded hover:bg-[var(--surface-2)]">
                    <button
                      type="button"
                      onClick={() => { onApplySavedFilter(filter.id); setSavedOpen(false); }}
                      className="min-w-0 flex-1 truncate px-2.5 py-1.5 text-left text-[12px] font-medium text-[var(--text)]"
                    >
                      {filter.name}{filter.is_default ? ' (default)' : ''}
                    </button>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); onDeleteSavedFilter(filter.id); }}
                      className="mr-1 grid h-6 w-6 place-items-center rounded text-[var(--text-3)] opacity-0 transition-all hover:text-rose-500 group-hover:opacity-100"
                      title="Delete saved filter"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {selectedCount > 0 && (
          <span className={chipActive}>
            {selectedCount} selected
            <button type="button" onClick={onBulkEdit} className="opacity-70 hover:opacity-100" title="Bulk edit">
              <Edit3 size={11} />
            </button>
            <button type="button" onClick={onBulkDelete} className="opacity-70 hover:opacity-100 hover:text-rose-500" title="Bulk delete">
              <Trash2 size={11} />
            </button>
          </span>
        )}
      </DesignContainer>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Right cluster: search + group + columns + view mode + more */}
      <DesignContainer id="action-bar-right-group" className="flex items-center gap-2 flex-wrap">
        <div className="relative" ref={searchRef}>
          {searchOpen || search ? (
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-3)]" size={12} />
              <input
                type="text"
                autoFocus
                placeholder={`Search ${title}...`}
                className="h-7 w-56 rounded-full border border-[var(--line)] bg-transparent pl-7 pr-7 text-[12px] text-[var(--text)] outline-none focus:border-[var(--accent)]"
                value={search}
                onChange={(e) => onSearchChange(e.target.value)}
              />
              {search && (
                <button onClick={() => { onSearchChange(''); setSearchOpen(false); }} className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-3)] hover:text-[var(--text)]">
                  <X size={12} />
                </button>
              )}
            </div>
          ) : (
            <button type="button" onClick={() => setSearchOpen(true)} className={iconChip} title="Search">
              <Search size={12} />
            </button>
          )}
        </div>

        {typeof total === 'number' && typeof page === 'number' && typeof perPage === 'number' && (
          <span className="text-[11.5px] text-[var(--text-3)] tabular-nums">
            <b className="text-[var(--text-2)]">{Math.min((page - 1) * perPage + 1, total)}–{Math.min(page * perPage, total)}</b> of <b className="text-[var(--text-2)]">{total.toLocaleString()}</b>
          </span>
        )}

        {onPerPageChange && typeof perPage === 'number' && (
          <SimpleCombobox
            options={[10, 20, 50, 100].map((n) => ({ label: `${n} / page`, value: n }))}
            value={perPage}
            onChange={(v) => onPerPageChange(Number(v))}
            title="Rows per page"
            align="right"
          />
        )}

        {onGroupFieldChange && groupableFields.length > 0 && (
          <div className="relative" ref={groupRef}>
            <button type="button" onClick={() => setGroupOpen(!groupOpen)} className={groupField ? chipActive : chip}>
              Group{groupLabel ? `: ${groupLabel}` : ''} <ChevronDown size={11} />
            </button>
            {groupOpen && (
              <div className="absolute right-0 top-full z-50 mt-1.5 w-52 rounded-lg border border-[var(--line)] bg-[var(--surface)] p-1.5 shadow-lg">
                <button
                  type="button"
                  onClick={() => { onGroupFieldChange(null); setGroupOpen(false); }}
                  className={`w-full text-left px-2.5 py-1.5 rounded text-[12px] font-medium ${!groupField ? 'text-[var(--accent)]' : 'text-[var(--text)]'} hover:bg-[var(--surface-2)]`}
                >
                  No grouping
                </button>
                {groupableFields.map((f) => (
                  <button
                    key={f.name}
                    type="button"
                    onClick={() => { onGroupFieldChange(f.name); setGroupOpen(false); }}
                    className={`w-full text-left px-2.5 py-1.5 rounded text-[12px] font-medium ${groupField === f.name ? 'text-[var(--accent)]' : 'text-[var(--text)]'} hover:bg-[var(--surface-2)]`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="relative" ref={columnsRef}>
          <button type="button" className={chip} onClick={onColumnPickerToggle} title="Columns">
            <Settings size={12} /> Columns
          </button>
          {isColumnPickerOpen && (
            <div className="absolute right-0 top-full z-50 mt-1.5 w-60 rounded-lg border border-[var(--line)] bg-[var(--surface)] p-2 shadow-lg">
              <div className="mb-1.5 px-1 text-[10px] font-extrabold uppercase tracking-widest text-[var(--text-3)]">Columns</div>
              <div className="max-h-64 space-y-0.5 overflow-y-auto">
                {fields.map((field) => (
                  <label key={field.name} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-[12px] font-medium text-[var(--text)] hover:bg-[var(--surface-2)]">
                    <input
                      type="checkbox"
                      checked={visibleColumns.includes(field.name)}
                      onChange={(e) => {
                        onVisibleColumnsChange(
                          e.target.checked
                            ? [...visibleColumns, field.name]
                            : visibleColumns.filter((c) => c !== field.name)
                        );
                      }}
                      className="accent-[var(--accent)]"
                    />
                    {field.label}
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        {onViewModeChange && (
          <div className="flex h-7 overflow-hidden rounded-full border border-[var(--line)]">
            <button type="button" onClick={() => onViewModeChange('list')} className={`grid w-7 place-items-center ${viewMode === 'list' ? 'text-[var(--accent)]' : 'text-[var(--text-3)] hover:text-[var(--text)]'}`} title="List">
              <List size={12} />
            </button>
            {hasTreeSupport && (
              <button type="button" onClick={() => onViewModeChange('tree')} className={`grid w-7 place-items-center border-l border-[var(--line)] ${viewMode === 'tree' ? 'text-[var(--accent)]' : 'text-[var(--text-3)] hover:text-[var(--text)]'}`} title="Tree">
                <LayoutGrid size={12} />
              </button>
            )}
            <button type="button" onClick={() => onViewModeChange('report')} className={`grid w-7 place-items-center border-l border-[var(--line)] ${viewMode === 'report' ? 'text-[var(--accent)]' : 'text-[var(--text-3)] hover:text-[var(--text)]'}`} title="Report">
              <FileText size={12} />
            </button>
          </div>
        )}

        <div className="relative" ref={actionsRef}>
          <button type="button" onClick={() => setActionsOpen(!actionsOpen)} className={iconChip} title="More">
            <MoreHorizontal size={13} />
          </button>
          {actionsOpen && (
            <div className="absolute right-0 top-full z-50 mt-1.5 w-44 overflow-hidden rounded-lg border border-[var(--line)] bg-[var(--surface)] shadow-lg">
              <button type="button" onClick={() => { onExport(); setActionsOpen(false); }} disabled={isExporting} className="flex w-full items-center gap-2 px-3 py-2 text-[12px] font-medium text-[var(--text)] hover:bg-[var(--surface-2)] disabled:opacity-50">
                <Download size={13} /> Export CSV
              </button>
              <label className="flex w-full cursor-pointer items-center gap-2 px-3 py-2 text-[12px] font-medium text-[var(--text)] hover:bg-[var(--surface-2)]">
                <Upload size={13} /> Import CSV
                <input type="file" accept=".csv" className="hidden" onChange={(e) => { onImport(e); setActionsOpen(false); }} />
              </label>
              {onArchive && (
                <button type="button" onClick={() => { onArchive(); setActionsOpen(false); }} className="flex w-full items-center gap-2 px-3 py-2 text-[12px] font-medium text-[var(--text)] hover:bg-[var(--surface-2)]">
                  <Archive size={13} /> View Archive
                </button>
              )}
            </div>
          )}
        </div>
      </DesignContainer>
    </DesignContainer>
  );
};

export default ListViewActionBar;

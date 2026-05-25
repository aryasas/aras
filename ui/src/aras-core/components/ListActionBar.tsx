import React from 'react';
import { Search, Filter, Plus, X } from 'lucide-react';

interface ListActionBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  onFilterToggle: () => void;
  filterCount: number;
  onAdd: () => void;
  resourceTitle: string;
}

export const ListActionBar: React.FC<ListActionBarProps> = ({
  search,
  onSearchChange,
  onFilterToggle,
  filterCount,
  onAdd,
  resourceTitle
}) => {
  return (
    <div className="flex flex-wrap items-center gap-3 bg-[var(--app-panel)] border border-[var(--app-border)] p-3 rounded-[var(--app-radius-lg)] shadow-[var(--shadow-premium)] mb-6">
      {/* Search Input Group */}
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--aras-muted)]" size={18} />
        <input
          type="text"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={`Search ${resourceTitle}...`}
          className="w-full h-11 pl-12 pr-4 bg-[var(--aras-panel-soft)] border border-[var(--aras-border)] rounded-[var(--app-radius)] text-sm font-bold text-[var(--aras-text)] outline-none focus:bg-[var(--aras-panel)] focus:border-[var(--aras-accent)] focus:ring-4 focus:ring-[var(--aras-accent)]/5 transition-all"
        />
        {search && (
          <button
            onClick={() => onSearchChange('')}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--aras-muted)] hover:text-[var(--aras-text)] p-1"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Filter Trigger */}
      <button
        onClick={onFilterToggle}
        className={`flex h-11 items-center gap-2 px-5 rounded-[var(--app-radius)] border font-bold text-sm transition-all ${
          filterCount > 0
            ? 'bg-[var(--aras-accent)]/10 border-[var(--aras-accent)] text-[var(--aras-accent)]'
            : 'bg-[var(--aras-panel)] border-[var(--aras-border)] text-[var(--aras-muted)] hover:border-[var(--aras-border-strong)]'
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

      {/* Add New Button */}
      <button
        onClick={onAdd}
        className="flex h-11 items-center gap-2 px-6 bg-[var(--aras-accent)] text-white rounded-[var(--app-radius)] font-bold text-sm shadow-md hover:brightness-110 active:scale-95 transition-all"
      >
        <Plus size={18} />
        <span className="hidden sm:inline">Add New</span>
      </button>
    </div>
  );
};

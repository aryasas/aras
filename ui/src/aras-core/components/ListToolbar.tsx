import React from 'react';
import { 
  Search, Filter, Plus, Edit3, Trash2, 
  Download, Upload, Settings 
} from 'lucide-react';

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
  fields: any[];
  visibleColumns: string[];
  onVisibleColumnsChange: (columns: string[]) => void;
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
  fields,
  visibleColumns,
  onVisibleColumnsChange
}) => {
  return (
    <div className="p-4 border-b border-slate-100 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1">
          <h2 className="text-xl font-bold text-slate-900 hidden md:block">{title}</h2>
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text" 
              placeholder={`Search in ${title}...`}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
            />
          </div>
          <button 
            onClick={onFilterToggle}
            className={`p-2 rounded-xl border transition-all flex items-center gap-2 text-sm font-medium ${isFilterOpen ? 'bg-indigo-50 border-indigo-200 text-indigo-600' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'}`}
          >
            <Filter size={18} />
            <span>Filters {filterCount > 0 && `(${filterCount})`}</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
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

          <button 
            onClick={onExport}
            disabled={isExporting}
            className="p-2 border border-slate-200 rounded-xl text-slate-600 hover:bg-slate-50 disabled:opacity-50"
            title="Export to CSV"
          >
            <Download size={18} className={isExporting ? 'animate-bounce' : ''} />
          </button>

          <label className="p-2 border border-slate-200 rounded-xl text-slate-600 hover:bg-slate-50 cursor-pointer" title="Import from CSV">
            <Upload size={18} />
            <input type="file" accept=".csv" className="hidden" onChange={onImport} />
          </label>
          
          <button 
            className="p-2 border border-slate-200 rounded-xl text-slate-600 hover:bg-slate-50 relative"
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

          <button 
            onClick={onAdd}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-bold hover:bg-indigo-700 transition-all shadow-md shadow-indigo-100"
          >
            <Plus size={18} />
            <span className="hidden sm:inline">Add New</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ListToolbar;

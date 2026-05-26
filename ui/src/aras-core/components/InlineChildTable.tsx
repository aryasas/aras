import React, { useEffect, useRef, useState } from 'react';
import { ExternalLink, Plus, Search, Settings, Trash2, X } from 'lucide-react';
import Combobox from './Combobox';
import { useNavigate } from 'react-router-dom';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { createDefaultRecord } from '../../lib/schemaUtils';

interface InlineChildTableProps {
  childResource: string;
  fkColumn: string;
  title?: string;
  parentId?: number | string;
  parentData?: any;
  rows: any[];
  onChange: (rows: any[]) => void;
  /** If true, show "Open as full list" shortcut button */
  allowFullList?: boolean;
}

const lookupCache = new Map<string, any[]>();

// claude-sonnet-4-6
export function invalidateInlineLookupCache(targetResource?: string) {
  if (targetResource) lookupCache.delete(cleanResourcePath(targetResource));
  else lookupCache.clear();
}

// claude-sonnet-4-6
function isEmptyUserRow(row: any, fields: any[]) {
  if (row.__aras_empty_row) return true;
  return fields.every((field) => {
    const value = row[field.name];
    return value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0);
  });
}

// claude-sonnet-4-6
export function filterEmptyChildRows(rows: any[], fields: any[]) {
  return rows.filter((row) => row.id || !isEmptyUserRow(row, fields));
}

// claude-sonnet-4-6
export const InlineChildTable: React.FC<InlineChildTableProps> = ({
  childResource,
  fkColumn,
  title,
  rows,
  onChange,
  allowFullList,
}) => {
  const [childMeta, setChildMeta] = useState<any>(null);
  const [visibleColumns, setVisibleColumns] = useState<string[]>([]);
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
  const [search, setSearch] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [columnPickerOpen, setColumnPickerOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const columnsRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const clean = cleanResourcePath(childResource);
    api.get(`/metadata/${clean}`).then(r => {
      setChildMeta(r.data);
      const cols = r.data.fields
        .filter((f: any) => !f.hidden && !f.form_hidden && !f.list_hidden && f.name !== fkColumn && f.type !== 'child_table')
        .map((f: any) => f.name);
      setVisibleColumns(cols);
    }).catch(() => {});
  }, [childResource, fkColumn]);

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      const t = e.target as Node;
      if (searchRef.current && !searchRef.current.contains(t)) setSearchOpen(false);
      if (columnsRef.current && !columnsRef.current.contains(t)) setColumnPickerOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, []);

  if (!childMeta) return null;

  const editableCols = childMeta.fields.filter((f: any) => !f.hidden && !f.form_hidden && f.name !== fkColumn && f.type !== 'child_table');
  const columnPickerCols = editableCols.filter((f: any) => !f.list_hidden);
  const visibleCols = editableCols.filter((f: any) => visibleColumns.includes(f.name));
  const validSelectedRows = new Set([...selectedRows].filter(idx => idx < rows.length));

  const filteredRows = rows
    .map((row, origIdx) => ({ row, origIdx }))
    .filter(({ row }) => !search.trim() || visibleCols.some((f: any) => {
      const v = String(row[`${f.name}_label`] ?? row[f.name] ?? '').toLowerCase();
      return v.includes(search.toLowerCase());
    }));

  const addRow = () => {
    const blank = { ...createDefaultRecord(editableCols), __aras_empty_row: true };
    onChange([...rows, blank]);
  };

  const deleteRow = (idx: number) => {
    setSelectedRows(prev => {
      const next = new Set<number>();
      prev.forEach(si => { if (si < idx) next.add(si); if (si > idx) next.add(si - 1); });
      return next;
    });
    onChange(rows.filter((_, i) => i !== idx));
  };

  const deleteSelectedRows = () => {
    if (validSelectedRows.size === 0) return;
    onChange(rows.filter((_, idx) => !validSelectedRows.has(idx)));
    setSelectedRows(new Set());
  };

  const toggleRowSelection = (idx: number) => {
    setSelectedRows(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx); else next.add(idx);
      return next;
    });
  };

  const allRowsSelected = rows.length > 0 && validSelectedRows.size === rows.length;
  const toggleAllRows = () => setSelectedRows(allRowsSelected ? new Set() : new Set(rows.map((_, i) => i)));

  const updateRow = (idx: number, patch: any) => {
    onChange(rows.map((row, i) => i === idx ? { ...row, ...patch, __aras_empty_row: false } : row));
  };

  const getColumnKind = (field: any) => {
    const name = String(field.name || '').toLowerCase();
    if (['qty', 'quantity'].includes(name)) return 'qty';
    if (['price', 'unit_price', 'rate'].includes(name)) return 'price';
    if (['total', 'amount', 'line_total'].includes(name)) return 'total';
    return 'description';
  };

  const formatMoney = (value: any) => {
    const num = Number(value ?? 0);
    return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const columnMinWidth = (field: any) => {
    const kind = getColumnKind(field);
    if (kind === 'qty') return 96;
    if (kind === 'price' || kind === 'total') return 144;
    return Math.max(180, Math.min(260, String(field.label || field.name || '').length * 11));
  };

  const tableMinWidth = Math.max(720, visibleCols.reduce((s: number, f: any) => s + columnMinWidth(f), 0) + 84);

  const chip = "inline-flex items-center gap-1.5 h-7 px-2.5 rounded-full border border-[var(--line)] bg-transparent text-[12px] font-medium text-[var(--text-2)] hover:text-[var(--text)] hover:border-[var(--text-3)] transition-colors";
  const iconChip = "inline-flex items-center justify-center h-7 w-7 rounded-full border border-[var(--line)] text-[var(--text-3)] hover:text-[var(--text)] hover:border-[var(--text-3)] transition-colors";
  const checkboxClass = "h-3.5 w-3.5 shrink-0 cursor-pointer rounded border-[var(--line-2)] bg-[var(--surface)] accent-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] focus:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-40";

  return (
    <div className="rounded border border-[var(--line)] overflow-hidden">
      {/* Toolbar — styled like ListViewActionBar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--line)] bg-[var(--surface-2)] flex-wrap">
        {/* Left cluster */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Add new */}
          <button
            type="button"
            onClick={addRow}
            className="inline-flex items-center gap-1.5 h-7 px-3 rounded-full bg-[var(--accent)] text-white text-[12px] font-semibold hover:brightness-110 transition-all"
          >
            <Plus size={13} /> Add row
          </button>

          {/* Bulk delete badge */}
          {validSelectedRows.size > 0 && (
            <span className="inline-flex items-center gap-1.5 h-7 px-2.5 rounded-full border border-[var(--accent)]/40 bg-[var(--accent)]/8 text-[12px] font-medium text-[var(--text)]">
              {validSelectedRows.size} selected
              <button
                type="button"
                onClick={deleteSelectedRows}
                className="opacity-70 hover:opacity-100 hover:text-rose-500"
                title="Delete selected"
              >
                <Trash2 size={11} />
              </button>
            </span>
          )}
        </div>

        <div className="flex-1" />

        {/* Right cluster */}
        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative" ref={searchRef}>
            {searchOpen || search ? (
              <div className="relative">
                <Search className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-3)]" size={12} />
                <input
                  type="text"
                  autoFocus
                  placeholder={`Search ${title || 'items'}...`}
                  className="h-7 w-44 rounded-full border border-[var(--line)] bg-transparent pl-7 pr-7 text-[12px] text-[var(--text)] outline-none focus:border-[var(--accent)]"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                {search && (
                  <button onClick={() => { setSearch(''); setSearchOpen(false); }} className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-3)] hover:text-[var(--text)]">
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

          {/* Column picker */}
          <div className="relative" ref={columnsRef}>
            <button type="button" className={chip} onClick={() => setColumnPickerOpen(!columnPickerOpen)} title="Columns">
              <Settings size={12} /> Columns
            </button>
            {columnPickerOpen && (
              <div className="absolute right-0 top-full z-50 mt-1.5 w-56 rounded-lg border border-[var(--line)] bg-[var(--surface)] p-2 shadow-lg">
                <div className="mb-1.5 px-1 text-[10px] font-extrabold uppercase tracking-widest text-[var(--text-3)]">Columns</div>
                <div className="max-h-56 space-y-0.5 overflow-y-auto">
                  {columnPickerCols.map((f: any) => (
                    <label key={f.name} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-[12px] font-medium text-[var(--text)] hover:bg-[var(--surface-2)]">
                      <input
                        type="checkbox"
                        checked={visibleColumns.includes(f.name)}
                        onChange={(e) => setVisibleColumns(
                          e.target.checked
                            ? [...visibleColumns, f.name]
                            : visibleColumns.filter((c) => c !== f.name)
                        )}
                        className={checkboxClass}
                      />
                      {f.label}
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Open as full list */}
          {allowFullList && (
            <button
              type="button"
              onClick={() => navigate(`/${cleanResourcePath(childResource)}`)}
              className={iconChip}
              title={`Open ${title || childResource} as full list`}
            >
              <ExternalLink size={12} />
            </button>
          )}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse" style={{ minWidth: tableMinWidth }}>
          <thead>
            <tr className="border-b border-[var(--line)] bg-[var(--surface-2)]">
              <th className="w-7 min-w-7 px-2 py-2 text-center">
                <input
                  type="checkbox"
                  checked={allRowsSelected}
                  onChange={toggleAllRows}
                  disabled={rows.length === 0}
                  aria-label="Select all rows"
                  className={checkboxClass}
                />
              </th>
              {visibleCols.map((f: any) => (
                <th
                  key={f.name}
                  style={{ minWidth: columnMinWidth(f) }}
                  className={`px-4 py-2 text-[10px] font-bold text-[var(--text-3)] uppercase tracking-[0.1em] whitespace-nowrap ${getColumnKind(f) !== 'description' ? 'text-right' : ''}`}
                >
                  {f.label}
                </th>
              ))}
              <th className="min-w-fit px-2 py-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--line)]">
            {filteredRows.length === 0 && (
              <tr>
                <td colSpan={visibleCols.length + 2} className="px-4 py-8 text-center text-[var(--text-3)] text-[12px] italic">
                  {search ? 'No items match your search.' : 'No items added.'}
                </td>
              </tr>
            )}
            {filteredRows.map(({ row, origIdx }) => {
              return (
                <tr key={origIdx} className="hover:bg-[var(--surface-2)]/40 transition-colors group">
                  <td className="w-7 min-w-7 px-2 py-2.5 text-center">
                    <input
                      type="checkbox"
                      checked={selectedRows.has(origIdx)}
                      onChange={() => toggleRowSelection(origIdx)}
                      aria-label={`Select row ${origIdx + 1}`}
                      className={checkboxClass}
                    />
                  </td>
                  {visibleCols.map((f: any) => {
                    const displayVal = row[`${f.name}_label`] ?? row[f.name];
                    const kind = getColumnKind(f);
                    return (
                      <td key={f.name} style={{ minWidth: columnMinWidth(f) }} className={`px-4 py-2.5 ${kind !== 'description' ? 'text-right' : ''}`}>
                        {kind === 'qty' ? (
                          <input
                            type="number"
                            value={row[f.name] ?? ''}
                            onChange={(e) => updateRow(origIdx, { [f.name]: e.target.value })}
                            className="w-16 text-right text-[12px] bg-transparent border-b border-[var(--line)] focus:border-[var(--accent)] outline-none py-0.5"
                          />
                        ) : kind === 'price' ? (
                          <input
                            type="number"
                            value={row[f.name] ?? ''}
                            onChange={(e) => updateRow(origIdx, { [f.name]: e.target.value })}
                            className="w-24 text-right text-[12px] bg-transparent border-b border-[var(--line)] focus:border-[var(--accent)] outline-none py-0.5"
                          />
                        ) : kind === 'total' ? (
                          <span className="text-[12px] font-semibold text-[var(--text)]">
                            {formatMoney(row[f.name])}
                          </span>
                        ) : f.type === 'lookup' ? (
                          <div style={{ minWidth: columnMinWidth(f) - 16 }}>
                            <Combobox
                              resource={f.target_resource || ''}
                              value={row[f.name]}
                              onChange={(val) => updateRow(origIdx, { [f.name]: val })}
                              placeholder="—"
                              variant="lookup"
                              field={f}
                              compact
                            />
                          </div>
                        ) : f.type === 'select' ? (
                          <div style={{ minWidth: columnMinWidth(f) - 16 }}>
                            <Combobox
                              options={f.options}
                              value={row[f.name]}
                              onChange={(val) => updateRow(origIdx, { [f.name]: val })}
                              placeholder="—"
                              variant="lookup"
                              field={f}
                              compact
                            />
                          </div>
                        ) : f.type === 'boolean' ? (
                          <input
                            type="checkbox"
                            checked={!!row[f.name]}
                            onChange={(e) => updateRow(origIdx, { [f.name]: e.target.checked })}
                            className={checkboxClass}
                          />
                        ) : f.type === 'date' || f.type === 'datetime' ? (
                          <input
                            type={f.type === 'datetime' ? 'datetime-local' : 'date'}
                            value={f.type === 'datetime'
                              ? (String(row[f.name] ?? '')).split('.')[0]
                              : (String(row[f.name] ?? '')).split('T')[0]}
                            onChange={(e) => updateRow(origIdx, { [f.name]: e.target.value })}
                            className="text-[12px] bg-transparent border-b border-[var(--line)] focus:border-[var(--accent)] outline-none py-0.5"
                          />
                        ) : (
                          <div className="flex flex-col">
                            <input
                              type="text"
                              value={displayVal ?? ''}
                              onChange={(e) => updateRow(origIdx, { [f.name]: e.target.value })}
                              className="text-[12px] text-[var(--text)] bg-transparent border-b border-transparent focus:border-[var(--accent)] outline-none py-0.5 w-full"
                              placeholder="—"
                            />
                            {f.name === 'description' && row.notes && <span className="text-[10.5px] text-[var(--text-3)]">{row.notes}</span>}
                          </div>
                        )}
                      </td>
                    );
                  })}
                  <td className="min-w-fit px-2 py-2.5 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="flex items-center justify-end gap-0.5">
                      {/* FK shortcuts — one per lookup field that has a value in this row */}
                      {visibleCols
                        .filter((f: any) => f.type === 'lookup' && f.target_resource && row[f.name])
                        .map((f: any) => (
                          <button
                            key={f.name}
                            type="button"
                            onClick={() => navigate(`/${cleanResourcePath(f.target_resource)}/${row[f.name]}`)}
                            title={`Open ${f.label}`}
                            className="h-6 px-1.5 flex items-center gap-1 rounded text-[10.5px] font-medium text-[var(--text-3)] hover:text-[var(--accent)] hover:bg-[color-mix(in_oklch,var(--accent)_10%,transparent)] transition-colors"
                          >
                            <ExternalLink size={11} />
                            <span className="hidden sm:inline">{f.label}</span>
                          </button>
                        ))}
                      <button
                        type="button"
                        onClick={() => deleteRow(origIdx)}
                        className="h-6 w-6 grid place-items-center rounded text-[var(--text-3)] hover:text-rose-600 hover:bg-rose-50 transition-colors"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

    </div>
  );
};

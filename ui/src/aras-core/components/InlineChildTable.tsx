import React, { useEffect, useState } from 'react';
import { Pencil, Plus, Trash2, X } from 'lucide-react';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { resolveFieldComponent } from '../SchemaRegistry';
import { createDefaultRecord } from '../../lib/schemaUtils';

interface InlineChildTableProps {
  childResource: string;
  fkColumn: string;
  title?: string;
  parentId?: number | string;
  parentData?: any;
  rows: any[];
  onChange: (rows: any[]) => void;
}

const lookupCache = new Map<string, any[]>();

export function invalidateInlineLookupCache(targetResource?: string) {
  if (targetResource) lookupCache.delete(cleanResourcePath(targetResource));
  else lookupCache.clear();
}

function isEmptyUserRow(row: any, fields: any[]) {
  if (row.__aras_empty_row) return true;
  return fields.every((field) => {
    const value = row[field.name];
    return value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0);
  });
}

export function filterEmptyChildRows(rows: any[], fields: any[]) {
  return rows.filter((row) => row.id || !isEmptyUserRow(row, fields));
}

export const InlineChildTable: React.FC<InlineChildTableProps> = ({
  childResource,
  fkColumn,
  title,
  rows,
  onChange
}) => {
  const [childMeta, setChildMeta] = useState<any>(null);
  const [visibleColumns, setVisibleColumns] = useState<string[]>([]);
  const [editingRow, setEditingRow] = useState<{ idx: number; data: any } | null>(null);

  useEffect(() => {
    const clean = cleanResourcePath(childResource);
    api.get(`/metadata/${clean}`).then(r => {
      setChildMeta(r.data);
      setVisibleColumns(r.data.fields.filter((f: any) => !f.hidden && !f.form_hidden && !f.list_hidden && f.name !== fkColumn && f.type !== 'child_table').map((f: any) => f.name));
    }).catch(() => {});
  }, [childResource, fkColumn]);

  if (!childMeta) return null;

  const editableCols = childMeta.fields.filter((f: any) => !f.hidden && !f.form_hidden && f.name !== fkColumn && f.type !== 'child_table');
  const visibleCols = editableCols.filter((f: any) => visibleColumns.includes(f.name));

  const addRow = () => {
    const blank = { ...createDefaultRecord(editableCols), __aras_empty_row: true };
    onChange([...rows, blank]);
  };

  const deleteRow = (idx: number) => {
    onChange(rows.filter((_, i) => i !== idx));
  };

  const updateRow = (idx: number, patch: any) => {
    const updated = rows.map((row, i) => i === idx ? { ...row, ...patch, __aras_empty_row: false } : row);
    onChange(updated);
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
    const labelLength = String(field.label || field.name || '').length;
    return Math.max(180, Math.min(260, labelLength * 11));
  };

  const tableMinWidth = Math.max(
    760,
    visibleCols.reduce((sum: number, field: any) => sum + columnMinWidth(field), 0) + 84
  );

  return (
    <div className="aras-island mt-6 overflow-hidden">
      <div className="aras-child-table-toolbar flex items-center justify-between gap-4 border-b border-[var(--aras-border)] bg-[var(--aras-panel)]/45 px-5 py-4">
        <h3 className="text-sm font-extrabold uppercase tracking-[0.16em] text-[var(--aras-muted)]">
          {title || childMeta.title}
        </h3>
        <button
          type="button"
          onClick={addRow}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-700 rounded-xl text-sm font-bold hover:bg-emerald-100 transition-colors"
        >
          <Plus size={16} />
          <span>Add Row</span>
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="aras-line-items-table w-full text-left border-collapse" style={{ minWidth: tableMinWidth }}>
          <thead>
            <tr className="bg-[var(--aras-table-head)] border-b border-[var(--aras-border)]">
              {visibleCols.map((f: any) => (
                <th
                  key={f.name}
                  style={{ minWidth: columnMinWidth(f) }}
                  className={`whitespace-nowrap px-5 py-3 text-xs font-bold text-[var(--aras-muted)] uppercase tracking-wider ${getColumnKind(f) !== 'description' ? 'text-right' : ''}`}
                >
                  {f.label}
                </th>
              ))}
              <th className="w-20 min-w-20 px-5 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--aras-border)]">
            {rows.length === 0 && (
              <tr>
                <td colSpan={visibleCols.length + 1} className="px-6 py-10 text-center text-[var(--aras-muted)] text-sm italic">
                  No items added.
                </td>
              </tr>
            )}
            {rows.map((row, idx) => (
              <tr key={idx} className="hover:bg-[var(--aras-panel-soft)]/60 transition-colors group">
                {visibleCols.map((f: any) => {
                  const displayVal = row[`${f.name}_label`] ?? row[f.name];
                  const kind = getColumnKind(f);

                  return (
                    <td key={f.name} style={{ minWidth: columnMinWidth(f) }} className={`px-5 py-3 ${kind !== 'description' ? 'text-right' : ''}`}>
                      {kind === 'qty' ? (
                        <input
                          type="number"
                          value={row[f.name] ?? ''}
                          onChange={(event) => updateRow(idx, { [f.name]: event.target.value })}
                          className="aras-line-qty"
                        />
                      ) : kind === 'price' ? (
                        <input
                          type="number"
                          value={row[f.name] ?? ''}
                          onChange={(event) => updateRow(idx, { [f.name]: event.target.value })}
                          className="aras-line-price"
                        />
                      ) : kind === 'total' ? (
                        <span className="font-mono font-black text-emerald-600 text-base">
                          {formatMoney(row[f.name])}
                        </span>
                      ) : (
                        <div className="flex flex-col">
                          <input
                            type="text"
                            value={displayVal ?? ''}
                            onChange={(event) => updateRow(idx, { [f.name]: event.target.value })}
                            className="aras-line-description"
                          />
                          {f.name === 'description' && row.notes && <span className="text-[11px] text-slate-400">{row.notes}</span>}
                        </div>
                      )}
                    </td>
                  );
                })}
                <td className="w-20 min-w-20 px-5 py-4 text-right opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                   <div className="flex items-center justify-end gap-1">
                      <button
                        type="button"
                        onClick={() => setEditingRow({ idx, data: { ...row } })}
                        className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all"
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        type="button"
                        onClick={() => deleteRow(idx)}
                        className="p-1.5 text-rose-300 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-all"
                      >
                        <Trash2 size={14} />
                      </button>
                   </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editingRow && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/20 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Edit Line Item</h3>
              <button onClick={() => setEditingRow(null)} className="p-2 hover:bg-slate-200 rounded-xl transition-colors"><X size={18} /></button>
            </div>
            <div className="p-6 grid grid-cols-1 gap-5">
              {editableCols.map((f: any) => {
                const Component = resolveFieldComponent(f);
                return (
                  <div key={f.name} className="flex flex-col gap-1.5">
                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">{f.label}</label>
                    <div className="aras-form-control-wrapper">
                      <Component
                        field={f}
                        value={editingRow.data[f.name]}
                        onChange={(val: any) => setEditingRow(prev => prev ? { ...prev, data: { ...prev.data, [f.name]: val } } : null)}
                        formData={editingRow.data}
                        disabled={f.read_only}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="px-6 py-4 bg-slate-50/80 border-t border-slate-100 flex justify-end gap-3">
              <button onClick={() => setEditingRow(null)} className="px-5 py-2 text-sm font-bold text-slate-500 hover:text-slate-700 transition-colors">Cancel</button>
              <button
                onClick={() => {
                   updateRow(editingRow.idx, editingRow.data);
                   setEditingRow(null);
                }}
                className="px-6 py-2 bg-[var(--aras-accent)] text-white text-sm font-bold rounded-xl shadow-md hover:brightness-110 active:scale-95 transition-all"
              >
                Apply Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

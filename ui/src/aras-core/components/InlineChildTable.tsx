import React, { useEffect, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { resolveFieldComponent } from '../SchemaRegistry';
import Combobox from './Combobox';
import { createDefaultRecord } from '../../lib/schemaUtils';

interface InlineChildTableProps {
  childResource: string;
  fkColumn: string;
  parentId?: number | string;
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
  rows,
  onChange
}) => {
  const [childMeta, setChildMeta] = useState<any>(null);
  const [search, setSearch] = useState('');
  const [visibleColumns, setVisibleColumns] = useState<string[]>([]);
  const [isColumnPickerOpen, setIsColumnPickerOpen] = useState(false);
  const [selectedRows, setSelectedRows] = useState<number[]>([]);
  const [editingCell, setEditingCell] = useState<{ rowIndex: number; fieldName: string } | null>(null);
  const [editingValue, setEditingValue] = useState<any>('');

  useEffect(() => {
    const clean = cleanResourcePath(childResource);
    api.get(`/metadata/${clean}`).then(r => {
      setChildMeta(r.data);
      setVisibleColumns(r.data.fields.filter((f: any) => !f.hidden && !f.form_hidden && f.name !== fkColumn && f.type !== 'child_table').map((f: any) => f.name));
    }).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [childResource, fkColumn]);

  if (!childMeta) {
    return <div className="p-4 text-sm text-slate-400 animate-pulse">Loading...</div>;
  }

  const editableCols = childMeta.fields.filter((f: any) =>
    !f.hidden && !f.form_hidden && f.name !== fkColumn && f.type !== 'child_table'
  );

  const visibleCols = editableCols.filter((f: any) => visibleColumns.includes(f.name));

  const filteredRows = rows.filter(row => {
    if (!search) return true;
    return Object.values(row).some(val => 
      String(val).toLowerCase().includes(search.toLowerCase())
    );
  });

  const addRow = () => {
    const blank = { ...createDefaultRecord(editableCols), __aras_empty_row: true };
    onChange([...rows, blank]);
  };

  const deleteRow = (idx: number) => {
    onChange(rows.filter((_, i) => i !== idx));
  };

  const updateRow = (idx: number, col: string, val: any) => {
    const updated = rows.map((row, i) => i === idx ? { ...row, [col]: val, __aras_empty_row: false } : row);
    onChange(updated);
  };

  const deleteSelected = () => {
    if (selectedRows.length === 0) return;
    onChange(rows.filter((_, i) => !selectedRows.includes(i)));
    setSelectedRows([]);
  };

  const toggleSelected = (idx: number) => {
    setSelectedRows(prev => prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]);
  };

  const startEdit = (idx: number, field: any) => {
    if (field.read_only || !['text', 'string', 'number', 'currency', 'select', 'date'].includes(field.type)) return;
    setEditingCell({ rowIndex: idx, fieldName: field.name });
    setEditingValue(rows[idx]?.[field.name] ?? '');
  };

  const commitEdit = () => {
    if (!editingCell) return;
    const { rowIndex, fieldName } = editingCell;
    const field = editableCols.find((f: any) => f.name === fieldName);
    const coerced = field && (field.type === 'number' || field.type === 'currency')
      ? (editingValue === '' || editingValue === null ? null : Number(editingValue))
      : editingValue;
    updateRow(rowIndex, fieldName, coerced);
    setEditingCell(null);
  };

  const cancelEdit = () => {
    setEditingCell(null);
    setEditingValue('');
  };

  return (
    <div className="bg-white overflow-hidden rounded-3xl border border-slate-200 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 p-4">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-bold text-slate-900">{childMeta.title}</h3>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search rows..."
            className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={addRow} className="flex items-center gap-2 rounded-xl bg-indigo-600 px-3 py-2 text-xs font-bold text-white hover:bg-indigo-700">
            <Plus size={14} />
            Add Row
          </button>
          <button type="button" onClick={deleteSelected} disabled={selectedRows.length === 0} className="flex items-center gap-2 rounded-xl bg-rose-50 px-3 py-2 text-xs font-bold text-rose-600 hover:bg-rose-100 disabled:opacity-40">
            <Trash2 size={14} />
            Delete Selected
          </button>
          <button type="button" onClick={() => setIsColumnPickerOpen(!isColumnPickerOpen)} className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50">
            Columns
          </button>
        </div>
        {isColumnPickerOpen && (
          <div className="basis-full rounded-xl border border-slate-200 bg-slate-50 p-3">
            <div className="flex flex-wrap gap-3">
              {editableCols.map((field: any) => (
                <label key={field.name} className="flex items-center gap-2 text-xs font-medium text-slate-600">
                  <input
                    type="checkbox"
                    checked={visibleColumns.includes(field.name)}
                    onChange={(e) => setVisibleColumns(e.target.checked ? [...visibleColumns, field.name] : visibleColumns.filter(col => col !== field.name))}
                  />
                  {field.label}
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50/50 border-b border-slate-100">
              <th className="w-10 px-4 py-3" />
              {visibleCols.map((f: any) => (
                <th key={f.name} className="px-6 py-3 text-left text-[11px] font-bold text-slate-500 uppercase tracking-wider whitespace-nowrap">
                  {f.label}
                </th>
              ))}
              <th className="w-12 px-6 py-3" />
            </tr>
          </thead>
          <tbody>
            {filteredRows.length === 0 && (
              <tr>
                <td colSpan={visibleCols.length + 2} className="px-6 py-12 text-center text-slate-400 text-sm italic bg-slate-50/30">
                  {search ? 'No results found' : 'No rows yet — click Add Row'}
                </td>
              </tr>
            )}
            {filteredRows.map((row) => {
              const idx = rows.indexOf(row);
              return (
              <tr key={idx} className="border-b border-slate-100 last:border-0 hover:bg-slate-50/30 transition-colors group">
                <td className="px-4 py-3 align-middle">
                  <input type="checkbox" checked={selectedRows.includes(idx)} onChange={() => toggleSelected(idx)} />
                </td>
                {visibleCols.map((f: any) => {
                  const Component = resolveFieldComponent(f);
                  const displayVal = row[`${f.name}_label`] ?? row[f.name];
                  const isEditing = editingCell?.rowIndex === idx && editingCell.fieldName === f.name;
                  return (
                    <td key={f.name} className="px-4 py-3 align-top min-w-[200px]" onClick={() => startEdit(idx, f)}>
                      <div className="relative">
                        {isEditing ? (
                          f.type === 'select' && f.options ? (
                            <select
                              autoFocus
                              value={editingValue ?? ''}
                              onChange={(e) => setEditingValue(e.target.value)}
                              onBlur={commitEdit}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') commitEdit();
                                if (e.key === 'Escape') cancelEdit();
                              }}
                              className="w-full rounded-xl border border-indigo-200 bg-white px-3 py-2 text-sm outline-none ring-2 ring-indigo-100"
                            >
                              {f.options.map((option: any) => <option key={option.value} value={option.value}>{option.label}</option>)}
                            </select>
                          ) : (
                            <input
                              autoFocus
                              type={f.type === 'number' || f.type === 'currency' ? 'number' : f.type === 'date' ? 'date' : 'text'}
                              value={editingValue ?? ''}
                              onChange={(e) => setEditingValue(e.target.value)}
                              onBlur={commitEdit}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') commitEdit();
                                if (e.key === 'Escape') cancelEdit();
                              }}
                              className="w-full rounded-xl border border-indigo-200 bg-white px-3 py-2 text-sm outline-none ring-2 ring-indigo-100"
                            />
                          )
                        ) : f.type === 'lookup' && f.target_resource ? (
                          f.read_only ? (
                            <span className="block px-4 py-2.5 text-sm text-slate-700">
                              {displayVal ?? ''}
                            </span>
                          ) : (
                            <InlineLookupCombobox
                              field={f}
                              value={row[f.name]}
                              onChange={(val) => updateRow(idx, f.name, val)}
                            />
                          )
                        ) : (
                          <Component
                            field={f}
                            value={row[f.name]}
                            onChange={(val: any) => updateRow(idx, f.name, val)}
                            formData={row}
                            disabled={false}
                          />
                        )}
                      </div>
                    </td>
                  );
                })}
                <td className="px-4 py-3 align-middle text-center opacity-50 group-hover:opacity-100 transition-opacity">
                  <button
                    type="button"
                    onClick={() => deleteRow(idx)}
                    className="p-2 text-rose-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
                    title="Remove row"
                  >
                    <Trash2 size={16} />
                  </button>
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

function getLookupLabel(item: any) {
  return item?.name ?? item?.code ?? item?.label ?? item?.id ?? '';
}

const InlineLookupCombobox: React.FC<{
  field: any;
  value: any;
  onChange: (value: any) => void;
}> = ({ field, value, onChange }) => {
  const [options, setOptions] = useState<Array<{ label: string; value: any }>>([]);

  useEffect(() => {
    if (!field.target_resource) return;
    const clean = cleanResourcePath(field.target_resource);
    const cached = lookupCache.get(clean);
    if (cached) {
      setOptions(cached.map((item: any) => ({
        label: String(getLookupLabel(item)),
        value: item.id
      })));
      return;
    }
    api.get(`/${clean}`, { params: { per_page: 200 } })
      .then(res => {
        const items = res.data?.items ?? res.data ?? [];
        lookupCache.set(clean, items);
        setOptions(items.map((item: any) => ({
          label: String(getLookupLabel(item)),
          value: item.id
        })));
      })
      .catch(() => setOptions([]));
  }, [field.target_resource]);

  return (
    <Combobox
      options={options}
      value={value}
      onChange={onChange}
      placeholder={`Select ${field.label}...`}
    />
  );
};

import React, { useEffect, useState } from 'react';
import { Pencil, Plus, Trash2, X } from 'lucide-react';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { resolveFieldComponent } from '../SchemaRegistry';
import Combobox from './Combobox';
import { createDefaultRecord } from '../../lib/schemaUtils';

interface InlineChildTableProps {
  childResource: string;
  fkColumn: string;
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
  parentId,
  parentData,
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
  const [editingRow, setEditingRow] = useState<{ idx: number; data: any } | null>(null);

  useEffect(() => {
    const clean = cleanResourcePath(childResource);
    api.get(`/metadata/${clean}`).then(r => {
      const fields = applyChildFieldOverrides(r.data.fields, childResource);
      setChildMeta({ ...r.data, fields });
      setVisibleColumns(fields.filter((f: any) => !f.hidden && !f.form_hidden && f.name !== fkColumn && f.type !== 'child_table').map((f: any) => f.name));
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

  const updateRow = async (idx: number, col: string, val: any) => {
    let patch: Record<string, any> = { [col]: val, __aras_empty_row: false };

    if (isPaymentAllocationResource(childResource) && col === 'invoice_id') {
      patch.invoice_type = parentData?.payment_type === 'Outgoing' ? 'OutflowInvoice' : 'InflowInvoice';
    }

    // Auto-fill fields that depend_on this column
    const triggerField = editableCols.find((f: any) => f.name === col);
    const dependents = editableCols.filter((f: any) => f.depends_on === col && f.default_from);
    if (dependents.length && triggerField?.target_resource && val) {
      try {
        const clean = cleanResourcePath(triggerField.target_resource);
        const res = await api.get(`/${clean}/${val}`);
        const item = res.data?.item ?? res.data;
        if (item) {
          for (const dep of dependents) {
            if (item[dep.default_from] != null) patch[dep.name] = item[dep.default_from];
          }
        }
      } catch { /* silent */ }
    } else {
      for (const dep of dependents) patch[dep.name] = null;
    }

    const mergedRow = { ...rows[idx], ...patch };
    const amountFields = ['qty', 'unit_price', 'discount'];
    if (amountFields.some(f => f in patch)) {
      const qty = parseFloat(mergedRow.qty) || 0;
      const unitPrice = parseFloat(mergedRow.unit_price) || 0;
      const discount = parseFloat(mergedRow.discount) || 0;
      patch.amount = qty * (unitPrice - discount);
    }
    const updated = rows.map((row, i) => i === idx ? { ...row, ...patch } : row);
    onChange(updated);
  };

  const runRemoveAction = async (row: any) => {
    const removeAction = childMeta?.actions?.find((action: any) => action.name === 'deallocate');
    if (!row.id || !removeAction) return false;
    const clean = cleanResourcePath(childResource);
    await api.post(`/${clean}/${row.id}/action/${removeAction.name}`, {});
    return true;
  };

  const deleteSelected = async () => {
    if (selectedRows.length === 0) return;
    for (const idx of selectedRows) {
      await runRemoveAction(rows[idx]);
    }
    onChange(rows.filter((_, i) => !selectedRows.includes(i)));
    setSelectedRows([]);
  };

  const toggleSelected = (idx: number) => {
    setSelectedRows(prev => prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]);
  };

  const startEdit = (idx: number, field: any) => {
    if (field.read_only || field.type === 'async_select' || !['text', 'string', 'number', 'currency', 'select', 'date'].includes(field.type)) return;
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
    <div className="aras-child-table bg-white overflow-hidden rounded-3xl border border-slate-200 shadow-sm">
      <div className="flex min-h-[54px] flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-slate-50/50 backdrop-blur-sm px-6 py-4">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">{childMeta.title}</h3>
          <label htmlFor="child-table-search-input" className="sr-only">Search rows</label>
          <input
            id="child-table-search-input"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search rows..."
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-500/10 transition-all shadow-sm"
            aria-label="Search rows in child table"
          />
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={addRow} className="flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 px-4 py-2 text-xs font-bold text-white shadow-sm transition-all focus:ring-4 focus:ring-indigo-500/20">
            <Plus size={14} />
            Add Row
          </button>
          <button type="button" onClick={deleteSelected} disabled={selectedRows.length === 0} className="flex items-center gap-2 rounded-xl bg-rose-50 px-4 py-2 text-xs font-bold text-rose-600 hover:bg-rose-100 disabled:opacity-40 transition-colors">
            <Trash2 size={14} />
            Delete Selected
          </button>
          <button
            type="button"
            onClick={() => setIsColumnPickerOpen(!isColumnPickerOpen)}
            className="rounded-xl border border-slate-200 bg-white shadow-sm px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors"
            aria-expanded={isColumnPickerOpen}
            aria-controls="child-table-column-picker"
          >
            Columns
          </button>
        </div>
        {isColumnPickerOpen && (
          <div id="child-table-column-picker" className="basis-full rounded-[var(--aras-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel)] p-3">
            <div className="flex flex-wrap gap-3">
              {editableCols.map((field: any) => (
                <label key={field.name} className="flex items-center gap-2 text-xs font-medium text-slate-600">
                  <input
                    type="checkbox"
                    checked={visibleColumns.includes(field.name)}
                    onChange={(e) => setVisibleColumns(e.target.checked ? [...visibleColumns, field.name] : visibleColumns.filter(col => col !== field.name))}
                    className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                    aria-label={`Toggle visibility of ${field.label} column`}
                  />
                  {field.label}
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
      <div className="overflow-x-auto scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-100">
              <th className="w-10 px-6 py-4" />
              {visibleCols.map((f: any) => (
                <th key={f.name} className="px-6 py-4 text-left text-[11px] font-bold text-slate-500 uppercase tracking-wider whitespace-nowrap">
                  {f.label}
                </th>
              ))}
              <th className="w-12 px-6 py-4" />
            </tr>
          </thead>
          <tbody>
            {filteredRows.length === 0 && (
              <tr>
                <td colSpan={visibleCols.length + 2} className="px-6 py-16 text-center text-slate-400 text-sm italic bg-slate-50/10">
                  {search ? 'No results found' : 'No rows yet — click Add Row'}
                </td>
              </tr>
            )}
            {filteredRows.map((row) => {
              const idx = rows.indexOf(row);
              return (
              <tr key={idx} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50 transition-colors group">
                <td className="px-6 py-4 align-middle">
                  <input
                    type="checkbox"
                    checked={selectedRows.includes(idx)}
                    onChange={() => toggleSelected(idx)}
                    className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                  />
                </td>
                {visibleCols.map((f: any) => {
                  const Component = resolveFieldComponent(f);
                  const displayVal = row[`${f.name}_label`] ?? row[f.name];
                  const isEditing = editingCell?.rowIndex === idx && editingCell.fieldName === f.name;
                  return (
                    <td key={f.name} className="px-6 py-4 align-top min-w-[200px]" onClick={() => startEdit(idx, f)}>
                      <div className="relative">
                        {isEditing ? (
                          f.type === 'select' && f.options ? (
                            <Combobox
                              options={f.options}
                              value={editingValue}
                              onChange={(val) => {
                                setEditingValue(val);
                                // For select fields in inline table, we might want to commit immediately on change
                                // but standard behavior is commit on blur/enter.
                              }}
                              placeholder={`Select...`}
                            />
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
                              className="w-full h-9 px-3 bg-[var(--aras-panel)] border border-[var(--aras-accent)] rounded-[var(--aras-radius)] text-xs outline-none ring-2 ring-[var(--aras-accent)]/10"
                            />
                          )
                        ) : f.type === 'async_select' && f.choices_url ? (
                          f.read_only ? (
                            <span className="block px-4 py-2.5 text-sm text-slate-700 font-medium">
                              {displayVal ?? ''}
                            </span>
                          ) : (
                            <InlineAsyncSelect
                              field={f}
                              parentId={parentId}
                              value={row[f.name]}
                              fallbackLabel={row.invoice_number ?? displayVal}
                              onChange={(val) => updateRow(idx, f.name, val)}
                            />
                          )
                        ) : f.type === 'lookup' && f.target_resource ? (
                          f.read_only ? (
                            <span className="block px-4 py-2.5 text-sm text-slate-700 font-medium">
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
                <td className="px-6 py-4 align-middle text-center opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                  <button
                    type="button"
                    onClick={() => setEditingRow({ idx, data: { ...row } })}
                    className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all"
                    title="Edit row"
                  >
                    <Pencil size={15} />
                  </button>
                  <button
                    type="button"
                    onClick={async () => {
                      await runRemoveAction(row);
                      deleteRow(idx);
                    }}
                    className="p-2 text-rose-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-all"
                    title={childMeta.actions?.find((action: any) => action.name === 'deallocate')?.label ?? 'Remove row'}
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
      {editingRow && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-2xl max-h-[85vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-800">Edit Row</h3>
              <button onClick={() => setEditingRow(null)} className="p-2 hover:bg-slate-100 rounded-xl">
                <X size={18} />
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {childMeta?.fields?.filter((f: any) => !f.hidden && f.name !== fkColumn).map((f: any) => {
                const Component = resolveFieldComponent(f);
                return (
                  <div key={f.name} className="flex flex-col gap-1.5">
                    <label className="text-sm font-bold text-slate-700">{f.label}</label>
                    <Component
                      field={f}
                      value={editingRow.data[f.name]}
                      onChange={(val: any) => setEditingRow(prev => prev ? { ...prev, data: { ...prev.data, [f.name]: val } } : null)}
                      formData={editingRow.data}
                      disabled={f.read_only}
                    />
                  </div>
                );
              })}
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setEditingRow(null)} className="px-4 py-2 text-sm rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50">Cancel</button>
              <button
                onClick={() => {
                  const next = [...rows];
                  next[editingRow.idx] = { ...rows[editingRow.idx], ...editingRow.data };
                  onChange(next);
                  setEditingRow(null);
                }}
                className="px-4 py-2 text-sm rounded-xl bg-indigo-600 text-white hover:bg-indigo-700"
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function isPaymentAllocationResource(resource: string) {
  return cleanResourcePath(resource).includes('payment-allocations');
}

function applyChildFieldOverrides(fields: any[], childResource: string) {
  if (!isPaymentAllocationResource(childResource)) return fields;
  return fields.map((field: any) => {
    if (field.name === 'invoice_type') return { ...field, read_only: true };
    if (field.name === 'invoice_id') {
      return {
        ...field,
        type: 'async_select',
        choices_url: '/api/erp/accounting/payments/{parent_id}/open_invoices',
        display_field: 'number',
      };
    }
    return field;
  });
}

function resolveChoicesUrl(url: string, parentId?: number | string) {
  const withParent = url.replace('{parent_id}', parentId == null ? '' : String(parentId));
  return cleanResourcePath(withParent)
    .replace(/^api\/v1\//, '')
    .replace(/^api\//, '');
}

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

const InlineAsyncSelect: React.FC<{
  field: any;
  parentId?: number | string;
  value: any;
  fallbackLabel?: any;
  onChange: (value: any) => void;
}> = ({ field, parentId, value, fallbackLabel, onChange }) => {
  const [options, setOptions] = useState<Array<{ label: string; value: any }>>([]);

  useEffect(() => {
    if (!field.choices_url || parentId == null) {
      setOptions([]);
      return;
    }

    const url = resolveChoicesUrl(field.choices_url, parentId);
    api.get(`/${url}`)
      .then(res => {
        const items = res.data?.items ?? res.data ?? [];
        const displayField = field.display_field ?? 'name';
        setOptions(items.map((item: any) => ({
          label: String(item[displayField] ?? item.name ?? item.id),
          value: item.id,
        })));
      })
      .catch(() => setOptions([]));
  }, [field.choices_url, field.display_field, parentId]);

  const selectedIsMissing = value != null && !options.some(option => String(option.value) === String(value));
  const mergedOptions = selectedIsMissing
    ? [{ label: String(fallbackLabel || value), value }, ...options]
    : options;

  return (
    <Combobox
      options={mergedOptions}
      value={value}
      onChange={onChange}
      placeholder={`Select ${field.label}...`}
      disabled={parentId == null}
    />
  );
};

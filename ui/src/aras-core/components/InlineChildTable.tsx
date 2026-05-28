import React, { useEffect, useState } from 'react';
import { ExternalLink, Trash2 } from 'lucide-react';
import { ArasActionBar } from './ArasActionBar';
import ArasTable from './ArasTable';
import type { ArasTableColumn } from './ArasTable';
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
  const [lookupOptions, setLookupOptions] = useState<Record<string, Array<{ label: string; value: string | number }>>>({});
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
    if (!childMeta) return;
    const lookupFields = childMeta.fields.filter((f: any) => f.type === 'lookup' && f.target_resource);
    lookupFields.forEach((field: any) => {
      const cleanTarget = cleanResourcePath(field.target_resource);
      const cached = lookupCache.get(cleanTarget);
      if (cached) {
        setLookupOptions(prev => ({ ...prev, [field.name]: cached.map(item => ({ label: item.name || item.title || item.number || String(item.id), value: item.id })) }));
        return;
      }
      api.get(`/${cleanTarget}`, { params: { per_page: 200 } })
        .then((res) => {
          const items = res.data.items || [];
          lookupCache.set(cleanTarget, items);
          setLookupOptions(prev => ({ ...prev, [field.name]: items.map((item: any) => ({ label: item.name || item.title || item.number || String(item.id), value: item.id })) }));
        })
        .catch(() => {});
    });
  }, [childMeta]);

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

  const cbClass = "h-3.5 w-3.5 shrink-0 cursor-pointer rounded accent-[var(--accent)]";

  // claude-sonnet-4-6
  const tableColumns: ArasTableColumn[] = [
    {
      key: '__sel',
      label: '',
      width: 32,
      sortable: false,
      render: (_val, _row, i) => {
        const origIdx = filteredRows[i]?.origIdx ?? i;
        return (
          <input
            type="checkbox"
            checked={selectedRows.has(origIdx)}
            onChange={() => toggleRowSelection(origIdx)}
            className={cbClass}
            onClick={(e) => e.stopPropagation()}
          />
        );
      },
    },
    ...visibleCols.map((f: any): ArasTableColumn => {
      const kind = getColumnKind(f);
      return {
        key: f.name,
        label: f.label,
        field: f.name,
        align: kind !== 'description' ? 'right' : 'left',
        minWidth: columnMinWidth(f),
        sortable: false,
        render: (_val, row, i) => {
          const origIdx = filteredRows[i]?.origIdx ?? i;
          const displayVal = row[`${f.name}_label`] ?? row[f.name];
          if (kind === 'qty') return (
            <input type="number" value={row[f.name] ?? ''} onChange={(e) => updateRow(origIdx, { [f.name]: e.target.value })}
              className="w-16 text-right text-[12px] bg-transparent border-b border-[var(--line)] focus:border-[var(--accent)] outline-none py-0.5" />
          );
          if (kind === 'price') return (
            <input type="number" value={row[f.name] ?? ''} onChange={(e) => updateRow(origIdx, { [f.name]: e.target.value })}
              className="w-24 text-right text-[12px] bg-transparent border-b border-[var(--line)] focus:border-[var(--accent)] outline-none py-0.5" />
          );
          if (kind === 'total') return (
            <span className="text-[12px] font-semibold text-[var(--text)]">{formatMoney(row[f.name])}</span>
          );
          if (f.type === 'lookup') return (
            <Combobox resource={f.target_resource || ''} value={row[f.name]}
              onChange={(val) => updateRow(origIdx, { [f.name]: val })}
              placeholder="—" variant="lookup" field={f} compact />
          );
          if (f.type === 'select') return (
            <Combobox options={f.options} value={row[f.name]}
              onChange={(val) => updateRow(origIdx, { [f.name]: val })}
              placeholder="—" variant="lookup" field={f} compact />
          );
          if (f.type === 'boolean') return (
            <input type="checkbox" checked={!!row[f.name]}
              onChange={(e) => updateRow(origIdx, { [f.name]: e.target.checked })} className={cbClass} />
          );
          if (f.type === 'date' || f.type === 'datetime') return (
            <input type={f.type === 'datetime' ? 'datetime-local' : 'date'}
              value={f.type === 'datetime' ? String(row[f.name] ?? '').split('.')[0] : String(row[f.name] ?? '').split('T')[0]}
              onChange={(e) => updateRow(origIdx, { [f.name]: e.target.value })}
              className="text-[12px] bg-transparent border-b border-[var(--line)] focus:border-[var(--accent)] outline-none py-0.5" />
          );
          return (
            <div className="flex flex-col">
              <input type="text" value={displayVal ?? ''} onChange={(e) => updateRow(origIdx, { [f.name]: e.target.value })}
                className="text-[12px] text-[var(--text)] bg-transparent border-b border-transparent focus:border-[var(--accent)] outline-none py-0.5 w-full" placeholder="—" />
              {f.name === 'description' && row.notes && <span className="text-[10.5px] text-[var(--text-3)]">{row.notes}</span>}
            </div>
          );
        },
      };
    }),
    {
      key: '__actions',
      label: '',
      align: 'right',
      sortable: false,
      render: (_val, row, i) => {
        const origIdx = filteredRows[i]?.origIdx ?? i;
        return (
          <div className="flex items-center justify-end gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
            {visibleCols.filter((f: any) => f.type === 'lookup' && f.target_resource && row[f.name]).map((f: any) => (
              <button key={f.name} type="button"
                onClick={(e) => { e.stopPropagation(); navigate(`/${cleanResourcePath(f.target_resource)}/${row[f.name]}`); }}
                title={`Open ${f.label}`}
                className="h-6 px-1.5 flex items-center gap-1 rounded text-[10.5px] font-medium text-[var(--text-3)] hover:text-[var(--accent)] hover:bg-[color-mix(in_oklch,var(--accent)_10%,transparent)] transition-colors">
                <ExternalLink size={11} />
              </button>
            ))}
            <button type="button" onClick={(e) => { e.stopPropagation(); deleteRow(origIdx); }}
              className="h-6 w-6 grid place-items-center rounded text-[var(--text-3)] hover:text-rose-600 hover:bg-rose-50 transition-colors">
              <Trash2 size={12} />
            </button>
          </div>
        );
      },
    },
  ];

  return (
    <div className="rounded border border-[var(--line)] overflow-hidden">
      <ArasActionBar
        variant="simple"
        title={title}
        onAdd={addRow}
        search={search}
        onSearchChange={setSearch}
        fields={columnPickerCols}
        visibleColumns={visibleColumns}
        onVisibleColumnsChange={setVisibleColumns}
        selectedCount={validSelectedRows.size}
        onBulkDelete={deleteSelectedRows}
        extra={allowFullList ? (
          <button type="button" onClick={() => navigate(`/${cleanResourcePath(childResource)}`)}
            className="inline-flex items-center justify-center h-7 w-7 rounded-full border border-[var(--line)] text-[var(--text-3)] hover:text-[var(--text)] hover:border-[var(--text-3)] transition-colors"
            title={`Open ${title || childResource} as full list`}>
            <ExternalLink size={12} />
          </button>
        ) : undefined}
      />
      <ArasTable
        columns={tableColumns}
        rows={filteredRows.map(fr => fr.row)}
        rowKey={(_row, i) => filteredRows[i]?.origIdx ?? i}
        minWidth={tableMinWidth}
        emptyMessage={search ? 'No items match your search.' : 'No items added.'}
      />
    </div>
  );
};

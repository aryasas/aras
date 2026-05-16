import React, { useEffect, useState } from 'react';
import { Trash2 } from 'lucide-react';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { resolveFieldComponent } from '../SchemaRegistry';
import ListToolbar from './ListToolbar';
import Combobox from './Combobox';

interface InlineChildTableProps {
  childResource: string;
  fkColumn: string;
  parentId?: number | string;
  rows: any[];
  onChange: (rows: any[]) => void;
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
    const today = new Date().toISOString().split('T')[0];
    const blank: any = {};
    editableCols.forEach((f: any) => {
      if (f.type === 'boolean') blank[f.name] = false;
      else if (f.type === 'number' || f.type === 'currency') blank[f.name] = 0;
      else if (f.type === 'date') blank[f.name] = today;
      else if (f.type === 'datetime') blank[f.name] = new Date().toISOString().split('.')[0];
      else blank[f.name] = '';
    });
    onChange([...rows, blank]);
  };

  const deleteRow = (idx: number) => {
    onChange(rows.filter((_, i) => i !== idx));
  };

  const updateRow = (idx: number, col: string, val: any) => {
    const updated = rows.map((row, i) => i === idx ? { ...row, [col]: val } : row);
    onChange(updated);
  };

  return (
    <div className="bg-white overflow-hidden rounded-3xl border border-slate-200 shadow-sm">
      <ListToolbar 
        title={childMeta.title}
        search={search}
        onSearchChange={setSearch}
        isFilterOpen={false}
        onFilterToggle={() => {}}
        filterCount={0}
        selectedCount={0}
        onBulkEdit={() => {}}
        onBulkDelete={() => {}}
        onExport={() => {}}
        isExporting={false}
        onImport={() => {}}
        onColumnPickerToggle={() => setIsColumnPickerOpen(!isColumnPickerOpen)}
        isColumnPickerOpen={isColumnPickerOpen}
        onAdd={addRow}
        fields={editableCols}
        visibleColumns={visibleColumns}
        onVisibleColumnsChange={setVisibleColumns}
      />
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50/50 border-b border-slate-100">
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
                <td colSpan={visibleCols.length + 1} className="px-6 py-12 text-center text-slate-400 text-sm italic bg-slate-50/30">
                  {search ? 'No results found' : 'No rows yet — click Add Row'}
                </td>
              </tr>
            )}
            {filteredRows.map((row) => {
              const idx = rows.indexOf(row);
              return (
              <tr key={idx} className="border-b border-slate-100 last:border-0 hover:bg-slate-50/30 transition-colors group">
                {visibleCols.map((f: any) => {
                  const Component = resolveFieldComponent(f);
                  const displayVal = row[`${f.name}_label`] ?? row[f.name];
                  return (
                    <td key={f.name} className="px-4 py-3 align-top min-w-[200px]">
                      <div className="relative">
                        {f.type === 'lookup' && f.target_resource ? (
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
    api.get(`/${clean}`, { params: { per_page: 200 } })
      .then(res => {
        const items = res.data?.items ?? res.data ?? [];
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

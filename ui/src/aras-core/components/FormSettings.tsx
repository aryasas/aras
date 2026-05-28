import React, { useMemo, useState } from 'react';
import { GripVertical, Save } from 'lucide-react';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { useAras } from '../hooks/useAras';

type TabKey = 'fields' | 'layout' | 'columns' | 'permissions';

interface FormSettingsProps {
  resource: string;
  metadata: any;
  visibleColumns?: string[];
  onVisibleColumnsChange?: (columns: string[]) => void;
}

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: 'fields', label: 'Fields' },
  { key: 'layout', label: 'Layout' },
  { key: 'columns', label: 'List Columns' },
  { key: 'permissions', label: 'Permissions' },
];

const normalizeLayout = (metadata: any) => {
  if (Array.isArray(metadata?.layout) && metadata.layout.length) return metadata.layout;
  return [{ title: 'Overview', fields: (metadata?.fields || []).filter((f: any) => !f.hidden).map((f: any) => f.name) }];
};

const FormSettings: React.FC<FormSettingsProps> = ({ resource, metadata, visibleColumns = [], onVisibleColumnsChange }) => {
  const [activeTab, setActiveTab] = useState<TabKey>('fields');
  const [layout, setLayout] = useState<any[]>(() => normalizeLayout(metadata));
  const [dragField, setDragField] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const { notify } = useAras();

  const fields = useMemo(() => metadata?.fields || [], [metadata]);

  const saveLayout = async () => {
    setSaving(true);
    try {
      const id = metadata?.resource_model_id || metadata?.id || cleanResourcePath(resource);
      await api.put(`/resource_model/${id}`, { layout });
      notify('Form layout saved', 'success');
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Failed to save form layout', 'error');
    } finally {
      setSaving(false);
    }
  };

  const moveFieldToSection = (sectionIndex: number, fieldName: string) => {
    setLayout((prev) => prev.map((section, idx) => {
      const nextFields = (section.fields || []).filter((name: string) => name !== fieldName);
      return idx === sectionIndex ? { ...section, fields: [...nextFields, fieldName] } : { ...section, fields: nextFields };
    }));
  };

  return (
    <div className="flex h-full flex-col gap-4 text-[13px] text-[var(--text)]">
      <div className="flex flex-wrap gap-1 rounded border border-[var(--line)] bg-[var(--surface-2)] p-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={`h-8 rounded px-3 text-[12px] font-semibold ${activeTab === tab.key ? 'bg-[var(--surface)] text-[var(--accent)] shadow-sm' : 'text-[var(--text-2)] hover:text-[var(--text)]'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'fields' && (
        <div className="space-y-2">
          {fields.map((field: any) => (
            <div key={field.name} className="rounded border border-[var(--line)] p-3">
              <div className="font-semibold">{field.label}</div>
              <div className="mt-2 grid grid-cols-2 gap-2 text-[12px] text-[var(--text-2)]">
                <label><input type="checkbox" checked={!!field.required} readOnly /> Required</label>
                <label><input type="checkbox" checked={!!field.hidden || !!field.form_hidden} readOnly /> Hidden</label>
                <label><input type="checkbox" checked={!!field.read_only} readOnly /> Read-only</label>
                <span>Default: {String(field.default ?? '-')}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'layout' && (
        <div className="flex flex-col gap-3">
          {layout.map((section, sectionIndex) => (
            <div
              key={`${section.title}-${sectionIndex}`}
              onDragOver={(event) => event.preventDefault()}
              onDrop={() => dragField && moveFieldToSection(sectionIndex, dragField)}
              className="min-h-24 rounded border border-dashed border-[var(--line)] p-3"
            >
              <input
                value={section.title || ''}
                onChange={(event) => setLayout((prev) => prev.map((s, i) => i === sectionIndex ? { ...s, title: event.target.value } : s))}
                className="mb-2 h-8 w-full rounded border border-[var(--line)] bg-[var(--surface)] px-2 text-[12px] font-semibold outline-none focus:border-[var(--accent)]"
              />
              <div className="flex flex-wrap gap-2">
                {(section.fields || []).map((name: string) => {
                  const field = fields.find((f: any) => f.name === name);
                  return (
                    <span key={name} draggable onDragStart={() => setDragField(name)} className="inline-flex cursor-grab items-center gap-1 rounded border border-[var(--line)] px-2 py-1 text-[12px]">
                      <GripVertical size={12} /> {field?.label || name}
                    </span>
                  );
                })}
              </div>
            </div>
          ))}
          <button type="button" onClick={() => setLayout([...layout, { title: 'Section', fields: [] }])} className="h-8 rounded border border-[var(--line)] text-[12px] font-semibold">
            Add section
          </button>
          <button type="button" onClick={saveLayout} disabled={saving} className="inline-flex h-8 items-center justify-center gap-2 rounded bg-[var(--accent)] px-3 text-[12px] font-semibold text-white disabled:opacity-60">
            <Save size={13} /> {saving ? 'Saving...' : 'Save layout'}
          </button>
        </div>
      )}

      {activeTab === 'columns' && (
        <div className="space-y-1">
          {fields.filter((f: any) => !f.hidden).map((field: any) => (
            <label key={field.name} className="flex items-center gap-2 rounded px-2 py-1.5 hover:bg-[var(--surface-2)]">
              <input
                type="checkbox"
                checked={visibleColumns.includes(field.name)}
                onChange={(event) => onVisibleColumnsChange?.(event.target.checked ? [...visibleColumns, field.name] : visibleColumns.filter((c) => c !== field.name))}
              />
              {field.label}
            </label>
          ))}
        </div>
      )}

      {activeTab === 'permissions' && (
        <div className="space-y-2">
          {fields.map((field: any) => (
            <div key={field.name} className="rounded border border-[var(--line)] p-3">
              <div className="font-semibold">{field.label}</div>
              <div className="mt-2 text-[12px] text-[var(--text-3)]">Per-role visibility is stored by field metadata when configured by the backend.</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FormSettings;

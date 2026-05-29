import React, { useMemo, useState } from 'react';
import { GripVertical, Plus, Save, Trash2 } from 'lucide-react';
import { DndContext, closestCenter, useDraggable, useDroppable, type DragEndEvent } from '@dnd-kit/core';
import { SortableContext, arrayMove, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { useAras } from '../hooks/useAras';
import { useAuthStore } from '../../store/authStore';

type TabKey = 'fields' | 'layout' | 'columns' | 'permissions';
type LayoutTab = { key?: string; title: string; fields: string[] };
type LayoutSection = { key?: string; title: string; fields: string[]; type?: string; tabs?: LayoutTab[] };

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

const normalizeLayout = (metadata: any): LayoutSection[] => {
  if (Array.isArray(metadata?.layout) && metadata.layout.length) {
    return metadata.layout.map((section: any, index: number) => ({
      key: section.key || `section-${index}`,
      title: section.title || 'Section',
      type: section.type,
      fields: Array.isArray(section.fields) ? section.fields : [],
      tabs: Array.isArray(section.tabs)
        ? section.tabs.map((tab: any, tabIndex: number) => ({
            key: tab.key || `tab-${index}-${tabIndex}`,
            title: tab.title || 'Tab',
            fields: Array.isArray(tab.fields) ? tab.fields : [],
          }))
        : [],
    }));
  }
  return [{ key: 'overview', title: 'Overview', fields: (metadata?.fields || []).filter((f: any) => !f.hidden).map((f: any) => f.name) }];
};

const withoutField = (layout: LayoutSection[], fieldName: string): LayoutSection[] =>
  layout.map((section) => ({
    ...section,
    fields: section.fields.filter((name) => name !== fieldName),
    tabs: (section.tabs || []).map((tab) => ({ ...tab, fields: tab.fields.filter((name) => name !== fieldName) })),
  }));

function SortableSection({ section, children }: { section: LayoutSection; children: React.ReactNode }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: `section-sort:${section.key}` });
  return (
    <section ref={setNodeRef} style={{ transform: CSS.Transform.toString(transform), transition }} className="rounded border border-[var(--line)] bg-[var(--surface)]">
      <div className="flex items-center gap-2 border-b border-[var(--line)] px-3 py-2">
        <button type="button" {...attributes} {...listeners} className="cursor-grab text-[var(--text-3)] hover:text-[var(--text)]" title="Drag section">
          <GripVertical size={14} />
        </button>
        {children}
      </div>
    </section>
  );
}

function DroppableFieldList({ id, children }: { id: string; children: React.ReactNode }) {
  const { setNodeRef, isOver } = useDroppable({ id });
  return (
    <div ref={setNodeRef} className={`min-h-16 rounded border border-dashed p-2 transition-colors ${isOver ? 'border-[var(--accent)] bg-[var(--surface-2)]' : 'border-[var(--line)]'}`}>
      {children}
    </div>
  );
}

function DraggableFieldChip({ name, label }: { name: string; label: string }) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: `field:${name}` });
  return (
    <span
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform) }}
      {...attributes}
      {...listeners}
      className="inline-flex cursor-grab items-center gap-1 rounded border border-[var(--line)] bg-[var(--surface)] px-2 py-1 text-[12px]"
    >
      <GripVertical size={12} /> {label}
    </span>
  );
}

const FormSettings: React.FC<FormSettingsProps> = ({ resource, metadata, visibleColumns = [], onVisibleColumnsChange }) => {
  const [activeTab, setActiveTab] = useState<TabKey>('fields');
  const [layout, setLayout] = useState<LayoutSection[]>(() => normalizeLayout(metadata));
  const [saving, setSaving] = useState(false);
  const [useOverride, setUseOverride] = useState(visibleColumns.length > 0);
  const { notify } = useAras();
  const user = useAuthStore((s) => s.user);

  const fields = useMemo(() => metadata?.fields || [], [metadata]);
  const fieldLabel = (name: string) => fields.find((field: any) => field.name === name)?.label || name;

  const saveLayout = async () => {
    setSaving(true);
    try {
      const id = metadata?.resource_model_id || metadata?.id || cleanResourcePath(resource);
      await api.put(`/resource_model/${id}`, { layout });
      await api.post('/dev/metadata/flush', { resource: cleanResourcePath(resource) });
      notify('Form layout saved', 'success');
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Failed to save form layout', 'error');
    } finally {
      setSaving(false);
    }
  };

  const canManageAdvanced = !!((user as any)?.is_superuser || user?.is_admin);
  const visibleTabs = tabs.filter((tab) => (tab.key === 'layout' || tab.key === 'permissions') ? canManageAdvanced : true);
  const orgDefaultColumns = fields.filter((f: any) => !f.hidden && !f.list_hidden).map((f: any) => f.name);
  const effectiveColumns = useOverride ? visibleColumns : orgDefaultColumns;

  const moveFieldToTarget = (fieldName: string, targetId: string) => {
    setLayout((prev) => {
      const next = withoutField(prev, fieldName);
      if (targetId.startsWith('section:')) {
        const sectionIndex = Number(targetId.split(':')[1]);
        next[sectionIndex] = { ...next[sectionIndex], fields: [...next[sectionIndex].fields, fieldName] };
      } else if (targetId.startsWith('tab:')) {
        const [, sectionRaw, tabRaw] = targetId.split(':');
        const sectionIndex = Number(sectionRaw);
        const tabIndex = Number(tabRaw);
        const tabs = [...(next[sectionIndex].tabs || [])];
        tabs[tabIndex] = { ...tabs[tabIndex], fields: [...tabs[tabIndex].fields, fieldName] };
        next[sectionIndex] = { ...next[sectionIndex], type: 'tabs', tabs };
      }
      return next;
    });
  };

  const handleLayoutDragEnd = (event: DragEndEvent) => {
    const activeId = String(event.active.id);
    const overId = event.over ? String(event.over.id) : '';
    if (!overId) return;
    if (activeId.startsWith('section-sort:') && overId.startsWith('section-sort:')) {
      const oldIndex = layout.findIndex((section) => `section-sort:${section.key}` === activeId);
      const newIndex = layout.findIndex((section) => `section-sort:${section.key}` === overId);
      if (oldIndex >= 0 && newIndex >= 0) setLayout((prev) => arrayMove(prev, oldIndex, newIndex));
      return;
    }
    if (activeId.startsWith('field:')) moveFieldToTarget(activeId.slice('field:'.length), overId);
  };

  const addSection = () => setLayout((prev) => [...prev, { key: `section-${Date.now()}`, title: 'Section', fields: [] }]);
  const removeSection = (sectionIndex: number) => setLayout((prev) => prev.filter((_, index) => index !== sectionIndex));
  const addTab = (sectionIndex: number) => setLayout((prev) => prev.map((section, index) => index === sectionIndex
    ? { ...section, type: 'tabs', tabs: [...(section.tabs || []), { key: `tab-${Date.now()}`, title: 'New Tab', fields: [] }] }
    : section));
  const removeTab = (sectionIndex: number, tabIndex: number) => setLayout((prev) => prev.map((section, index) => index === sectionIndex
    ? { ...section, tabs: (section.tabs || []).filter((_, i) => i !== tabIndex) }
    : section));

  return (
    <div className="flex h-full flex-col gap-4 text-[13px] text-[var(--text)]">
      <div className="flex flex-wrap gap-1 rounded border border-[var(--line)] bg-[var(--surface-2)] p-1">
        {visibleTabs.map((tab) => (
          <button key={tab.key} type="button" onClick={() => setActiveTab(tab.key)} className={`h-8 rounded px-3 text-[12px] font-semibold ${activeTab === tab.key ? 'bg-[var(--surface)] text-[var(--accent)] shadow-sm' : 'text-[var(--text-2)] hover:text-[var(--text)]'}`}>
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
        <DndContext collisionDetection={closestCenter} onDragEnd={handleLayoutDragEnd}>
          <div className="grid min-h-[520px] grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <button type="button" onClick={addSection} className="inline-flex h-8 items-center gap-2 rounded border border-[var(--line)] px-3 text-[12px] font-semibold">
                  <Plus size={13} /> Add Section
                </button>
                <button type="button" onClick={saveLayout} disabled={saving} className="inline-flex h-8 items-center justify-center gap-2 rounded bg-[var(--accent)] px-3 text-[12px] font-semibold text-white disabled:opacity-60">
                  <Save size={13} /> {saving ? 'Saving...' : 'Save layout'}
                </button>
              </div>
              <SortableContext items={layout.map((section) => `section-sort:${section.key}`)} strategy={verticalListSortingStrategy}>
                <div className="flex flex-col gap-3">
                  {layout.map((section, sectionIndex) => (
                    <SortableSection key={section.key} section={section}>
                      <div className="flex-1">
                        <input
                          value={section.title || ''}
                          onChange={(event) => setLayout((prev) => prev.map((s, i) => i === sectionIndex ? { ...s, title: event.target.value } : s))}
                          className="h-8 w-full rounded border border-[var(--line)] bg-[var(--surface)] px-2 text-[12px] font-semibold outline-none focus:border-[var(--accent)]"
                        />
                        <div className="mt-2">
                          <DroppableFieldList id={`section:${sectionIndex}`}>
                            <div className="flex flex-wrap gap-2">
                              {section.fields.map((name) => <DraggableFieldChip key={name} name={name} label={fieldLabel(name)} />)}
                            </div>
                          </DroppableFieldList>
                        </div>
                        {(section.tabs || []).map((tab, tabIndex) => (
                          <div key={tab.key} className="mt-2 rounded border border-[var(--line)] p-2" onContextMenu={(event) => { event.preventDefault(); removeTab(sectionIndex, tabIndex); }}>
                            <div className="mb-2 flex items-center gap-2">
                              <input
                                value={tab.title}
                                onChange={(event) => setLayout((prev) => prev.map((s, i) => {
                                  if (i !== sectionIndex) return s;
                                  const nextTabs = [...(s.tabs || [])];
                                  nextTabs[tabIndex] = { ...nextTabs[tabIndex], title: event.target.value };
                                  return { ...s, tabs: nextTabs };
                                }))}
                                className="h-7 flex-1 rounded border border-[var(--line)] bg-[var(--surface)] px-2 text-[12px] outline-none focus:border-[var(--accent)]"
                              />
                              <button type="button" onClick={() => removeTab(sectionIndex, tabIndex)} className="text-[var(--text-3)] hover:text-rose-500" title="Remove tab"><Trash2 size={13} /></button>
                            </div>
                            <DroppableFieldList id={`tab:${sectionIndex}:${tabIndex}`}>
                              <div className="flex flex-wrap gap-2">
                                {tab.fields.map((name) => <DraggableFieldChip key={name} name={name} label={fieldLabel(name)} />)}
                              </div>
                            </DroppableFieldList>
                          </div>
                        ))}
                      </div>
                      <button type="button" onClick={() => addTab(sectionIndex)} className="rounded border border-[var(--line)] px-2 py-1 text-[11px] font-semibold"><Plus size={12} /></button>
                      <button type="button" onClick={() => removeSection(sectionIndex)} onContextMenu={(event) => { event.preventDefault(); removeSection(sectionIndex); }} className="text-[var(--text-3)] hover:text-rose-500" title="Remove section"><Trash2 size={13} /></button>
                    </SortableSection>
                  ))}
                </div>
              </SortableContext>
            </div>

            <div className="rounded border border-[var(--line)] bg-[var(--surface)] p-4">
              <div className="mb-3 text-[11px] font-bold uppercase tracking-[0.14em] text-[var(--text-3)]">Live preview</div>
              <div className="space-y-4">
                {layout.map((section) => (
                  <div key={`preview-${section.key}`} className="rounded border border-[var(--line)] p-3">
                    <div className="mb-3 text-[12px] font-semibold text-[var(--text)]">{section.title}</div>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                      {section.fields.map((name) => <div key={name} className="rounded border border-[var(--line)] bg-[var(--surface-2)] px-2 py-1.5 text-[12px]">{fieldLabel(name)}</div>)}
                    </div>
                    {(section.tabs || []).length > 0 && (
                      <div className="mt-3 border-t border-[var(--line)] pt-3">
                        {(section.tabs || []).map((tab) => (
                          <div key={`preview-${tab.key}`} className="mb-3">
                            <div className="mb-2 inline-flex rounded border border-[var(--line)] px-2 py-1 text-[11px] font-semibold text-[var(--accent)]">{tab.title}</div>
                            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                              {tab.fields.map((name) => <div key={name} className="rounded border border-[var(--line)] bg-[var(--surface-2)] px-2 py-1.5 text-[12px]">{fieldLabel(name)}</div>)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </DndContext>
      )}

      {activeTab === 'columns' && (
        <div className="space-y-1">
          <label className="mb-3 flex items-center gap-2 rounded border border-[var(--line)] p-2 text-[12px] font-semibold">
            <input
              type="checkbox"
              checked={useOverride}
              onChange={async (event) => {
                const checked = event.target.checked;
                setUseOverride(checked);
                const columns = checked ? effectiveColumns : orgDefaultColumns;
                onVisibleColumnsChange?.(columns);
                await api.put('/preference', { key: `list:${cleanResourcePath(resource)}:columns`, value: JSON.stringify(columns) });
              }}
            />
            Use my column override
          </label>
          <div className="text-[11px] text-[var(--text-3)]">Organization default: {orgDefaultColumns.join(', ') || 'none'}</div>
          {fields.filter((f: any) => !f.hidden).map((field: any) => (
            <label key={field.name} className="flex items-center gap-2 rounded px-2 py-1.5 hover:bg-[var(--surface-2)]">
              <input
                type="checkbox"
                disabled={!useOverride}
                checked={effectiveColumns.includes(field.name)}
                onChange={(event) => {
                  const columns = event.target.checked ? [...effectiveColumns, field.name] : effectiveColumns.filter((c: string) => c !== field.name);
                  onVisibleColumnsChange?.(columns);
                  api.put('/preference', { key: `list:${cleanResourcePath(resource)}:columns`, value: JSON.stringify(columns) }).catch(() => {});
                }}
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

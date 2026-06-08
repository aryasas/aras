import { useEffect, useMemo, useRef, useState } from 'react';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import {
  RefreshCw, Check, MoreHorizontal, Share2, Copy, X, Link2, Settings, Zap
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { FieldProps } from '../SchemaRegistry';
import { useAras } from '../hooks/useAras';
import { useVocabulary } from '../../context/VocabularyContext';
import { createDefaultRecord } from '../../lib/schemaUtils';
import { DesignContainer } from './design/DesignContainer';
import { DesignElement } from './design/DesignElement';
import { useAuthStore } from '../../store/authStore';
import { InlineChildTable } from './InlineChildTable';
import FormSettings from './FormSettings';
import { useUIStore } from '../../store/uiStore';
import { validateField } from '../lib/validate';
import { InsightStrip } from './InsightStrip';
import { renderField, StatusBadge, findDisplayToken, type Field } from './dynamicForm.helpers';

// Re-exported so existing consumers keep importing { renderField, Field } from DynamicForm.
export { renderField } from './dynamicForm.helpers';
export type { Field } from './dynamicForm.helpers';

interface Metadata {
  resource: string;
  api_path?: string;
  title: string;
  fields: Field[];
  children?: Array<{ resource: string; fk_column?: string | null }>;
  workflow?: any;
  actions?: any[];
  layout?: any[];
  is_auditable?: boolean;
  app_name?: string;
  insights?: Array<{ key: string; label: string; format: string; icon?: string | null; prefix?: string | null; suffix?: string | null }>;
  form_insights?: Array<{ key: string; label: string; format: 'number' | 'currency' | 'percent'; icon?: string | null; prefix?: string | null; suffix?: string | null }>;
}

interface ModelAction {
  name: string;
  label?: string;
  icon?: string;
  has_input_schema?: boolean;
  input_fields?: Array<{ name: string; label: string; required: boolean; type: string }> | null;
}


export const DynamicForm = ({ resource, id, initialData, onSave, onCancel }: any) => {
  const vocabulary = useVocabulary();
  const navigate = useNavigate();
  const activeApps = useAuthStore((s) => s.activeApps);
  const optionalFeatures = useAuthStore((s) => s.optionalFeatures);
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [formData, setFormData] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [currentId, setCurrentId] = useState<any>(id !== 'new' ? id : undefined);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [displayToken, setDisplayToken] = useState<string | null>(null);
  const [childData, setChildData] = useState<Record<string, any[]>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [initialValues, setInitialValues] = useState<any>({});
  const [externalUpdate, setExternalUpdate] = useState(false);
  const formRef = useRef<HTMLDivElement>(null);
  
  const { notify } = useAras();
  const showPanel = useUIStore((s) => s.showPanel);
  const setDirty = useUIStore((s) => s.setDirty);
  const setPageTitle = useUIStore((s) => s.setPageTitle);

  useEffect(() => {
    const controller = new AbortController();
    const fetchMetadata = async () => {
      try {
        const cleanResource = cleanResourcePath(resource);
        const metaRes = await api.get(`/metadata/${cleanResource}`, { signal: controller.signal });
        setMetadata(metaRes.data);
        setLoading(false);
      } catch (err: any) {
        if (err.name === 'CanceledError') return;
        notify("Failed to load metadata", "error");
      }
    };
    fetchMetadata();
    return () => { controller.abort(); setPageTitle('', '', ''); };
  }, [resource, notify, setPageTitle]);

  useEffect(() => {
    const controller = new AbortController();
    if (metadata && currentId) {
      api.get(`/${cleanResourcePath(metadata.api_path || resource)}/${currentId}`, { signal: controller.signal })
        .then(res => {
          setFormData(res.data)
          setInitialValues(res.data)
        })
        .catch(err => {
          if (err.name === 'CanceledError') return;
          console.error("Failed to fetch record:", err);
        });
    } else if (metadata) {
      const next = { ...createDefaultRecord(metadata.fields), ...initialData }
      setFormData(next)
      setInitialValues(next)
    }
    return () => controller.abort();
  }, [metadata, currentId, initialData, resource]);

  const dirtyKey = `${cleanResourcePath(resource)}:${currentId || 'new'}`
  const isDirty = useMemo(() => JSON.stringify(formData) !== JSON.stringify(initialValues), [formData, initialValues])

  useEffect(() => {
    setDirty(dirtyKey, isDirty)
    return () => setDirty(dirtyKey, false)
  }, [dirtyKey, isDirty, setDirty])

  // claude-sonnet-4-6
  useEffect(() => {
    if (!metadata) return;
    const recordLabel = formData?.name || formData?.code || formData?.title || (currentId ? `#${currentId}` : 'New');
    setPageTitle(metadata.title, '', String(recordLabel));
  }, [metadata, formData?.name, formData?.code, formData?.title, currentId, setPageTitle]);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent).detail
      if (detail?.resource === cleanResourcePath(resource) && String(detail.id) === String(currentId)) {
        setExternalUpdate(true)
      }
    }
    window.addEventListener('aras:record-event', handler)
    return () => window.removeEventListener('aras:record-event', handler)
  }, [currentId, resource])

  const validateForm = () => {
    if (!metadata) return {};
    const nextErrors: Record<string, string> = {};
    for (const field of metadata.fields) {
      if (!isFieldVisible(field) || field.read_only || field.type === 'child_table') continue;
      const error = validateField(field, formData[field.name]);
      if (error) nextErrors[field.name] = error;
    }
    return nextErrors;
  };

  const handleSubmit = async () => {
    const nextErrors = validateForm();
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      notify("Please fix the highlighted fields", "error");
      const first = Object.keys(nextErrors)[0];
      formRef.current?.querySelector<HTMLElement>(`[name="${CSS.escape(first)}"], [data-field-name="${CSS.escape(first)}"] input, [data-field-name="${CSS.escape(first)}"] button`)?.focus();
      return;
    }
    setSaving(true);
    try {
      const cleanPath = cleanResourcePath(metadata?.api_path || resource);
      let savedId = currentId;
      if (currentId) {
        await api.patch(`/${cleanPath}/${currentId}`, formData);
      } else {
        const res = await api.post(`/${cleanPath}`, formData);
        if (res.data.id) {
          savedId = res.data.id;
          setCurrentId(res.data.id);
        }
      }
      if (savedId && metadata) {
        const m2mFields = metadata.fields.filter((field) => field.type === 'm2m');
        await Promise.all(m2mFields.map((field) => api.put(`/${cleanPath}/${savedId}/${field.name}`, { ids: formData[field.name] || [] })));
      }
      notify("Saved successfully", "success");
      setInitialValues(formData);
      setDirty(dirtyKey, false);
      if (onSave) onSave();
    } catch (err) {
      notify("Save failed", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleModelAction = async (action: ModelAction) => {
    if (!currentId || !metadata) return;
    setActionLoading(action.name);
    try {
      const cleanPath = cleanResourcePath(metadata.api_path || resource);
      const res = await api.post(`/${cleanPath}/${currentId}/action/${action.name}`, {});
      const token = findDisplayToken(res.data);
      if (token) setDisplayToken(token);
      notify(`${action.label || action.name} completed`, "success");
      const redirect = (res.data as any)?.data?.redirect ?? (res.data as any)?.redirect;
      if (typeof redirect === 'string' && redirect) {
        navigate(redirect);
        return;
      }
    } catch (err) {
      notify(`${action.label || action.name} failed`, "error");
    } finally {
      setActionLoading(null);
    }
  };

  const copyDisplayToken = async () => {
    if (!displayToken) return;
    try {
      await navigator.clipboard.writeText(displayToken);
      notify("Token copied", "success");
    } catch {
      notify("Copy failed", "error");
    }
  };

  const isFieldVisible = (field: Field) => {
    if (field.hidden || field.form_hidden) return false;
    const requiredApp = optionalFeatures[field.name];
    if (requiredApp && !activeApps.includes(requiredApp)) return false;
    return true;
  };

  // claude-opus-4-7
  // Field DnD reorder — only active when the URL has __builder_edit=1 (inside the Template Builder iframe).
  // Native HTML5 DnD writes the new order through the mounted dev field-reorder endpoint, then notifies the parent to reload.
  const builderEditMode = typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('__builder_edit') === '1'
  const dragFieldRef = (window as any).__arasDragField || { current: null as string | null }
  ;(window as any).__arasDragField = dragFieldRef

  const handleFieldDrop = async (targetName: string) => {
    const sourceName = dragFieldRef.current
    dragFieldRef.current = null
    if (!sourceName || sourceName === targetName || !metadata) return
    const ordered = metadata.fields.filter(isFieldVisible).map((f) => f.name)
    const from = ordered.indexOf(sourceName)
    const to = ordered.indexOf(targetName)
    if (from < 0 || to < 0) return
    ordered.splice(to, 0, ordered.splice(from, 1)[0])
    try {
      await import('../../lib/api').then(({ default: apiClient }) =>
        apiClient.post('/dev/dev/field-reorder', { resource: metadata.resource, order: ordered }),
      )
      if (window.parent !== window.self) {
        window.parent.postMessage({ type: 'aras-builder-reordered' }, '*')
      } else {
        window.location.reload()
      }
    } catch (err) {
      console.warn('field-reorder failed', err)
    }
  }

  const renderDynamicField = (field: Field) => renderField({
    field,
    value: formData[field.name],
    onChange: (val: FieldProps['value']) => {
      setFormData((prev: any) => ({...prev, [field.name]: val}));
      setErrors((prev) => {
        if (!prev[field.name]) return prev;
        const next = { ...prev };
        delete next[field.name];
        return next;
      });
    },
    formData,
    error: errors[field.name],
    disabled: field.read_only,
    vocabularyGet: vocabulary.get,
    isVisible: isFieldVisible,
    builderEditMode,
    onDragStart: () => { dragFieldRef.current = field.name },
    onDragOver: (e: React.DragEvent) => e.preventDefault(),
    onDrop: () => handleFieldDrop(field.name),
  });

  if (loading || !metadata) return <div className="p-8 text-center text-[var(--text-3)]">Loading form...</div>

  const fieldNames = new Set(metadata.fields.map((f) => f.name));
  const hasStatus = fieldNames.has('status') || fieldNames.has('state');
  const statusValue = formData.status ?? formData.state ?? null;
  const tagValue = formData.program ?? formData.project ?? formData.tag ?? null;
  const hasWorkflow = !!metadata.workflow || fieldNames.has('workflow_state') || fieldNames.has('lifecycle');
  const hasApprovers = fieldNames.has('approvers') || Array.isArray(formData.approvers);
  const hasWatching = fieldNames.has('watchers') || Array.isArray(formData.watchers);
  const showRail = hasWorkflow || hasApprovers || hasWatching;

  // Build sections from layout (or fall back to single section of all visible fields)
  const sections: { title: string; fields: Field[] }[] = (() => {
    const layout = metadata.layout;
    if (Array.isArray(layout) && layout.length > 0) {
      const out: { title: string; fields: Field[] }[] = [];
      for (const grp of layout) {
        const grpFields: Field[] = (grp.fields || [])
          .map((fn: string) => metadata.fields.find((f) => f.name === fn))
          .filter((f: Field | undefined): f is Field => !!f && isFieldVisible(f));
        if (grpFields.length) out.push({ title: grp.title || 'Section', fields: grpFields });
        for (const tab of grp.tabs || []) {
          const tabFields: Field[] = (tab.fields || [])
            .map((fn: string) => metadata.fields.find((f) => f.name === fn))
            .filter((f: Field | undefined): f is Field => !!f && isFieldVisible(f));
          if (tabFields.length) out.push({ title: tab.title || 'Section', fields: tabFields });
        }
      }
      if (out.length) return out;
    }
    return [{ title: 'Overview', fields: metadata.fields.filter(isFieldVisible) }];
  })();

  const codeField = formData.number ?? formData.code ?? (currentId ? String(currentId) : 'NEW');
  const titleField = formData.name ?? formData.title ?? formData.subject ?? '';
  const modelActions = (metadata.actions || []) as ModelAction[];

  const openSettings = () => {
    showPanel('Form Settings', <FormSettings resource={resource} metadata={metadata} />, 'max-w-3xl');
  };

  // claude-sonnet-4-6
  const AvatarInitial = ({ name, size = 22 }: { name: string; size?: number }) => (
    <span
      className="arc-av inline-flex items-center justify-center shrink-0"
      style={{ width: size, height: size, borderRadius: 999, background: 'var(--surface-2)', color: 'var(--text-2)', fontSize: size * 0.45, fontWeight: 700, border: '1px solid var(--line)' }}
    >
      {String(name || '?')[0].toUpperCase()}
    </span>
  );

  // claude-sonnet-4-6
  const LIFECYCLE_STAGES = ['Draft', 'In review', 'Approved', 'Released'];
  const curStageIdx = LIFECYCLE_STAGES.findIndex(s => s.toLowerCase() === String(statusValue || '').toLowerCase().replace(/_/g, ' '));

  // Derive thread from formData
  const thread: any[] = Array.isArray(formData.thread) ? formData.thread
    : Array.isArray(formData.comments) ? formData.comments : [];


  return (
    <div ref={formRef} className="aras-form-view flex w-full h-full animate-in fade-in duration-300">
      {/* Main column */}
      <div className={`flex-1 min-w-0 overflow-y-auto ${showRail ? 'border-r border-[var(--line)]' : ''}`}>

        {/* ── Insight strip ── */}
        {metadata?.form_insights?.length ? (
          <InsightStrip resource={resource} insights={metadata.form_insights} recordId={currentId} />
        ) : null}

        {/* ── Action band ── */}
        {externalUpdate && (
          <div className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-amber-200 bg-amber-50 px-5 py-2 text-sm text-amber-900">
            <span>Record updated externally — reload?</span>
            <button type="button" onClick={() => window.location.reload()} className="rounded bg-amber-600 px-3 py-1 text-xs font-bold text-white">
              Reload
            </button>
          </div>
        )}
        <DesignElement id="form-action-band" className="flex items-center gap-2.5 px-5 sm:px-7 lg:px-8 py-2.5 border-b border-[var(--line)] sticky top-0 z-20 bg-[var(--bg)]/90 backdrop-blur flex-wrap">
          {/* Left: record label + status + tag */}
          <span className="text-[13px] font-semibold text-[var(--text)]" style={{ letterSpacing: '-0.005em' }}>
            {titleField || (codeField ? String(codeField).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : (metadata?.title || ''))}
          </span>
          {hasStatus && statusValue != null && (
            <StatusBadge value={statusValue} />
          )}
          {tagValue && (
            <span className="inline-flex items-center gap-1 h-5 px-2 rounded bg-[var(--surface-2)] border border-[var(--line)] text-[10.5px] font-medium text-[var(--text-2)]">
              {String(tagValue)}
            </span>
          )}

          <div className="flex-1" />

          {/* Model action buttons */}
          {modelActions.map((action) => (
            <button
              key={action.name}
              type="button"
              onClick={() => handleModelAction(action)}
              disabled={!currentId || actionLoading !== null}
              className="h-6 px-3 rounded border border-[var(--accent)] text-[var(--accent)] text-[11.5px] font-semibold inline-flex items-center gap-1.5 hover:bg-[var(--accent)] hover:text-white disabled:cursor-not-allowed disabled:opacity-50 transition-all"
            >
              <Zap size={10} />
              {actionLoading === action.name ? 'Running…' : (action.label || action.name)}
            </button>
          ))}

          {/* Right: icon actions + defer + approve */}
          <button type="button" className="h-6 w-6 grid place-items-center rounded text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors" title="Share">
            <Share2 size={13} />
          </button>
          <button type="button" className="h-6 w-6 grid place-items-center rounded text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors" title="Copy link">
            <Link2 size={13} />
          </button>
          <button type="button" className="h-6 w-6 grid place-items-center rounded text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors" title="More">
            <MoreHorizontal size={13} />
          </button>
          <button type="button" onClick={openSettings} className="h-6 w-6 grid place-items-center rounded text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors" title="Settings">
            <Settings size={13} />
          </button>
          <button
            type="button"
            onClick={() => { if (onCancel) onCancel(); else navigate(-1); }}
            className="h-6 px-3 rounded border border-[var(--line)] text-[11.5px] font-medium text-[var(--text-2)] hover:text-[var(--text)] hover:border-[var(--text-3)] transition-colors"
          >
            {currentId ? 'Defer' : 'Cancel'}
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={saving}
            className="h-6 px-3 rounded bg-[var(--accent)] text-white text-[11.5px] font-semibold inline-flex items-center gap-1.5 hover:brightness-110 disabled:opacity-60 transition-all"
          >
            {saving ? <RefreshCw size={11} className="animate-spin" /> : <Check size={11} />}
            {currentId ? 'Approve' : 'Save'}
          </button>
        </DesignElement>

        {/* ── Body ── */}
        <div className="px-5 sm:px-7 lg:px-8 py-7">

          {/* Numbered sections */}
          <div className="flex flex-col gap-10">
            {sections.map((section, i) => {
              const n = String(i + 1).padStart(2, '0');
              return (
                <DesignContainer key={`${section.title}-${i}`} id={`section-${i}`} className="flex gap-8">
                  {/* Section number column */}
                  <div className="shrink-0 w-10 pt-[3px]">
                    <span className="arc-mono text-[12px] text-[var(--text-3)]">{n}</span>
                  </div>
                  {/* Section content */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-[14px] font-semibold text-[var(--text)] mb-1" style={{ letterSpacing: '-0.005em' }}>
                      {section.title}
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-5 mt-4">
                      {section.fields.map(renderDynamicField)}
                    </div>
                  </div>
                </DesignContainer>
              );
            })}
          </div>

          {/* Child tables — styled section */}
          {metadata.fields.filter(f => f.type === 'child_table' && f.target_resource).map((f, ci) => {
            const n = String(sections.length + ci + 1).padStart(2, '0');
            return (
              <div key={f.name} className="flex gap-8 mt-10">
                <div className="shrink-0 w-10 pt-[3px]">
                  <span className="arc-mono text-[12px] text-[var(--text-3)]">{n}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-[14px] font-semibold text-[var(--text)] mb-3" style={{ letterSpacing: '-0.005em' }}>
                    {vocabulary.get(f.label)}
                  </h3>
                  <InlineChildTable
                    childResource={f.target_resource!}
                    fkColumn={f.fk_column || ''}
                    parentId={currentId}
                    title={f.label}
                    rows={childData[f.target_resource!] ?? []}
                    onChange={rows => setChildData(prev => ({ ...prev, [f.target_resource!]: rows }))}
                    allowFullList={!!f.allow_full_list}
                  />
                </div>
              </div>
            );
          })}

          {/* Thread section */}
          {thread.length > 0 && (
            <div className="flex gap-8 mt-10">
              <div className="shrink-0 w-10 pt-[3px]">
                <span className="arc-mono text-[12px] text-[var(--text-3)]">{String(sections.length + metadata.fields.filter(f => f.type === 'child_table').length + 1).padStart(2, '0')}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-3">
                  <h3 className="text-[14px] font-semibold text-[var(--text)] flex-1" style={{ letterSpacing: '-0.005em' }}>Thread</h3>
                  <span className="text-[11px] text-[var(--text-3)]">{thread.length} posts</span>
                </div>
                <div className="flex flex-col gap-5">
                  {thread.map((post: any, idx: number) => (
                    <div key={idx} className="flex gap-3">
                      <AvatarInitial name={post.author || post.name || post.user || '?'} size={26} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-baseline gap-2 mb-1">
                          <span className="text-[12.5px] font-semibold text-[var(--text)]">{post.author || post.name || post.user}</span>
                          <span className="text-[11px] text-[var(--text-3)]">{post.created_at || post.timestamp || post.date || ''}</span>
                        </div>
                        <p className="text-[12.5px] text-[var(--text-2)] leading-relaxed">{post.content || post.body || post.text || ''}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

        </div>
      </div>

      {/* ── Right rail ── */}
      {showRail && (
        <aside className="hidden lg:flex flex-col shrink-0 px-4 py-6 gap-7 overflow-y-auto" style={{ width: 224, background: 'var(--bg-2)' }}>

          {/* Lifecycle */}
          {hasWorkflow && (
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-3)] mb-3">Lifecycle</div>
              <ol className="flex flex-col" style={{ gap: 0 }}>
                {LIFECYCLE_STAGES.map((stage, i) => {
                  const isActive = i === curStageIdx;
                  const isDone = curStageIdx >= 0 && i < curStageIdx;
                  const isLast = i === LIFECYCLE_STAGES.length - 1;
                  return (
                    <li key={stage} className="flex items-start gap-2.5" style={{ position: 'relative' }}>
                      {/* Vertical line connector */}
                      <div className="flex flex-col items-center shrink-0" style={{ width: 8 }}>
                        <span style={{
                          width: 8, height: 8, borderRadius: 999, flexShrink: 0, marginTop: 4,
                          background: isActive ? 'var(--accent)' : isDone ? 'var(--accent)' : 'transparent',
                          border: `1.5px solid ${isActive || isDone ? 'var(--accent)' : 'var(--line-2)'}`,
                        }} />
                        {!isLast && (
                          <span style={{
                            width: 1, flex: 1, minHeight: 16,
                            background: isDone ? 'var(--accent)' : 'var(--line)',
                            marginBottom: 0
                          }} />
                        )}
                      </div>
                      <div className="pb-3.5">
                        <div className={`text-[12px] ${isActive ? 'text-[var(--text)] font-semibold' : isDone ? 'text-[var(--text-2)]' : 'text-[var(--text-3)]'}`}>
                          {stage}
                        </div>
                        {isActive && (
                          <div className="text-[10.5px] text-[var(--text-3)] mt-0.5">in progress</div>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ol>
            </div>
          )}

          {/* Approvers */}
          {hasApprovers && Array.isArray(formData.approvers) && formData.approvers.length > 0 && (
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-3)] mb-3">Approvers</div>
              <ul className="flex flex-col gap-3">
                {formData.approvers.map((a: any, idx: number) => (
                  <li key={idx} className="flex items-center gap-2">
                    <AvatarInitial name={a.name || a.username || '?'} size={22} />
                    <div className="flex-1 min-w-0">
                      <div className="text-[12px] text-[var(--text)] truncate font-medium">{a.name || a.username}</div>
                      {a.role && <div className="text-[10.5px] text-[var(--text-3)] truncate">{a.role}</div>}
                    </div>
                    {a.approved
                      ? <span className="shrink-0 inline-flex items-center justify-center" style={{ width: 16, height: 16, borderRadius: 999, background: '#059669' }}><Check size={9} color="white" strokeWidth={3} /></span>
                      : <span className="shrink-0" style={{ width: 16, height: 16, borderRadius: 999, border: '1.5px solid var(--line-2)', display: 'inline-block' }} />
                    }
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Watching */}
          {hasWatching && Array.isArray(formData.watchers) && formData.watchers.length > 0 && (
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-3)] mb-2">
                Watching · {formData.watchers.length}
              </div>
              <div className="flex flex-wrap gap-1">
                {formData.watchers.map((w: any, i: number) => (
                  <AvatarInitial key={i} name={w.name || w.username || '?'} size={22} />
                ))}
              </div>
            </div>
          )}
        </aside>
      )}

      {/* Token modal */}
      {displayToken && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4">
          <div className="w-full max-w-lg rounded-[var(--app-radius)] border border-[var(--line)] bg-[var(--bg)] p-5 shadow-xl">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-[16px] font-semibold text-[var(--text)]">Copy token</h3>
              <button
                type="button"
                onClick={() => setDisplayToken(null)}
                className="h-8 w-8 grid place-items-center rounded-full text-[var(--text-3)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
                title="Close"
              >
                <X size={16} />
              </button>
            </div>
            <pre className="mt-4 max-h-64 overflow-auto whitespace-pre-wrap break-all rounded-[var(--app-radius)] border border-[var(--line)] bg-[var(--surface-2)] p-4 text-[12px] text-[var(--text)]">{displayToken}</pre>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDisplayToken(null)}
                className="h-9 px-4 rounded-full border border-[var(--line)] text-[13px] font-medium text-[var(--text-2)] hover:text-[var(--text)]"
              >
                Close
              </button>
              <button
                type="button"
                onClick={copyDisplayToken}
                className="h-9 px-4 rounded-full bg-[var(--accent)] text-[var(--accent-d)] text-[13px] font-semibold inline-flex items-center gap-2 hover:brightness-110"
              >
                <Copy size={14} />
                Copy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

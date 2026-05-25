import { useEffect, useState } from 'react';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import {
  RefreshCw, Check, MoreHorizontal, Share2, Copy, X
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { resolveFieldComponent } from '../SchemaRegistry';
import { useAras } from '../hooks/useAras';
import { useVocabulary } from '../../context/VocabularyContext';
import { createDefaultRecord } from '../../lib/schemaUtils';
import { DesignContainer } from './design/DesignContainer';
import { DesignElement } from './design/DesignElement';
import { useAuthStore } from '../../store/authStore';

interface Field {
  name: string;
  label: string;
  type: string;
  required: boolean;
  read_only: boolean;
  hidden: boolean;
  form_hidden?: boolean;
  depends_on?: string;
  target_resource?: string;
  target_api_path?: string | null;
  fk_column?: string | null;
  options?: { label: string; value: any }[];
}

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
}

interface ModelAction {
  name: string;
  label?: string;
  icon?: string;
  has_input_schema?: boolean;
  input_fields?: Array<{ name: string; label: string; required: boolean; type: string }> | null;
}

// claude-opus-4-7
const STATUS_GLYPH: Record<string, { ch: string; color: string; label?: string }> = {
  draft:       { ch: '○', color: 'var(--text-3)' },
  in_progress: { ch: '◐', color: 'var(--accent)' },
  in_review:   { ch: '△', color: '#d97706', label: 'In review' },
  pending:     { ch: '△', color: '#d97706' },
  released:    { ch: '●', color: '#059669' },
  active:      { ch: '●', color: '#059669' },
  approved:    { ch: '●', color: '#059669' },
  blocked:     { ch: '✕', color: '#e11d48' },
  cancelled:   { ch: '✕', color: '#e11d48' },
  rejected:    { ch: '✕', color: '#e11d48' },
};
function StatusBadge({ value }: { value: any }) {
  if (value == null || value === '') return null;
  const raw = String(value).toLowerCase().trim().replace(/\s+/g, '_');
  const g = STATUS_GLYPH[raw] || { ch: '○', color: 'var(--text-3)' };
  const label = g.label || String(value).replace(/_/g, ' ');
  return (
    <span className="inline-flex items-center gap-1.5 text-[12px] capitalize text-[var(--text-2)]">
      <span style={{ color: g.color, fontFamily: 'Geist Mono, ui-monospace, monospace', fontSize: 13 }}>{g.ch}</span>
      {label}
    </span>
  );
}

function findDisplayToken(value: any): string | null {
  if (!value || typeof value !== 'object') return null;
  if (typeof value.display_token === 'string') return value.display_token;
  return findDisplayToken(value.data) || findDisplayToken(value.result);
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
  
  const { notify } = useAras();

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
    return () => controller.abort();
  }, [resource, notify]);

  useEffect(() => {
    const controller = new AbortController();
    if (metadata && currentId) {
      api.get(`/${cleanResourcePath(metadata.api_path || resource)}/${currentId}`, { signal: controller.signal })
        .then(res => setFormData(res.data))
        .catch(err => {
          if (err.name === 'CanceledError') return;
          console.error("Failed to fetch record:", err);
        });
    } else if (metadata) {
      setFormData({ ...createDefaultRecord(metadata.fields), ...initialData })
    }
    return () => controller.abort();
  }, [metadata, currentId, initialData, resource]);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      const cleanPath = cleanResourcePath(metadata?.api_path || resource);
      if (currentId) {
        await api.patch(`/${cleanPath}/${currentId}`, formData);
      } else {
        const res = await api.post(`/${cleanPath}`, formData);
        if (res.data.id) setCurrentId(res.data.id);
      }
      notify("Saved successfully", "success");
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

  const renderField = (field: Field) => {
    if (!isFieldVisible(field)) return null;
    const Component = resolveFieldComponent(field);
    return (
      <DesignElement id={`field-${field.name}`} key={field.name} className="flex flex-col gap-1.5 w-full">
        <label className="text-[10px] font-bold text-[var(--text-3)] uppercase tracking-[0.14em]">{vocabulary.get(field.label)}</label>
        <Component
           field={field}
           value={formData[field.name]}
           onChange={(val: any) => setFormData((prev: any) => ({...prev, [field.name]: val}))}
           formData={formData}
        />
      </DesignElement>
    );
  };

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
  const kicker = (vocabulary.get(metadata.title) || '').toUpperCase();
  const idPrefix = (resource.split('/').pop() || 'ARC').toUpperCase().slice(0, 3);
  const modelActions = (metadata.actions || []) as ModelAction[];

  return (
    <div className="aras-form-view flex w-full h-full animate-in fade-in duration-300">
      {/* Main column */}
      <div className={`flex-1 min-w-0 ${showRail ? 'border-r border-[var(--line)]' : ''}`}>
        {/* Action band */}
        <DesignElement id="form-action-band" className="flex items-center gap-3 px-5 sm:px-7 lg:px-8 py-3 border-b border-[var(--line)] sticky top-0 z-20 bg-[var(--bg)]/85 backdrop-blur flex-wrap">
          <span className="inline-flex items-center gap-1.5 h-6 px-2.5 rounded-full border border-[var(--line)] text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-2)]">
            {kicker} · <span className="text-[var(--accent)]">{idPrefix}</span>
          </span>
          {hasStatus && statusValue != null && <StatusBadge value={statusValue} />}
          {tagValue && (
            <span className="inline-flex items-center gap-1 h-6 px-2.5 rounded-full bg-[var(--surface-2)] text-[11.5px] font-medium text-[var(--text-2)]">
              {String(tagValue)}
            </span>
          )}
          <div className="flex-1" />
          <button type="button" className="h-7 w-7 grid place-items-center rounded-full text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors" title="Share">
            <Share2 size={13} />
          </button>
          <button type="button" className="h-7 w-7 grid place-items-center rounded-full text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors" title="More">
            <MoreHorizontal size={14} />
          </button>
          <button
            type="button"
            onClick={() => { if (onCancel) onCancel(); else navigate(-1); }}
            className="h-7 px-3 rounded-full border border-[var(--line)] text-[12px] font-medium text-[var(--text-2)] hover:text-[var(--text)] hover:border-[var(--text-3)] transition-colors"
          >
            {currentId ? 'Defer' : 'Cancel'}
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={saving}
            className="h-7 px-3.5 rounded-full bg-[var(--accent)] text-white text-[12px] font-semibold inline-flex items-center gap-1.5 hover:brightness-110 disabled:opacity-60 transition-all"
          >
            {saving ? <RefreshCw size={12} className="animate-spin" /> : <Check size={12} />}
            {currentId ? 'Approve' : 'Save'}
          </button>
        </DesignElement>

        {/* Body */}
        <div className="px-5 sm:px-7 lg:px-8 py-6">
          {/* Title row */}
          <div className="flex items-baseline gap-2 mb-3 flex-wrap">
            <span className="arc-id text-[20px] sm:text-[22px]" style={{ color: 'var(--accent)' }}>
              <b>{idPrefix}</b> · <b>{codeField}</b>
            </span>
            {titleField && (
              <h1 className="text-[20px] sm:text-[22px] font-semibold text-[var(--text)] leading-tight" style={{ letterSpacing: '-0.01em' }}>
                {titleField}
              </h1>
            )}
          </div>

          {/* Meta strip */}
          <DesignElement id="meta-strip" className="flex flex-wrap items-start gap-x-8 gap-y-2 py-4 border-b border-[var(--line)] mb-8">
            {['owner', 'created_at', 'target_rev', 'severity', 'cost_impact', 'updated_at']
              .filter((n) => fieldNames.has(n) && formData[n] != null)
              .slice(0, 5)
              .map((n) => {
                const f = metadata.fields.find((x) => x.name === n)!;
                return (
                  <div key={n} className="text-[11.5px] text-[var(--text-3)]">
                    <span className="font-medium text-[var(--text-2)]">{vocabulary.get(f.label)}</span>{' '}
                    <span className="text-[var(--text)]">{String(formData[n])}</span>
                  </div>
                );
              })}
          </DesignElement>

          {/* Numbered sections */}
          <div className="flex flex-col gap-10">
            {sections.map((section, i) => {
              const n = String(i + 1).padStart(2, '0');
              return (
                <DesignContainer key={`${section.title}-${i}`} id={`section-${i}`} className="flex flex-col gap-4">
                  <div className="flex items-baseline gap-3">
                    <span className="arc-mono text-[12px] text-[var(--text-3)]">{n}</span>
                    <h3 className="text-[16px] font-semibold text-[var(--text)]" style={{ letterSpacing: '-0.005em' }}>
                      {section.title}
                    </h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-5">
                    {section.fields.map(renderField)}
                  </div>
                </DesignContainer>
              );
            })}
          </div>
          {modelActions.length > 0 && (
            <DesignElement id="form-action-footer" className="mt-10 flex flex-wrap items-center gap-2 border-t border-[var(--line)] pt-5">
              {modelActions.map((action) => (
                <button
                  key={action.name}
                  type="button"
                  onClick={() => handleModelAction(action)}
                  disabled={!currentId || actionLoading !== null}
                  className="h-8 px-3.5 rounded-full border border-[var(--line)] text-[12px] font-semibold text-[var(--text-2)] hover:text-[var(--text)] hover:border-[var(--text-3)] disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
                >
                  {actionLoading === action.name ? 'Running...' : (action.label || action.name)}
                </button>
              ))}
            </DesignElement>
          )}
        </div>
      </div>

      {/* Right rail (lifecycle / approvers / watching) */}
      {showRail && (
        <aside className="hidden lg:flex flex-col shrink-0 px-5 py-6 gap-7" style={{ width: 240, background: 'var(--bg-2)' }}>
          {hasWorkflow && (
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-3)] mb-3">Lifecycle</div>
              <ol className="flex flex-col gap-2.5">
                {(['Draft','In review','Approved','Released'] as const).map((stage, i) => {
                  const cur = String(statusValue || '').toLowerCase().replace(/_/g,' ');
                  const active = cur === stage.toLowerCase();
                  return (
                    <li key={stage} className="flex items-start gap-2.5 text-[12px]">
                      <span style={{
                        width: 8, height: 8, marginTop: 5, borderRadius: 999,
                        background: active ? 'var(--accent)' : 'transparent',
                        border: `1px solid ${active ? 'var(--accent)' : 'var(--line)'}`,
                      }} />
                      <span className={active ? 'text-[var(--text)] font-semibold' : 'text-[var(--text-3)]'}>
                        {stage}
                        {i === 1 && active && (
                          <div className="text-[11px] font-normal text-[var(--text-3)] mt-0.5">in progress</div>
                        )}
                      </span>
                    </li>
                  );
                })}
              </ol>
            </div>
          )}

          {hasApprovers && Array.isArray(formData.approvers) && (
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-3)] mb-3">Approvers</div>
              <ul className="flex flex-col gap-2.5">
                {formData.approvers.map((a: any, idx: number) => (
                  <li key={idx} className="flex items-center gap-2 text-[12px]">
                    <span className="arc-av inline-flex items-center justify-center" style={{ width: 22, height: 22, borderRadius: 999, background: 'var(--surface-2)', color: 'var(--text-2)', fontSize: 10, fontWeight: 700 }}>
                      {String(a.name || a.username || '?')[0]?.toUpperCase()}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-[var(--text)] truncate">{a.name || a.username}</div>
                      {a.role && <div className="text-[11px] text-[var(--text-3)] truncate">{a.role}</div>}
                    </div>
                    {a.approved && <Check size={12} className="text-[var(--accent)]" />}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {hasWatching && Array.isArray(formData.watchers) && (
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-3)] mb-3">Watching · {formData.watchers.length}</div>
              <div className="flex flex-wrap gap-1">
                {formData.watchers.map((w: any, i: number) => (
                  <span key={i} className="arc-av inline-flex items-center justify-center" style={{ width: 22, height: 22, borderRadius: 999, background: 'var(--surface-2)', color: 'var(--text-2)', fontSize: 10, fontWeight: 700 }}>
                    {String(w.name || w.username || '?')[0]?.toUpperCase()}
                  </span>
                ))}
              </div>
            </div>
          )}
        </aside>
      )}
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
                className="h-9 px-4 rounded-full bg-[var(--accent)] text-white text-[13px] font-semibold inline-flex items-center gap-2 hover:brightness-110"
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

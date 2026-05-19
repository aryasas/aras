import React, { useEffect, useRef, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { useAuthStore } from '../../store/authStore';
import {
  Save, ArrowLeft, RefreshCw, ChevronLeft, ChevronRight,
  History as HistoryIcon, Zap, Settings, AlertCircle,
  Building2, Store, School, Users, HandHeart, Library, HeartPulse, Landmark, BriefcaseBusiness,
  Printer, Trash2, Copy, Link2, ArrowUpRight
} from 'lucide-react';
import ListView from './ListView';
import { filterEmptyChildRows, InlineChildTable, invalidateInlineLookupCache } from './InlineChildTable';
import MultiSelectCombobox from './MultiSelectCombobox';
import { resolveFieldComponent } from '../SchemaRegistry';
import { useAras } from '../hooks/useAras';
import { useUIStore } from '../../store/uiStore';
import { LogicEvaluator } from '../../lib/LogicEvaluator';
import { useVocabulary, vocabularyCache } from '../../context/VocabularyContext';
import { PrintPreview } from './PrintPreview';
import { createDefaultRecord } from '../../lib/schemaUtils';

interface Field {
  name: string;
  label: string;
  type: string;
  required: boolean;
  read_only: boolean;
  hidden: boolean;
  form_hidden?: boolean;
  depends_on?: string; // Conditional visibility logic
  target_resource?: string;
  target_api_path?: string | null;
  fk_column?: string | null;
  options?: { label: string; value: any }[];
  min_length?: number;
  max_length?: number;
  min_value?: number;
  max_value?: number;
  pattern?: string;
  min?: number;
  max?: number;
}

interface WorkflowAction {
  name: string;
  to: string;
  label: string;
  icon?: string;
}

interface ActionInputField {
  name: string;
  label: string;
  type: string;
  required: boolean;
}

interface ModelAction {
  name: string;
  label: string;
  icon?: string;
  has_input_schema: boolean;
  input_fields?: ActionInputField[];
}

interface LayoutSection {
  title: string;
  fields: string[];
  type?: 'section' | 'tab';  // default 'section' if omitted
  actions?: string[];  // action names to render as inline buttons in the section header
}

interface LayoutGroup {
  type: 'tabs';
  tabs: LayoutSection[];
}

interface LayoutLinkedList {
  type: 'linked_list';
  title: string;
  resource: string;
  fk_field: string;
}

interface Metadata {
  resource: string;
  api_path?: string;
  title: string;
  fields: Field[];
  children?: Array<{ resource: string; fk_column?: string | null }>;
  workflow?: any;
  actions?: ModelAction[];
  layout?: (LayoutSection | LayoutGroup | LayoutLinkedList)[];
  is_auditable?: boolean;
  is_document?: boolean;
  app_name?: string;
}

interface LinkedDoc {
  label: string;
  resource: string;
  id: number;
  number: string;
}

const normalizeLinkedDocs = (value: any): LinkedDoc[] => {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.data)) return value.data;
  return [];
};

const linkedDocsDeleteMessage = (docs: LinkedDoc[]) => {
  if (docs.length === 0) return 'Delete this record? This cannot be undone.';
  const preview = docs.slice(0, 5).map(doc => `${doc.label} ${doc.number || `#${doc.id}`}`).join(', ');
  const suffix = docs.length > 5 ? `, and ${docs.length - 5} more` : '';
  return `Delete this record and ${docs.length} related document${docs.length === 1 ? '' : 's'}? Related documents will also be deleted: ${preview}${suffix}. This cannot be undone.`;
};

const PROFILE_OPTIONS = [
  { value: 'general', label: 'General', icon: BriefcaseBusiness },
  { value: 'retail', label: 'Retail', icon: Store },
  { value: 'school', label: 'School', icon: School },
  { value: 'coop', label: 'Cooperative', icon: Users },
  { value: 'npo', label: 'Nonprofit', icon: HandHeart },
  { value: 'library', label: 'Library', icon: Library },
  { value: 'hospital', label: 'Hospital', icon: HeartPulse },
  { value: 'government', label: 'Government', icon: Landmark },
]

const UNIT_TYPE_OPTIONS = [
  { value: 'organization', label: 'Organization' },
  { value: 'company', label: 'Company' },
  { value: 'branch', label: 'Branch' },
  { value: 'unit', label: 'Unit' },
  { value: 'division', label: 'Division' },
  { value: 'department', label: 'Department' },
  { value: 'school', label: 'School' },
  { value: 'clinic', label: 'Clinic' },
  { value: 'store', label: 'Store' },
]

const TERMINAL_PLACEHOLDERS: Record<string, string> = {
  retail: 'Kasir 1',
  school: 'Loket SPP',
  coop: 'Teller',
}

interface DynamicFormProps {
  resource: string;
  id?: number | string;
  onSave?: (data: any) => void;
  onCancel?: () => void;
  onDelete?: () => void;
  onNavigate?: (id: number) => void;
  initialData?: Record<string, any>;
  parentResourceTitle?: string;
}

export const DynamicForm: React.FC<DynamicFormProps> = ({
  resource,
  id,
  onSave,
  onCancel,
  onDelete,
  onNavigate,
  initialData,
  parentResourceTitle
}) => {
  const { activeOrgId, organizations, setOrganizations } = useAuthStore();
  const vocabulary = useVocabulary();
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [formData, setFormData] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [metadataLoading, setMetadataLoading] = useState(true);
  const [metadataError, setMetadataError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [workflowActions, setWorkflowActions] = useState<WorkflowAction[]>([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [actionDialog, setActionDialog] = useState<{ action: ModelAction; inputData: Record<string, any> } | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [childRows, setChildRows] = useState<Record<string, any[]>>({});
  const [resourceSubtitle, setResourceSubtitle] = useState<string | null>(parentResourceTitle ?? null);
  const [prevId, setPrevId] = useState<number | null>(null);
  const [nextId, setNextId] = useState<number | null>(null);
  const [searchParams] = useSearchParams();
  // currentId tracks the actual persisted record ID — updated after POST so child tables appear immediately
  const [currentId, setCurrentId] = useState<number | string | undefined>(() =>
    id != null && id !== 'new' ? id : undefined
  );
  
  const { notify, confirm } = useAras();
  const navigate = useNavigate();
  const showPanel = useUIStore((state) => state.showPanel);
  const closePanel = useUIStore((state) => state.closePanel);
  const [showPrintPreview, setShowPrintPreview] = useState(false);
  const [activeTab, setActiveTab] = useState<Record<number, number>>({});
  const [nextSeriesNumber, setNextSeriesNumber] = useState<string | null>(null);
  const [linkedDocs, setLinkedDocs] = useState<LinkedDoc[]>([]);
  const handleSubmitRef = useRef<(() => void) | null>(null);
  const initialM2mRef = useRef<Record<string, any[]>>({});
  const initialChildRowIdsRef = useRef<Record<string, Set<any>>>({});

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        handleSubmitRef.current?.();
      } else if (event.key === 'Escape') {
        if (onCancel) {
          event.preventDefault();
          onCancel();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onCancel]);


  useEffect(() => {
    setCurrentId(id != null && id !== 'new' ? id : undefined);
    initialM2mRef.current = {};
    initialChildRowIdsRef.current = {};
  }, [id]);

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        setMetadataLoading(true);
        setMetadataError(null);
        const cleanResource = cleanResourcePath(resource);
        const metaRes = await api.get(`/metadata/${cleanResource}`);
        setMetadata(metaRes.data);
        setMetadataLoading(false);
      } catch (err: any) {
        const message = err.response?.data?.detail || "Failed to load metadata";
        setMetadataError(message);
        notify(message, "error");
        setMetadataLoading(false);
      }
    };
    fetchMetadata();
  }, [resource, notify]);

  useEffect(() => {
    if (!metadata?.is_document || (id != null && id !== 'new')) {
      setNextSeriesNumber(null);
      return;
    }
    api.get('/erp/series/next', { params: { key: metadata.resource } })
      .then(res => setNextSeriesNumber(res.data.next ?? null))
      .catch(() => setNextSeriesNumber(null));
  }, [metadata, id]);

  useEffect(() => {
    const fetchData = async () => {
      if (!metadata) return; // Wait for metadata to be loaded
      try {
        setLoading(true);
        const cleanResource = cleanResourcePath(resource);

        const queryResource = searchParams.get('resource');
        if (queryResource && cleanResource.replace(/-/g, '_') === 'aras_fields') {
          try {
            const queryResourcePath = queryResource.replace(/_/g, '-');
            let resourceMeta;
            try {
              resourceMeta = await api.get(`/metadata/${queryResourcePath}`);
            } catch {
              resourceMeta = await api.get(`/metadata/${queryResource}`);
            }
            setResourceSubtitle(resourceMeta.data?.title || queryResource);
          } catch {
            setResourceSubtitle(queryResource);
          }
        } else {
          setResourceSubtitle(parentResourceTitle ?? null);
        }

        if (id != null && id !== 'new') {
          const resourceApiPath = metadata.api_path || cleanResource;
          const dataRes = await api.get(`/${resourceApiPath}/${id}`);
          setFormData(dataRes.data);
          initialM2mRef.current = metadata.fields
            .filter((f: any) => f.type === 'm2m')
            .reduce((acc: Record<string, any[]>, f: any) => {
              acc[f.name] = Array.isArray(dataRes.data?.[f.name]) ? dataRes.data[f.name] : [];
              return acc;
            }, {});

          // Load existing child rows for every child_table field
          const childFields = metadata.fields.filter((f: any) => f.type === 'child_table' && f.target_resource);
          if (childFields.length > 0) {
            const childData: Record<string, any[]> = {};
            await Promise.all(childFields.map(async (f: any) => {
              try {
                const childRes = resolveChildApiPath(f);
                const fkKey = f.fk_column || `${resourceApiPath.split('/').pop()}_id`;
                const filters = JSON.stringify([{ field: fkKey, op: '=', value: id }]);
                const res = await api.get(`/${childRes}`, { params: { filters, per_page: 500 } });
                childData[f.name] = res.data?.items ?? res.data ?? [];
              } catch (err) {
                console.error('Child load failed', f.name, err);
                childData[f.name] = [];
              }
            }));
            setChildRows(childData);
            initialChildRowIdsRef.current = Object.fromEntries(
              Object.entries(childData).map(([k, rows]) => [k, new Set((rows as any[]).map(r => r.id).filter(Boolean))])
            );
          }

          if (metadata.workflow) {
            try {
              const actionRes = await api.get(`/workflow/${cleanResource}/${id}/actions`);
              setWorkflowActions(actionRes.data);
            } catch (aErr) {
              console.warn("Could not fetch workflow actions", aErr);
            }
          }
        } else {
          const defaults: any = { ...createDefaultRecord(metadata.fields), ...initialData };
          if (activeOrgId && !defaults['org_id']) defaults['org_id'] = activeOrgId;
          setFormData(defaults);
          // Pre-populate child rows when duplicating
          if (initialData) {
            const childFields = metadata.fields.filter((f: any) => f.type === 'child_table');
            const seedRows: Record<string, any[]> = {};
            for (const cf of childFields) {
              if (Array.isArray(initialData[cf.name]) && initialData[cf.name].length > 0) {
                seedRows[cf.name] = initialData[cf.name];
              }
            }
            if (Object.keys(seedRows).length > 0) setChildRows(seedRows);
          }
        }
      } catch (err: any) {
        notify(err.response?.data?.detail || "Failed to load form", "error");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [resource, id, notify, initialData, refreshTrigger, searchParams, parentResourceTitle, activeOrgId, metadata]);

  useEffect(() => {
    if (!currentId) { setLinkedDocs([]); return; }
    api.get(`/${cleanResourcePath(resource)}/${currentId}/linked-documents`)
      .then(res => setLinkedDocs(normalizeLinkedDocs(res.data)))
      .catch(() => setLinkedDocs([]));
  }, [resource, currentId, refreshTrigger]);

  useEffect(() => {
    if (!currentId || !metadata) {
      setPrevId(null);
      setNextId(null);
      return;
    }

    const base = metadata.api_path || cleanResourcePath(resource);
    const numericId = Number(currentId);
    api.get(`/${base}`, {
      params: {
        per_page: 1,
        order_by: 'id',
        desc: true,
        filters: JSON.stringify([{ field: 'id', op: '<', value: numericId }])
      }
    })
      .then(r => setPrevId(r.data?.data?.items?.[0]?.id ?? null))
      .catch(() => setPrevId(null));
    api.get(`/${base}`, {
      params: {
        per_page: 1,
        order_by: 'id',
        desc: false,
        filters: JSON.stringify([{ field: 'id', op: '>', value: numericId }])
      }
    })
      .then(r => setNextId(r.data?.data?.items?.[0]?.id ?? null))
      .catch(() => setNextId(null));
  }, [currentId, metadata, resource]);

  const handleChange = (name: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => {
        const n = { ...prev };
        delete n[name];
        return n;
      });
    }
  };

  const handleLinesChange = (fieldName: string, rows: any[]) => {
    setChildRows(prev => ({ ...prev, [fieldName]: rows }));
    if (fieldName === 'lines' && 'subtotal' in formData) {
      const subtotal = rows.reduce((sum, r) => sum + (parseFloat(r.amount) || 0), 0);
      const charges = childRows['charges'] ?? [];
      const totalCharge = charges.reduce((sum, r) => sum + (parseFloat(r.amount) || 0), 0);
      setFormData((prev: any) => ({
        ...prev,
        subtotal,
        total_amount: subtotal + totalCharge + (parseFloat(prev.total_tax) || 0),
      }));
    }
  };

  const isFieldVisible = (field: Field) => {
    if (field.hidden) return false;
    if (field.form_hidden) return false;
    if (!field.depends_on) return true;
    
    return LogicEvaluator.evaluate(field.depends_on, formData);
  };

  const handleShowHistory = () => {
    const cleanResource = cleanResourcePath(resource);
    showPanel(
      `${metadata ? vocabulary.get(metadata.title) : ''} Audit Trail`,
      <div className="h-[calc(100vh-150px)]">
        <ListView 
          resource="aras_activity_logs" 
          fixedFilters={{ resource: cleanResource, resource_id: currentId }}
        />
      </div>,
      'max-w-5xl'
    );
  };

  const handleCustomize = async () => {
    if (!metadata) return;
    // metadata.resource is the tablename (e.g. erp_accounting_outflow_invoices);
    // the URL-based resource prop is an API path and won't match ResourceModel.name.
    const tableName = metadata.resource;

    try {
      const res = await api.get('/aras_resources', {
        params: { filters: JSON.stringify([{ field: 'name', op: '=', value: tableName }]) }
      });
      const resourceRecord = res.data.items[0];
      if (!resourceRecord) {
        notify("Resource record not found in registry", "error");
        return;
      }

      const CustomizePanel = () => {
        const [customizeTab, setCustomizeTab] = useState<'fields' | 'layout'>('fields');

        const LayoutPanel = () => {
          const [layoutJson, setLayoutJson] = useState(
            JSON.stringify(resourceRecord?.layout ?? [], null, 2)
          );
          const [savingLayout, setSavingLayout] = useState(false);
          const save = async () => {
            setSavingLayout(true);
            try {
              await api.patch(`/aras_resources/${resourceRecord.id}`, { layout: JSON.parse(layoutJson) });
              notify('Layout saved. Refresh to see changes.', 'success');
              closePanel();
            } catch {
              notify('Invalid JSON or save failed', 'error');
            }
            setSavingLayout(false);
          };
          return (
            <div className="p-4 flex flex-col gap-3">
              <p className="text-xs text-slate-500">Edit layout JSON directly. Supports <code>type:"tabs"</code> and <code>type:"section"</code>.</p>
              <textarea
                className="w-full h-64 font-mono text-xs border border-slate-200 rounded-xl p-3 bg-slate-50 focus:ring-2 focus:ring-indigo-500 outline-none"
                value={layoutJson}
                onChange={e => setLayoutJson(e.target.value)}
              />
              <button onClick={save} disabled={savingLayout}
                className="self-end px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm hover:bg-indigo-700 disabled:opacity-50">
                {savingLayout ? 'Saving…' : 'Save Layout'}
              </button>
            </div>
          );
        };

        return (
          <div className="h-[calc(100vh-150px)] flex flex-col">
            <div className="flex border-b border-slate-200 bg-white px-4 pt-3">
              <button
                type="button"
                onClick={() => setCustomizeTab('fields')}
                className={`px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${customizeTab === 'fields' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
              >
                Fields
              </button>
              <button
                type="button"
                onClick={() => setCustomizeTab('layout')}
                className={`px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${customizeTab === 'layout' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
              >
                Layout
              </button>
            </div>
            <div className="flex-1 min-h-0">
              {customizeTab === 'fields' ? (
                <ListView
                  key={resourceRecord.id}
                  resource="aras_fields"
                  fixedFilters={{ resource_id: resourceRecord.id }}
                  onAdd={() => {
                    showPanel(
                      `New Field — ${vocabulary.get(metadata.title)}`,
                      <DynamicForm
                        resource="aras_fields"
                        id="new"
                        initialData={{ resource_id: resourceRecord.id }}
                        onSave={() => {
                          notify("Field added. Refresh to see changes.", "success");
                          setRefreshTrigger(prev => prev + 1);
                          closePanel();
                        }}
                        onCancel={closePanel}
                      />,
                      'max-w-4xl'
                    );
                  }}
                  onRowClick={(fieldId) => {
                     showPanel(`Edit Field Customization`,
                       <DynamicForm
                         resource="aras_fields"
                         id={fieldId}
                         parentResourceTitle={metadata.title}
                         onSave={() => {
                           notify("Field customized. Refresh to see changes.", "success");
                           setRefreshTrigger(prev => prev + 1);
                         }}
                         onCancel={closePanel}
                       />,
                       'max-w-4xl'
                     );
                  }}
                />
              ) : (
                <LayoutPanel />
              )}
            </div>
          </div>
        );
      };

      showPanel(
        `Customize: ${vocabulary.get(metadata.title)}`,
        <CustomizePanel />,
        'max-w-5xl'
      );
    } catch (err) {
      notify("Failed to load resource record", "error");
    }
  };

  const handleWorkflowAction = async (actionName: string) => {
    setSaving(true);
    try {
      const cleanResource = cleanResourcePath(resource);
      await api.post(`/workflow/${cleanResource}/${currentId}/action/${actionName}`);
      notify(`Workflow action completed`, "success");
      setRefreshTrigger(prev => prev + 1);
    } catch (err: any) {
      notify(err.response?.data?.detail || "Workflow action failed", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!currentId) return;
    const cleanResource = metadata?.api_path || cleanResourcePath(resource);
    let docs = linkedDocs;
    if (docs.length === 0) {
      try {
        const res = await api.get(`/${cleanResource}/${currentId}/linked-documents`);
        docs = normalizeLinkedDocs(res.data);
      } catch {
        docs = [];
      }
    }
    const confirmed = await confirm({
      title: 'Delete record',
      message: linkedDocsDeleteMessage(docs),
      confirmText: 'Delete',
      type: 'danger'
    });
    if (!confirmed) return;
    try {
      await api.delete(`/${cleanResource}/${currentId}`);
      notify('Record deleted.', 'success');
      if (onDelete) onDelete();
      else if (onCancel) onCancel();
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Delete failed', 'error');
    }
  };

  const handleDuplicate = () => {
    if (!metadata) return;
    const SKIP = new Set(['id', 'number', 'created_at', 'updated_at', 'created_by', 'updated_by', 'status', 'deleted_at']);
    const readOnlyOrComputed = new Set(
      metadata.fields.filter((f: any) => f.read_only || f.type === 'computed').map((f: any) => f.name)
    );
    const duplicateData: Record<string, any> = {};
    for (const [k, v] of Object.entries(formData)) {
      if (!SKIP.has(k) && !readOnlyOrComputed.has(k)) duplicateData[k] = v;
    }
    // Include child rows stripped of their IDs (will be created fresh on save)
    const childFields = metadata.fields.filter((f: any) => f.type === 'child_table');
    for (const cf of childFields) {
      const rows = childRows[cf.name];
      if (rows?.length) {
        duplicateData[cf.name] = rows.map(({ id: _id, ...row }: any) => row);
      }
    }
    const cleanResource = metadata.api_path || cleanResourcePath(resource);
    navigate(`/${cleanResource}/new`, { state: { initialData: duplicateData } });
  };

  const resolveChildApiPath = (field: Field): string => {
    if (field.target_api_path) return cleanResourcePath(field.target_api_path);

    const targetResource = cleanResourcePath(field.target_resource || field.name);
    if (targetResource.includes('/')) return targetResource;

    const parentApiPath = metadata?.api_path || cleanResourcePath(resource);
    const parentPathParts = parentApiPath.split('/').filter(Boolean);
    const parentAppPath = parentPathParts.slice(0, -1);
    if (parentAppPath.length === 0 || !targetResource.includes('_')) return targetResource;

    const appPrefix = parentAppPath.join('_').replace(/-/g, '_');
    const parentPrefix = parentAppPath[0]?.replace(/-/g, '_');
    let childSegment = targetResource;
    if (childSegment.startsWith(`${appPrefix}_`)) {
      childSegment = childSegment.slice(appPrefix.length + 1);
    } else if (parentPrefix && childSegment.startsWith(`${parentPrefix}_`)) {
      childSegment = childSegment.slice(parentPrefix.length + 1);
    }

    return `${parentAppPath.join('/')}/${childSegment.replace(/_/g, '-')}`;
  };

  const handleModelAction = async (action: ModelAction) => {
    if (action.has_input_schema && action.input_fields?.length) {
      const initial: Record<string, any> = {};
      action.input_fields.forEach(f => { initial[f.name] = ''; });
      setActionDialog({ action, inputData: initial });
      return;
    }

    const ok = await confirm({
      title: action.label,
      message: `Are you sure you want to execute "${action.label}"?`,
      type: 'primary'
    });
    if (!ok) return;
    await _runAction(action, undefined);
  };

  const _runAction = async (action: ModelAction, inputData: Record<string, any> | undefined) => {
    setSaving(true);
    try {
      const cleanResource = cleanResourcePath(resource);
      const response = await api.post(`/${cleanResource}/${currentId}/action/${action.name}`, inputData ?? {});
      const result = response.data?.result?.data ?? response.data?.result ?? response.data;
      if (result?.prefill_field && Array.isArray(result.rows)) {
        setChildRows(prev => ({
          ...prev,
          [result.prefill_field]: result.rows
        }));
      }
      if (result?.redirect) {
        navigate(result.redirect);
        return;
      }
      notify(`${action.label} completed successfully`, "success");
      setRefreshTrigger(prev => prev + 1);
    } catch (err: any) {
      notify(err.response?.data?.detail || "Action failed", "error");
    } finally {
      setSaving(false);
    }
  };

  const validateClient = (): Record<string, string> => {
    const errs: Record<string, string> = {};
    if (!metadata) return errs;
    for (const field of metadata.fields) {
      if (!isFieldVisible(field)) continue;
      const val = formData[field.name];
      const empty = val === null || val === undefined || val === '';
      if (field.required && !field.read_only && empty) {
        errs[field.name] = `${vocabulary.get(field.label)} is required`;
        continue;
      }
      if (empty) continue;
      const str = String(val);
      if (field.min_length !== undefined && str.length < field.min_length)
        errs[field.name] = `Minimum ${field.min_length} characters`;
      else if (field.max_length !== undefined && str.length > field.max_length)
        errs[field.name] = `Maximum ${field.max_length} characters`;
      else if ((field.min_value ?? field.min) !== undefined && Number(val) < Number(field.min_value ?? field.min))
        errs[field.name] = `Minimum value is ${field.min_value ?? field.min}`;
      else if ((field.max_value ?? field.max) !== undefined && Number(val) > Number(field.max_value ?? field.max))
        errs[field.name] = `Maximum value is ${field.max_value ?? field.max}`;
      else if (field.pattern && !new RegExp(field.pattern).test(str))
        errs[field.name] = `Invalid format`;
    }
    return errs;
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const clientErrors = validateClient();
    if (Object.keys(clientErrors).length > 0) {
      setErrors(clientErrors);
      notify('Please correct validation errors', 'error');
      return;
    }
    try {
      setSaving(true);
      const cleanResource = metadata?.api_path || cleanResourcePath(resource);
      const m2mFields = metadata?.fields.filter(f => f.type === 'm2m') ?? [];
      const payload = { ...formData };
      m2mFields.forEach(field => delete payload[field.name]);
      let res: { data?: any };
      if (currentId != null) {
        res = await api.patch(`/${cleanResource}/${currentId}`, payload);
      } else {
        const childFields = metadata?.fields.filter(f => f.type === 'child_table') ?? [];
        const children = Object.entries(childRows).flatMap(([fieldName, rows]) => {
          const childField = childFields.find(f => f.name === fieldName);
          if (!childField?.target_resource) return [];
          const editableFields = rows.length > 0 ? Object.keys(rows[0]).map(name => ({ name })) : [];
          const filteredRows = filterEmptyChildRows(rows, editableFields);
          if (filteredRows.length !== rows.length) notify(`${rows.length - filteredRows.length} empty child row(s) discarded`, 'warning');
          const childRes = resolveChildApiPath(childField);
          return filteredRows.map(row => {
            const { __aras_empty_row, ...data } = row;
            return { resource: childRes, data };
          });
        });
        res = children.length > 0
          ? await api.post(`/${cleanResource}/batch`, { parent: payload, children })
          : await api.post(`/${cleanResource}`, payload);
        if (res.data?.id != null) setCurrentId(res.data.id);
        // Merge server response into formData so server-generated fields (number, etc.) appear immediately
        if (res.data && typeof res.data === 'object') setFormData((prev: any) => ({ ...prev, ...(res.data as Record<string, any>) }));
        const childErrors = res.data?.child_errors || res.data?.errors;
        if (childErrors) {
          setErrors(prev => ({ ...prev, children: Array.isArray(childErrors) ? childErrors.join(', ') : String(childErrors) }));
          notify('Some child rows failed to save', 'error');
        }
      }
      const savedId = res.data?.id ?? currentId;
      for (const field of m2mFields) {
        const before = initialM2mRef.current[field.name] ?? [];
        const after = Array.isArray(formData[field.name]) ? formData[field.name] : [];
        const add = after.filter((id: any) => !before.includes(id));
        const remove = before.filter((id: any) => !after.includes(id));
        if (savedId != null && (add.length > 0 || remove.length > 0)) {
          await api.post(`/${cleanResource}/${savedId}/m2m/${field.name}`, { add, remove });
          initialM2mRef.current[field.name] = after;
        }
      }
      // Sync child rows: delete removed, patch existing, post new
      for (const [fieldName, rows] of Object.entries(childRows)) {
        if (currentId == null) continue;
        const childField = metadata?.fields.find(f => f.name === fieldName);
        if (!childField?.target_resource) continue;
        const editableFields = Object.keys(rows[0] ?? {}).map(name => ({ name }));
        const filteredRows = filterEmptyChildRows(rows, editableFields);
        if (filteredRows.length !== rows.length) notify(`${rows.length - filteredRows.length} empty child row(s) discarded`, 'warning');
        const fkKey = childField.fk_column || `${cleanResource.split('/').pop()}_id`;
        const childRes = resolveChildApiPath(childField);
        // Delete rows that existed at load but are no longer present
        const initialIds = initialChildRowIdsRef.current[fieldName] ?? new Set();
        const currentIds = new Set(filteredRows.map((r: any) => r.id).filter(Boolean));
        for (const removedId of initialIds) {
          if (!currentIds.has(removedId)) {
            try {
              await api.delete(`/${childRes}/${removedId}`);
            } catch (e: any) {
              if (e.response?.status !== 404) throw e;
            }
          }
        }
        for (const row of filteredRows) {
          const { __aras_empty_row, ...rowData } = row;
          if (row.id) {
            await api.patch(`/${childRes}/${row.id}`, { ...rowData, [fkKey]: savedId });
          } else {
            await api.post(`/${childRes}`, { ...rowData, [fkKey]: savedId });
          }
        }
        // Update baseline so a subsequent save doesn't re-delete already-removed rows
        initialChildRowIdsRef.current[fieldName] = currentIds;
      }
      invalidateInlineLookupCache();
      const isOrganizationResource = cleanResourcePath(resource).includes('organizations') || cleanResource.includes('config/organizations');
      if (isOrganizationResource) {
        const savedOrgId = Number(res.data?.id ?? savedId ?? formData.id);
        setOrganizations(organizations.map((organization) => (
          organization.id === savedOrgId
            ? {
                ...organization,
                profile: formData.profile ?? organization.profile,
                unit_type: formData.unit_type ?? organization.unit_type,
              }
            : organization
        )));
        vocabularyCache.delete(savedOrgId);
      }
      notify('Record saved successfully', 'success');
      if (onSave) onSave(res.data);
    } catch (err: any) {
      if (err.response?.status === 422) {
        const valErrors: Record<string, string> = {};
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          detail.forEach((d: any) => {
            // Pydantic usually gives ["body", "field_name"]
            const field = (d.loc && d.loc.length > 1) ? d.loc[1] : 'base';
            valErrors[field] = d.msg;
          });
        } else if (typeof detail === 'string') {
          valErrors['base'] = detail;
        } else {
          valErrors['base'] = "Please check your input data.";
        }
        setErrors(valErrors);
        notify("Please correct validation errors", "error");
      } else {
        notify(err.response?.data?.detail || "Failed to save record", "error");
      }
    } finally {
      setSaving(false);
    }
  };

  handleSubmitRef.current = () => handleSubmit();

  if (metadataLoading) return (
    <div className="p-8 flex items-center justify-center text-slate-400 text-sm animate-pulse">
      Loading metadata...
    </div>
  );
  if (!metadata) return (
    <div className="p-8">
      <div className="bg-rose-50 border border-rose-100 rounded-3xl p-6 flex items-start gap-4 shadow-sm">
        <AlertCircle className="text-rose-500 shrink-0 mt-0.5" size={24} />
        <div>
          <h3 className="text-sm font-bold text-rose-700">Metadata could not be loaded</h3>
          <p className="mt-1 text-sm text-rose-600">{metadataError || 'Metadata not found.'}</p>
        </div>
      </div>
    </div>
  );

  if (loading) {
    const visibleFields = metadata.fields.filter(f => !f.hidden && !f.form_hidden && f.type !== 'child_table');
    const childTableFields = metadata.fields.filter(f => f.type === 'child_table');

    return (
      <div className="p-8 space-y-6 animate-pulse">
        {/* Skeleton for Header */}
        <div className="flex items-center justify-between bg-white/80 backdrop-blur-md p-4 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 bg-slate-200 rounded-xl" />
            <div>
              <div className="h-5 w-48 bg-slate-200 rounded-md mb-1" />
              <div className="h-3 w-32 bg-slate-200 rounded-md" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-9 w-20 bg-slate-200 rounded-xl" />
            <div className="h-9 w-24 bg-indigo-200 rounded-xl" />
          </div>
        </div>

        {/* Skeleton for Main Form Content */}
        <div className="space-y-6">
          {metadata.layout && metadata.layout.length > 0 ? (
            metadata.layout.map((section, idx) => {
              if (section.type === 'linked_list') {
                return (
                  <div key={idx} className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="px-8 py-4 bg-slate-50 border-b border-slate-100">
                      <div className="h-4 w-32 bg-slate-200 rounded" />
                    </div>
                    <div className="p-8">
                      <div className="h-40 w-full bg-slate-100 rounded-lg" />
                    </div>
                  </div>
                );
              }
              const fieldNames = 'tabs' in section ? section.tabs.flatMap(t => t.fields) : section.fields;
              const sectionFields = fieldNames
                .map(fieldName => metadata.fields.find(f => f.name === fieldName))
                .filter((f): f is Field => !!f);
              const normalFields = sectionFields.filter(f => !f.hidden && !f.form_hidden && f.type !== 'child_table');
              const childFields = sectionFields.filter(f => f.type === 'child_table');

              return (
                <React.Fragment key={idx}>
                  {normalFields.length > 0 && (
                    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                      <div className="px-8 py-4 bg-slate-50 border-b border-slate-100">
                        <div className="h-4 w-32 bg-slate-200 rounded" />
                      </div>
                      <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                        {normalFields.map((_f, i) => (
                          <div key={i} className="space-y-2">
                            <div className="h-3 w-24 bg-slate-200 rounded" />
                            <div className="h-9 w-full bg-slate-200 rounded" />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {childFields.map((_f, i) => (
                    <div key={i} className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8 space-y-4">
                      <div className="h-4 w-48 bg-slate-200 rounded" /> {/* Section title skeleton */}
                      <div className="space-y-3"> {/* Container for multiple row skeletons */}
                        <div className="h-10 w-full bg-slate-100 rounded-lg" /> {/* Row 1 skeleton */}
                        <div className="h-10 w-full bg-slate-100 rounded-lg" /> {/* Row 2 skeleton */}
                        <div className="h-10 w-full bg-slate-100 rounded-lg" /> {/* Row 3 skeleton */}
                      </div>
                    </div>
                  ))}
                </React.Fragment>
              );
            })
          ) : (
            <>
              {visibleFields.length > 0 && (
                <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                  <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                    {visibleFields.map((_f, i) => (
                      <div key={i} className="space-y-2">
                        <div className="h-3 w-24 bg-slate-200 rounded" />
                        <div className="h-9 w-full bg-slate-200 rounded" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {childTableFields.map((_f, i) => (
                <div key={i} className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8 space-y-4">
                  <div className="h-4 w-48 bg-slate-200 rounded" /> {/* Section title skeleton */}
                  <div className="space-y-3"> {/* Container for multiple row skeletons */}
                    <div className="h-10 w-full bg-slate-100 rounded-lg" /> {/* Row 1 skeleton */}
                    <div className="h-10 w-full bg-slate-100 rounded-lg" /> {/* Row 2 skeleton */}
                    <div className="h-10 w-full bg-slate-100 rounded-lg" /> {/* Row 3 skeleton */}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    );
  }
  if (!metadata) return null;
  const metadataTitle = vocabulary.get(metadata.title);

  const renderField = (field: Field) => {
    if (!isFieldVisible(field)) return null;
    
    // Handle Child Tables inline
    if (field.type === 'child_table') {
      const parentApiPath = metadata?.api_path || cleanResourcePath(resource);
      const fkKey = field.fk_column || `${parentApiPath.split('/').pop()}_id`;
      const childApiPath = resolveChildApiPath(field);
      return (
        <InlineChildTable
          key={`${field.name}-${refreshTrigger}`}
          childResource={childApiPath}
          fkColumn={fkKey}
          parentId={currentId}
          parentData={formData}
          rows={childRows[field.name] ?? []}
          onChange={(rows) => handleLinesChange(field.name, rows)}
        />
      );
    }

    if (field.name === 'stock_by_location') {
      const rows: { location_name: string; qty: number }[] =
        Array.isArray(formData[field.name]) ? formData[field.name] : [];
      return (
        <div key={field.name} className="flex flex-col gap-1.5 md:col-span-2">
          <label className="text-sm font-bold text-slate-700">Stock by Location</label>
          {rows.length === 0
            ? <p className="text-sm text-slate-400 italic">No stock recorded</p>
            : (
              <table className="w-full text-sm border border-slate-200 rounded-xl overflow-hidden">
                <thead className="bg-slate-50 text-slate-600 text-xs uppercase">
                  <tr>
                    <th className="px-3 py-2 text-left font-semibold">Location</th>
                    <th className="px-3 py-2 text-right font-semibold">Qty on Hand</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                      <td className="px-3 py-2">{r.location_name}</td>
                      <td className="px-3 py-2 text-right font-mono text-slate-800">{r.qty}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )
          }
        </div>
      );
    }

    if (field.name === 'note_id') {
      const noteId = formData[field.name];
      return (
        <div key={field.name} className="flex flex-col gap-1.5 md:col-span-2">
          <label className="text-sm font-bold text-slate-700">Notes</label>
          <textarea
            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm resize-none focus:ring-2 focus:ring-indigo-500 outline-none"
            rows={3}
            placeholder="Add a note..."
            defaultValue={formData['notes'] ?? ''}
            onBlur={async (e) => {
              const content = e.target.value.trim();
              if (!content) return;
              if (noteId) {
                await api.patch(`/erp/core/notes/${noteId}`, { content });
              } else if (currentId) {
                const res = await api.post(`/erp/core/notes`, {
                  resource: metadata?.resource,
                  record_id: currentId,
                  content,
                });
                handleChange(field.name, res.data?.data?.id);
              }
            }}
          />
        </div>
      );
    }

    const Component = resolveFieldComponent(field);
    const fieldLabel = vocabulary.get(field.label);

    const fieldForComponent = { ...field, label: fieldLabel };
    const isDocNumberField = field.name === 'number' && metadata?.is_document;
    const isOrganizationField = (field.name === 'org_id') && organizations.length > 0;
    const isProfileField = field.name === 'profile';
    const isUnitTypeField = field.name === 'unit_type';
    const isTerminalLabelField = field.name === 'terminal_label';
    const selectedProfile = PROFILE_OPTIONS.find(option => option.value === formData[field.name]);
    const ProfileIcon = selectedProfile?.icon || Building2;

    return (
      <div key={field.name} className={`flex flex-col gap-1.5 ${field.type === 'textarea' ? 'md:col-span-2' : ''}`}>
        <label className="text-sm font-bold text-slate-700 flex items-center gap-1">
          {fieldLabel}
          {field.required && <span className="text-rose-500">*</span>}
        </label>

        {isDocNumberField ? (
          <div className="w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-xl text-sm text-slate-500 select-none">
            {formData[field.name] ? String(formData[field.name]) : (nextSeriesNumber ?? '[Auto-generated]')}
          </div>
        ) : field.type === 'm2m' && field.target_resource ? (
          <MultiSelectCombobox
            resource={field.target_resource}
            value={Array.isArray(formData[field.name]) ? formData[field.name] : []}
            onChange={(val) => handleChange(field.name, val)}
            placeholder={`Select ${fieldLabel}...`}
            disabled={field.read_only}
          />
        ) : isOrganizationField ? (
          <select
            value={formData[field.name] ?? ''}
            onChange={(e) => handleChange(field.name, e.target.value ? Number(e.target.value) : null)}
            disabled={organizations.length === 1}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none disabled:opacity-60"
          >
            {organizations.length > 1 && <option value="">Select organization...</option>}
            {organizations.map((organization) => <option key={organization.id} value={organization.id}>{organization.name}</option>)}
          </select>
        ) : isProfileField ? (
          <div className="relative">
            <ProfileIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" size={16} />
            <select
              value={formData[field.name] || 'general'}
              onChange={(e) => handleChange(field.name, e.target.value)}
              disabled={field.read_only}
              className="w-full appearance-none px-3 py-2 pl-9 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none disabled:opacity-60"
            >
              {PROFILE_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
        ) : isUnitTypeField ? (
          <select
            value={formData[field.name] || 'organization'}
            onChange={(e) => handleChange(field.name, e.target.value)}
            disabled={field.read_only}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none disabled:opacity-60"
          >
            {UNIT_TYPE_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        ) : isTerminalLabelField ? (
          <input
            type="text"
            value={formData[field.name] || ''}
            onChange={(e) => handleChange(field.name, e.target.value)}
            disabled={field.read_only}
            className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all placeholder:text-slate-300"
            placeholder={`${TERMINAL_PLACEHOLDERS[vocabulary.profile] || vocabulary.pot}...`}
          />
        ) : (
          <Component
            field={fieldForComponent}
            value={formData[field.name]}
            onChange={(val) => handleChange(field.name, val)}
            formData={formData}
            disabled={field.read_only}
          />
        )}
        
        {errors[field.name] && (
          <span className="text-[10px] font-bold text-rose-500 uppercase tracking-wider">{errors[field.name]}</span>
        )}
      </div>
    );
  };

  return (
    <>
    <div className="max-w-6xl mx-auto space-y-6 pb-20">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between bg-white/80 backdrop-blur-md p-4 rounded-2xl border border-slate-200 shadow-sm sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <button 
            onClick={onCancel}
            className="p-2 hover:bg-slate-50 rounded-xl text-slate-500 transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900">
                {currentId != null ? `Edit ${metadataTitle}` : `New ${metadataTitle}`}
              </h2>
              {formData.status && (
                <span className="px-2 py-0.5 bg-indigo-50 text-indigo-600 text-[10px] font-bold rounded-md border border-indigo-100 uppercase tracking-widest">
                  {formData.status}
                </span>
              )}
            </div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-widest">
              Resource: {resourceSubtitle || resource}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* History Button */}
          {currentId != null && metadata.is_auditable && (
            <button
              onClick={handleShowHistory}
              className="p-2 hover:bg-slate-50 rounded-xl text-slate-500 transition-colors mr-2"
              title="View History"
            >
              <HistoryIcon size={20} />
            </button>
          )}

          {/* Customize Button */}
          <button
            onClick={handleCustomize}
            className="p-2 hover:bg-slate-50 rounded-xl text-slate-500 transition-colors mr-2"
            title="Customize Form"
          >
            <Settings size={20} />
          </button>

          {currentId != null && (
            <button
              onClick={handleDelete}
              title="Delete record"
              className="p-2 hover:bg-rose-50 rounded-xl text-rose-400 hover:text-rose-600 transition-colors"
            >
              <Trash2 size={20} />
            </button>
          )}
          {currentId != null && (
            <button onClick={handleDuplicate} title="Duplicate record"
              className="p-2 hover:bg-indigo-50 rounded-xl text-indigo-400 hover:text-indigo-600 transition-colors">
              <Copy size={20} />
            </button>
          )}
          {currentId != null && (
            <>
              <button
                onClick={() => prevId && onNavigate?.(prevId)}
                disabled={!prevId}
                title="Previous record"
                className="p-2 hover:bg-slate-50 rounded-xl text-slate-400 disabled:opacity-30 transition-colors"
              >
                <ChevronLeft size={20} />
              </button>
              <button
                onClick={() => nextId && onNavigate?.(nextId)}
                disabled={!nextId}
                title="Next record"
                className="p-2 hover:bg-slate-50 rounded-xl text-slate-400 disabled:opacity-30 transition-colors"
              >
                <ChevronRight size={20} />
              </button>
            </>
          )}

          {/* Model Actions */}
          {currentId != null && metadata.actions?.map(action => (
            <button
              key={action.name}
              onClick={() => handleModelAction(action)}
              disabled={saving}
              className="p-2 hover:bg-indigo-50 rounded-xl text-indigo-600 transition-colors"
              title={action.label}
            >
              <Zap size={20} />
            </button>
          ))}

          {/* Workflow Actions */}
          {workflowActions.map(action => (
            <button
              key={action.name}
              onClick={() => handleWorkflowAction(action.name)}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-xl text-sm font-bold hover:bg-slate-50 transition-all"
            >
              <span>{action.label}</span>
              <ChevronRight size={14} />
            </button>
          ))}

          {(workflowActions.length > 0 || (metadata.actions?.length ?? 0) > 0 || (metadata.app_name === 'erp_accounting' && currentId != null)) && <div className="w-px h-6 bg-slate-200 mx-1" />}

          {/* Print Button */}
          {metadata.app_name === 'erp_accounting' && currentId != null && (
            <button
              onClick={() => setShowPrintPreview(true)}
              className="p-2 hover:bg-slate-50 rounded-xl text-slate-500 transition-colors mr-2"
              title="Print Document"
            >
              <Printer size={20} />
            </button>
          )}

          <button 
            type="button" 
            onClick={onCancel}
            className="px-4 py-2 text-sm font-bold text-slate-600 hover:bg-slate-50 rounded-xl transition-all"
          >
            Cancel
          </button>
          <button 
            onClick={() => handleSubmit()}
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-xl text-sm font-bold hover:bg-indigo-700 transition-all shadow-md shadow-indigo-100 disabled:opacity-50"
          >
            {saving ? <RefreshCw className="animate-spin" size={18} /> : <Save size={18} />}
            <span>{saving ? 'Saving...' : 'Save Changes'}</span>
          </button>
        </div>
      </div>

      {/* ── Main Form Content ────────────────────────────────────────────── */}
      <div className="space-y-6">
        {/* General Errors (errors not mapping to visible fields or mapping to hidden fields) */}
        {Object.entries(errors).filter(([key]) => {
          const field = metadata.fields.find(f => f.name === key);
          return !field || !isFieldVisible(field);
        }).length > 0 && (
          <div className="bg-rose-50 border border-rose-100 rounded-3xl p-6 flex items-start gap-4">
            <AlertCircle className="text-rose-500 shrink-0 mt-0.5" size={24} />
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-rose-700">Please correct the following:</h4>
              <ul className="list-disc list-inside text-xs text-rose-600 space-y-1">
                {Object.entries(errors)
                  .filter(([key]) => {
                    const field = metadata.fields.find(f => f.name === key);
                    return !field || !isFieldVisible(field);
                  })
                  .map(([key, msg]) => (
                    <li key={key}>
                      <span className="font-bold uppercase tracking-tight mr-1">{key.replace(/_/g, ' ')}:</span> {msg}
                    </li>
                  ))}
              </ul>
            </div>
          </div>
        )}

        {metadata.layout && metadata.layout.length > 0 ? (
          metadata.layout.map((entry, idx) => {
            if (entry.type === 'linked_list') {
              if (currentId == null) return null;
              return (
                <div key={idx} className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                  <div className="px-8 py-4 bg-slate-50 border-b border-slate-100">
                    <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider">{vocabulary.get(entry.title)}</h3>
                  </div>
                  <div className="p-6">
                    <ListView
                      resource={entry.resource}
                      fixedFilters={{ [entry.fk_field]: currentId }}
                      onRowClick={(id) => navigate('/' + entry.resource + '/' + id)}
                    />
                  </div>
                </div>
              );
            }

            if ('tabs' in entry) {
              // Tab group
              const currentTab = activeTab[idx] ?? 0;
              const tab = entry.tabs[currentTab];
              const tabFields = (tab?.fields ?? [])
                .map(name => metadata.fields.find(f => f.name === name))
                .filter((f): f is Field => !!f);
              const normalFields = tabFields.filter(f => f.type !== 'child_table');
              const childTableFields = tabFields.filter(f => f.type === 'child_table');

              return (
                <div key={idx} className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                  <div className="flex border-b border-slate-200 bg-slate-50">
                    {entry.tabs.map((t, ti) => (
                      <button
                        key={ti}
                        type="button"
                        onClick={() => setActiveTab(prev => ({ ...prev, [idx]: ti }))}
                        className={`px-6 py-3 text-sm font-semibold transition-colors ${currentTab === ti ? 'text-indigo-600 border-b-2 border-indigo-600 bg-white' : 'text-slate-500 hover:text-slate-700'}`}
                      >
                        {vocabulary.get(t.title)}
                      </button>
                    ))}
                  </div>
                  {normalFields.length > 0 && (
                    <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                      {normalFields.map(renderField)}
                    </div>
                  )}
                  {childTableFields.map(renderField)}
                </div>
              );
            }

            // Regular section
            const section = entry as LayoutSection;
            const sectionFields = section.fields
              .map(fieldName => metadata.fields.find(f => f.name === fieldName))
              .filter((f): f is Field => !!f);
            const normalFields = sectionFields.filter(f => f.type !== 'child_table');
            const childTableFields = sectionFields.filter(f => f.type === 'child_table');

            return (
              <React.Fragment key={idx}>
                {normalFields.length > 0 && (
                  <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="px-8 py-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                      <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider">{vocabulary.get(section.title)}</h3>
                      {currentId != null && section.actions && section.actions.length > 0 && (
                        <div className="flex items-center gap-2">
                          {section.actions.map(actionName => {
                            const act = metadata.actions?.find(a => a.name === actionName);
                            if (!act) return null;
                            return (
                              <button
                                key={act.name}
                                onClick={() => handleModelAction(act)}
                                disabled={saving}
                                className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors"
                                title={act.label}
                              >
                                <Zap size={12} />
                                {act.label}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                    <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                      {normalFields.map(renderField)}
                    </div>
                  </div>
                )}
                {childTableFields.map(renderField)}
              </React.Fragment>
            );
          })
        ) : (          <>
            {metadata.fields.filter(f => f.type !== 'child_table').length > 0 && (
              <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                  {metadata.fields.filter(f => f.type !== 'child_table').map(renderField)}
                </div>
              </div>
            )}
            {metadata.fields.filter(f => f.type === 'child_table').map(renderField)}
          </>
        )}
        {/* Render child_table fields not covered by the layout */}
        {metadata.layout && metadata.layout.length > 0 && (() => {
          const layoutFieldNames = new Set(
            metadata.layout.flatMap((entry: any) =>
              'tabs' in entry
                ? entry.tabs.flatMap((t: any) => t.fields ?? [])
                : entry.fields ?? []
            )
          );
          return metadata.fields
            .filter(f => f.type === 'child_table' && !layoutFieldNames.has(f.name))
            .map(renderField);
        })()}
      </div>

      {/* ── Linked Documents ── */}
      {linkedDocs.length > 0 && (
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-8 py-4 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
            <Link2 size={14} className="text-slate-400" />
            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider">Linked Documents</h3>
          </div>
          <div className="p-6 flex flex-wrap gap-3">
            {linkedDocs.map(doc => (
              <button
                key={`${doc.resource}-${doc.id}`}
                type="button"
                onClick={() => navigate(`/${doc.resource}/${doc.id}`)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-indigo-50 hover:border-indigo-200 text-sm font-medium text-slate-700 hover:text-indigo-700 transition-colors"
              >
                <span className="text-xs text-slate-400 font-normal">{doc.label}</span>
                <span className="font-semibold">{doc.number}</span>
                <ArrowUpRight size={13} className="text-slate-400" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Child Tables Section (Fallback for children not in fields list) ── */}
      {metadata.children && metadata.children.length > 0 && (
        <div className="space-y-6">
          {metadata.children
            .filter(child => !metadata.fields.some(f => 
              f.type === 'child_table' && 
              (cleanResourcePath(f.target_resource || '') === cleanResourcePath(child.resource) || cleanResourcePath(f.name) === cleanResourcePath(child.resource))
            ))
            .map((child) => {
              const parentResourceKey = cleanResourcePath(metadata.resource).split('/').pop();
              const fkKey = child.fk_column || `${parentResourceKey}_id`;
              return (
                <InlineChildTable
                  key={`${child.resource}-${refreshTrigger}`}
                  childResource={child.resource}
                  fkColumn={fkKey}
                  parentId={currentId}
                  parentData={formData}
                  rows={childRows[child.resource] ?? []}
                  onChange={(rows) => setChildRows(prev => ({ ...prev, [child.resource]: rows }))}
                />
              );
            })}
        </div>
      )}
    </div>

    {/* ── Action Input Dialog ───────────────────────────────────────────── */}
    {actionDialog && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
        <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md space-y-4">
          <h3 className="text-lg font-semibold text-slate-900">{actionDialog.action.label}</h3>
          <div className="space-y-3">
            {actionDialog.action.input_fields?.map(field => (
              <div key={field.name}>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  {field.label}{field.required && <span className="text-red-500 ml-0.5">*</span>}
                </label>
                <input
                  type={field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text'}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                  value={actionDialog.inputData[field.name] ?? ''}
                  onChange={e => setActionDialog(prev => prev && ({
                    ...prev,
                    inputData: { ...prev.inputData, [field.name]: e.target.value }
                  }))}
                />
              </div>
            ))}
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={() => setActionDialog(null)}
              className="px-4 py-2 text-sm rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors"
            >
              Cancel
            </button>
            <button
              disabled={saving}
              onClick={async () => {
                const { action, inputData } = actionDialog;
                setActionDialog(null);
                await _runAction(action, inputData);
              }}
              className="px-4 py-2 text-sm rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition-colors disabled:opacity-50"
            >
              {actionDialog.action.label}
            </button>
          </div>
        </div>
      </div>
    )}

    {showPrintPreview && currentId && (
      <PrintPreview
        resource={resource}
        id={currentId}
        onClose={() => setShowPrintPreview(false)}
      />
    )}
    </>
  );
};

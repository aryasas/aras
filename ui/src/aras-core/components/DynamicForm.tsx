import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { useAuthStore } from '../../store/authStore';
import {
  Save, ArrowLeft, RefreshCw, ChevronRight,
  History as HistoryIcon, Zap, Settings, AlertCircle,
  Building2, Store, School, Users, HandHeart, Library, HeartPulse, Landmark, BriefcaseBusiness
} from 'lucide-react';
import ListView from './ListView';
import { InlineChildTable } from './InlineChildTable';
import { SchemaRegistry } from '../services/SchemaRegistry';
import { useAras } from '../hooks/useAras';
import { useUIStore } from '../../store/uiStore';
import { LogicEvaluator } from '../../lib/LogicEvaluator';
import { useVocabulary } from '../../context/VocabularyContext';

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
  fk_column?: string | null;
  options?: { label: string; value: any }[];
  min_length?: number;
  max_length?: number;
  min_value?: number;
  max_value?: number;
  pattern?: string;
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
}

interface Metadata {
  resource: string;
  api_path?: string;
  title: string;
  fields: Field[];
  children?: Array<{ resource: string; fk_column?: string | null }>;
  workflow?: any;
  actions?: ModelAction[];
  layout?: LayoutSection[];
  is_auditable?: boolean;
}

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
  initialData?: any;
  parentResourceTitle?: string;
}

export const DynamicForm: React.FC<DynamicFormProps> = ({
  resource,
  id,
  onSave,
  onCancel,
  initialData,
  parentResourceTitle
}) => {
  const { activeCompanyId, companies } = useAuthStore();
  const vocabulary = useVocabulary();
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [formData, setFormData] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [workflowActions, setWorkflowActions] = useState<WorkflowAction[]>([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [actionDialog, setActionDialog] = useState<{ action: ModelAction; inputData: Record<string, any> } | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [childRows, setChildRows] = useState<Record<string, any[]>>({});
  const [resourceSubtitle, setResourceSubtitle] = useState<string | null>(parentResourceTitle ?? null);
  const [searchParams] = useSearchParams();
  // currentId tracks the actual persisted record ID — updated after POST so child tables appear immediately
  const [currentId, setCurrentId] = useState<number | string | undefined>(() =>
    id != null && id !== 'new' ? id : undefined
  );
  
  const { notify, confirm } = useAras();
  const showPanel = useUIStore((state) => state.showPanel);
  const closePanel = useUIStore((state) => state.closePanel);

  useEffect(() => {
    setCurrentId(id != null && id !== 'new' ? id : undefined);
  }, [id]);

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        const cleanResource = cleanResourcePath(resource);
        
        const metaRes = await api.get(`/metadata/${cleanResource}`);
        const meta = metaRes.data;
        setMetadata(meta);

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
          const resourceApiPath = meta.api_path || cleanResource;
          const dataRes = await api.get(`/${resourceApiPath}/${id}`);
          setFormData(dataRes.data);

          // Load existing child rows for every child_table field
          const childFields = meta.fields.filter((f: any) => f.type === 'child_table' && f.target_resource);
          if (childFields.length > 0) {
            const childData: Record<string, any[]> = {};
            await Promise.all(childFields.map(async (f: any) => {
              try {
                const childRes = f.target_api_path || cleanResourcePath(f.target_resource);
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
          }

          if (meta.workflow) {
            try {
              const actionRes = await api.get(`/workflow/${cleanResource}/${id}/actions`);
              setWorkflowActions(actionRes.data);
            } catch (aErr) {
              console.warn("Could not fetch workflow actions", aErr);
            }
          }
        } else {
          const today = new Date().toISOString().split('T')[0];
          const defaults: any = { ...initialData };
          if (activeCompanyId && !defaults['company_id']) defaults['company_id'] = activeCompanyId;
          if (activeCompanyId && !defaults['org_id']) defaults['org_id'] = activeCompanyId;
          meta.fields.forEach((f: any) => {
             if (defaults[f.name] !== undefined) return;
             if (f.default_value) {
                defaults[f.name] = f.default_value;
                if (f.type === 'number' || f.type === 'currency') defaults[f.name] = Number(f.default_value);
                if (f.type === 'boolean') defaults[f.name] = f.default_value === 'true';
                return;
             }
             if (f.series) {
                // If it's a naming series field, we might want to handle it specially
                // But for now just use it as default if it's not empty
                defaults[f.name] = f.series;
             }

             if (f.type === 'boolean') defaults[f.name] = false;
             else if (f.type === 'number' || f.type === 'currency') defaults[f.name] = 0;
             else if (f.type === 'date') defaults[f.name] = today;
             else if (f.type === 'datetime') defaults[f.name] = new Date().toISOString().split('.')[0];
             else if (f.type === 'lookup') defaults[f.name] = null;
             else defaults[f.name] = '';
          });
          setFormData(defaults);
        }
      } catch (err: any) {
        notify(err.response?.data?.detail || "Failed to load form", "error");
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [resource, id, notify, initialData, refreshTrigger, searchParams, parentResourceTitle, activeCompanyId]);

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
    const cleanResource = cleanResourcePath(resource);
    
    try {
      const res = await api.get('/aras_resources', { params: { name: cleanResource } });
      const resourceRecord = res.data.items[0];
      if (!resourceRecord) {
        notify("Resource record not found in registry", "error");
        return;
      }

      showPanel(
        `Customize: ${vocabulary.get(metadata.title)}`,
        <div className="h-[calc(100vh-150px)]">
          <ListView 
            resource="aras_fields" 
            fixedFilters={{ resource_id: resourceRecord.id }}
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
        </div>,
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
      await api.post(`/${cleanResource}/${currentId}/action/${action.name}`, inputData ?? {});
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
      if (field.required && empty) {
        errs[field.name] = `${vocabulary.get(field.label)} is required`;
        continue;
      }
      if (empty) continue;
      const str = String(val);
      if (field.min_length !== undefined && str.length < field.min_length)
        errs[field.name] = `Minimum ${field.min_length} characters`;
      else if (field.max_length !== undefined && str.length > field.max_length)
        errs[field.name] = `Maximum ${field.max_length} characters`;
      else if (field.min_value !== undefined && Number(val) < field.min_value)
        errs[field.name] = `Minimum value is ${field.min_value}`;
      else if (field.max_value !== undefined && Number(val) > field.max_value)
        errs[field.name] = `Maximum value is ${field.max_value}`;
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
      const payload = { ...formData };
      let res;
      if (currentId != null) {
        res = await api.patch(`/${cleanResource}/${currentId}`, payload);
      } else {
        res = await api.post(`/${cleanResource}`, payload);
        if (res.data?.id != null) setCurrentId(res.data.id);
      }
      const savedId = res.data?.id ?? currentId;
      // POST pending child rows
      for (const [fieldName, rows] of Object.entries(childRows)) {
        const childField = metadata?.fields.find(f => f.name === fieldName);
        if (!childField?.target_resource || rows.length === 0) continue;
        const fkKey = childField.fk_column || `${cleanResource.split('/').pop()}_id`;
        const childRes = (childField as any).target_api_path || cleanResourcePath(childField.target_resource);
        for (const row of rows) {
          if (row.id) {
            await api.patch(`/${childRes}/${row.id}`, { ...row, [fkKey]: savedId });
          } else {
            await api.post(`/${childRes}`, { ...row, [fkKey]: savedId });
          }
        }
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

  if (loading) return (
    <div className="p-8 space-y-5 animate-pulse">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="space-y-2">
          <div className="h-3 w-24 bg-slate-200 dark:bg-slate-700 rounded" />
          <div className="h-9 w-full bg-slate-200 dark:bg-slate-700 rounded" />
        </div>
      ))}
    </div>
  );
  if (!metadata) return <div className="p-12 text-center text-red-500">Metadata not found.</div>;
  const metadataTitle = vocabulary.get(metadata.title);

  const renderField = (field: Field) => {
    if (!isFieldVisible(field)) return null;
    
    // Handle Child Tables inline
    if (field.type === 'child_table') {
      const parentApiPath = metadata?.api_path || cleanResourcePath(resource);
      const fkKey = field.fk_column || `${parentApiPath.split('/').pop()}_id`;
      const childApiPath = (field as any).target_api_path || cleanResourcePath(field.target_resource!);
      return (
        <InlineChildTable
          key={`${field.name}-${refreshTrigger}`}
          childResource={childApiPath}
          fkColumn={fkKey}
          parentId={currentId}
          rows={childRows[field.name] ?? []}
          onChange={(rows) => setChildRows(prev => ({ ...prev, [field.name]: rows }))}
        />
      );
    }

    const Component = SchemaRegistry.get(field.type);
    const fieldLabel = vocabulary.get(field.label);

    const fieldForComponent = { ...field, label: fieldLabel };
    const isOrganizationField = (field.name === 'company_id' || field.name === 'org_id') && companies.length > 0;
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

        {isOrganizationField ? (
          <select
            value={formData[field.name] ?? ''}
            onChange={(e) => handleChange(field.name, e.target.value ? Number(e.target.value) : null)}
            disabled={companies.length === 1}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none disabled:opacity-60"
          >
            {companies.length > 1 && <option value="">Select organization...</option>}
            {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
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

          {(workflowActions.length > 0 || (metadata.actions?.length ?? 0) > 0) && <div className="w-px h-6 bg-slate-200 mx-1" />}

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
          metadata.layout.map((section, idx) => {
            const sectionFields = section.fields
              .map(fieldName => metadata.fields.find(f => f.name === fieldName))
              .filter((f): f is Field => !!f);
              
            const normalFields = sectionFields.filter(f => f.type !== 'child_table');
            const childTableFields = sectionFields.filter(f => f.type === 'child_table');

            return (
              <React.Fragment key={idx}>
                {normalFields.length > 0 && (
                  <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="px-8 py-4 bg-slate-50 border-b border-slate-100">
                      <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider">{vocabulary.get(section.title)}</h3>
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
        ) : (
          <>
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
      </div>

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
    </>
  );
};

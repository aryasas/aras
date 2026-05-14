import React, { useEffect, useState } from 'react';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { 
  Save, ArrowLeft, Plus, RefreshCw, ChevronRight, 
  History as HistoryIcon, Zap
} from 'lucide-react';
import ListView from './ListView';
import { SchemaRegistry } from '../services/SchemaRegistry';
import { useAras } from '../hooks/useAras';
import { useUIStore } from '../../store/uiStore';
import { LogicEvaluator } from '../../lib/LogicEvaluator';

interface Field {
  name: string;
  label: string;
  type: string;
  required: boolean;
  read_only: boolean;
  hidden: boolean;
  depends_on?: string; // Conditional visibility logic
  target_resource?: string;
  options?: { label: string; value: any }[];
}

interface WorkflowAction {
  name: string;
  to: string;
  label: string;
  icon?: string;
}

interface ModelAction {
  name: string;
  label: string;
  icon?: string;
  has_input_schema: boolean;
}

interface LayoutSection {
  title: string;
  fields: string[];
}

interface Metadata {
  resource: string;
  title: string;
  fields: Field[];
  children?: string[];
  workflow?: any;
  actions?: ModelAction[];
  layout?: LayoutSection[];
  is_auditable?: boolean;
}

interface DynamicFormProps {
  resource: string;
  id?: number | string;
  onSave?: (data: any) => void;
  onCancel?: () => void;
  initialData?: any;
}

export const DynamicForm: React.FC<DynamicFormProps> = ({ 
  resource, 
  id, 
  onSave, 
  onCancel, 
  initialData 
}) => {
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [formData, setFormData] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [workflowActions, setWorkflowActions] = useState<WorkflowAction[]>([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const { notify, confirm } = useAras();
  const showPanel = useUIStore((state) => state.showPanel);
  const closePanel = useUIStore((state) => state.closePanel);

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        const cleanResource = cleanResourcePath(resource);
        
        const metaRes = await api.get(`/metadata/${cleanResource}`);
        const meta = metaRes.data;
        setMetadata(meta);

        if (id && id !== 'new') {
          const dataRes = await api.get(`/${cleanResource}/${id}`);
          setFormData(dataRes.data);

          if (meta.workflow) {
            try {
              const actionRes = await api.get(`/workflow/${cleanResource}/${id}/actions`);
              setWorkflowActions(actionRes.data);
            } catch (aErr) {
              console.warn("Could not fetch workflow actions", aErr);
            }
          }
        } else {
          const defaults: any = { ...initialData };
          meta.fields.forEach((f: any) => {
             if (defaults[f.name] !== undefined) return;
             if (f.type === 'boolean') defaults[f.name] = false;
             else if (f.type === 'number' || f.type === 'currency') defaults[f.name] = 0;
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
  }, [resource, id, notify, initialData, refreshTrigger]);

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
    if (!field.depends_on) return true;
    
    return LogicEvaluator.evaluate(field.depends_on, formData);
  };

  const handleShowHistory = () => {
    const cleanResource = cleanResourcePath(resource);
    showPanel(
      `${metadata?.title} Audit Trail`,
      <div className="h-[calc(100vh-150px)]">
        <ListView 
          resource="aras_activity_logs" 
          fixedFilters={{ resource: cleanResource, resource_id: id }}
        />
      </div>,
      'max-w-5xl'
    );
  };

  const handleAddChild = (childResource: string) => {
    const cleanResource = cleanResourcePath(resource);
    showPanel(
      `Add New ${childResource.replace(/_/g, ' ')}`,
      <div className="bg-slate-50 -m-6 p-6 h-[calc(100vh-80px)] overflow-auto">
        <DynamicForm 
          resource={childResource} 
          id="new" 
          initialData={{ [`${cleanResource}_id`]: id }}
          onSave={() => {
            closePanel();
            setRefreshTrigger(prev => prev + 1);
          }}
          onCancel={closePanel}
        />
      </div>,
      'max-w-4xl'
    );
  };

  const handleWorkflowAction = async (actionName: string) => {
    setSaving(true);
    try {
      const cleanResource = cleanResourcePath(resource);
      await api.post(`/workflow/${cleanResource}/${id}/action/${actionName}`);
      notify(`Workflow action completed`, "success");
      setRefreshTrigger(prev => prev + 1);
    } catch (err: any) {
      notify(err.response?.data?.detail || "Workflow action failed", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleModelAction = async (action: ModelAction) => {
    if (action.has_input_schema) {
      // Future: Show dialog with input schema form
      notify("Action requires input schema (not yet implemented in UI)", "info");
      return;
    }

    const ok = await confirm({
      title: action.label,
      message: `Are you sure you want to execute "${action.label}"?`,
      type: 'primary'
    });

    if (!ok) return;

    setSaving(true);
    try {
      const cleanResource = cleanResourcePath(resource);
      await api.post(`/${cleanResource}/${id}/action/${action.name}`);
      notify(`${action.label} completed successfully`, "success");
      setRefreshTrigger(prev => prev + 1);
    } catch (err: any) {
      notify(err.response?.data?.detail || "Action failed", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    try {
      setSaving(true);
      const cleanResource = cleanResourcePath(resource);
      let res;
      if (id && id !== 'new') {
        res = await api.patch(`/${cleanResource}/${id}`, formData);
      } else {
        res = await api.post(`/${cleanResource}`, formData);
      }
      notify('Record saved successfully', 'success');
      if (onSave) onSave(res.data);
    } catch (err: any) {
      if (err.response?.status === 422) {
        const valErrors: Record<string, string> = {};
        err.response.data.detail.forEach((d: any) => {
          if (d.loc && d.loc.length > 1) valErrors[d.loc[1]] = d.msg;
        });
        setErrors(valErrors);
        notify("Please correct validation errors", "error");
      } else {
        notify(err.response?.data?.detail || "Failed to save record", "error");
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-12 text-center animate-pulse text-slate-400">Loading form...</div>;
  if (!metadata) return <div className="p-12 text-center text-red-500">Metadata not found.</div>;

  const renderField = (field: Field) => {
    if (!isFieldVisible(field)) return null;
    const Component = SchemaRegistry.get(field.type);
    
    return (
      <div key={field.name} className={`flex flex-col gap-1.5 ${field.type === 'textarea' ? 'md:col-span-2' : ''}`}>
        <label className="text-sm font-bold text-slate-700 flex items-center gap-1">
          {field.label}
          {field.required && <span className="text-rose-500">*</span>}
        </label>
        
        <Component 
          field={field} 
          value={formData[field.name]} 
          onChange={(val) => handleChange(field.name, val)}
          formData={formData}
          disabled={field.read_only}
        />
        
        {errors[field.name] && (
          <span className="text-[10px] font-bold text-rose-500 uppercase tracking-wider">{errors[field.name]}</span>
        )}
      </div>
    );
  };

  return (
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
                {id && id !== 'new' ? `Edit ${metadata.title}` : `New ${metadata.title}`}
              </h2>
              {formData.status && (
                <span className="px-2 py-0.5 bg-indigo-50 text-indigo-600 text-[10px] font-bold rounded-md border border-indigo-100 uppercase tracking-widest">
                  {formData.status}
                </span>
              )}
            </div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-widest">Resource: {resource}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* History Button */}
          {id && id !== 'new' && metadata.is_auditable && (
            <button
              onClick={handleShowHistory}
              className="p-2 hover:bg-slate-50 rounded-xl text-slate-500 transition-colors mr-2"
              title="View History"
            >
              <HistoryIcon size={20} />
            </button>
          )}

          {/* Model Actions */}
          {id && id !== 'new' && metadata.actions?.map(action => (
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
        {metadata.layout ? (
          metadata.layout.map((section, idx) => (
            <div key={idx} className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-8 py-4 bg-slate-50 border-b border-slate-100">
                <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider">{section.title}</h3>
              </div>
              <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                {section.fields.map(fieldName => {
                  const field = metadata.fields.find(f => f.name === fieldName);
                  return field ? renderField(field) : null;
                })}
              </div>
            </div>
          ))
        ) : (
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              {metadata.fields.map(renderField)}
            </div>
          </div>
        )}
      </div>

      {/* ── Child Tables Section ─────────────────────────────────────────── */}
      {id && id !== 'new' && metadata.children && metadata.children.length > 0 && (
        <div className="space-y-6">
          {metadata.children.map((childResource) => (
            <div key={childResource} className="space-y-3">
               <div className="flex items-center justify-between px-2">
                  <h3 className="text-lg font-bold text-slate-800 uppercase tracking-tight">{childResource.replace(/_/g, ' ')}</h3>
                  <button 
                    onClick={() => handleAddChild(childResource)}
                    className="flex items-center gap-1 text-xs font-bold text-indigo-600 hover:bg-indigo-50 px-3 py-1.5 rounded-lg transition-all"
                  >
                    <Plus size={14} /> Add Line
                  </button>
               </div>
               <div className="h-[400px]">
                 <ListView 
                   key={`${childResource}-${refreshTrigger}`}
                   resource={childResource} 
                   fixedFilters={{ [`${cleanResourcePath(resource)}_id`]: id }}
                 />
               </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

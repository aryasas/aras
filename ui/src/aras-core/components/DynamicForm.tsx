import React, { useEffect, useState } from 'react';
import api from '../../lib/api';
import { 
  Save, ArrowLeft, Plus, RefreshCw, ChevronRight, 
  History as HistoryIcon 
} from 'lucide-react';
import ListView from './ListView';
import Combobox from './Combobox';
import { useUIStore } from '../../store/uiStore';

interface Field {
  name: string;
  label: string;
  type: string;
  required: boolean;
  read_only: boolean;
  hidden: boolean;
  target_resource?: string;
  options?: { label: string; value: any }[];
}

interface WorkflowAction {
  name: string;
  to: string;
  label: string;
  icon?: string;
}

interface Metadata {
  resource: string;
  title: string;
  fields: Field[];
  children?: string[];
  workflow?: any;
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
  const [actions, setActions] = useState<WorkflowAction[]>([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  
  const showAlert = useUIStore((state) => state.showAlert);
  const showError = useUIStore((state) => state.showError);
  const showPanel = useUIStore((state) => state.showPanel);
  const closePanel = useUIStore((state) => state.closePanel);

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        const cleanResource = resource.startsWith('/') ? resource.substring(1) : resource;
        
        const metaRes = await api.get(`/metadata/${cleanResource}`);
        const meta = metaRes.data;
        setMetadata(meta);

        if (id && id !== 'new') {
          const dataRes = await api.get(`/${cleanResource}/${id}`);
          setFormData(dataRes.data);

          if (meta.workflow) {
            try {
              const actionRes = await api.get(`/workflow/${cleanResource}/${id}/actions`);
              setActions(actionRes.data);
            } catch (aErr) {
              console.warn("Could not fetch workflow actions", aErr);
            }
          }
        } else {
          // Initialize with defaults from metadata + initialData
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
        showError("Load Error", err.response?.data?.detail || "Failed to load form");
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [resource, id, showError, initialData, refreshTrigger]);

  const handleChange = (name: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [name]: value }));
  };

  const handleShowHistory = () => {
    const cleanResource = resource.startsWith('/') ? resource.substring(1) : resource;
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
    const cleanResource = resource.startsWith('/') ? resource.substring(1) : resource;
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

  const handleAction = async (actionName: string) => {
    setSaving(true);
    try {
      const cleanResource = resource.startsWith('/') ? resource.substring(1) : resource;
      await api.post(`/workflow/${cleanResource}/${id}/action/${actionName}`);
      showAlert('Success', `Action completed successfully`);
      
      // Refresh data and actions
      const dataRes = await api.get(`/${cleanResource}/${id}`);
      setFormData(dataRes.data);
      const actionRes = await api.get(`/workflow/${cleanResource}/${id}/actions`);
      setActions(actionRes.data);
    } catch (err: any) {
      showError("Action Failed", err.response?.data?.detail || "Could not trigger workflow action");
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    try {
      setSaving(true);
      const cleanResource = resource.startsWith('/') ? resource.substring(1) : resource;
      let res;
      if (id && id !== 'new') {
        res = await api.patch(`/${cleanResource}/${id}`, formData);
      } else {
        res = await api.post(`/${cleanResource}`, formData);
      }
      showAlert('Success', 'Record saved successfully');
      if (onSave) onSave(res.data);
    } catch (err: any) {
      showError("Save Error", err.response?.data?.detail || "Failed to save record");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-12 text-center animate-pulse text-slate-400">Loading form...</div>;
  if (!metadata) return <div className="p-12 text-center text-red-500">Metadata not found.</div>;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-20">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between bg-white p-4 rounded-2xl border border-slate-200 shadow-sm sticky top-0 z-20">
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

          {/* Workflow Actions */}
          {actions.map(action => (
            <button
              key={action.name}
              onClick={() => handleAction(action.name)}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-xl text-sm font-bold hover:bg-slate-50 transition-all"
            >
              <span>{action.label}</span>
              <ChevronRight size={14} />
            </button>
          ))}

          {actions.length > 0 && <div className="w-px h-6 bg-slate-200 mx-1" />}

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

      {/* ── Main Form Grid ────────────────────────────────────────────────── */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          {metadata.fields.map((field) => {
            if (field.hidden) return null;

            return (
              <div key={field.name} className={`flex flex-col gap-1.5 ${field.type === 'textarea' ? 'md:col-span-2' : ''}`}>
                <label className="text-sm font-bold text-slate-700 flex items-center gap-1">
                  {field.label}
                  {field.required && <span className="text-rose-500">*</span>}
                </label>
                
                {renderInput(field, formData[field.name], (val) => handleChange(field.name, val))}
              </div>
            );
          })}
        </div>
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
                   fixedFilters={{ [`${resource.startsWith('/') ? resource.substring(1) : resource}_id`]: id }}
                 />
               </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const renderInput = (field: Field, value: any, onChange: (val: any) => void) => {
  const commonClass = "w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all placeholder:text-slate-300";
  
  if (field.read_only) {
    return (
      <div className={`${commonClass} bg-slate-100 text-slate-500 cursor-not-allowed font-medium`}>
        {value || '-'}
      </div>
    );
  }

  switch (field.type) {
    case 'lookup':
      return (
        <Combobox 
          resource={field.target_resource || ''} 
          value={value} 
          onChange={onChange} 
          placeholder={`Select ${field.label}...`}
        />
      );
    case 'select':
      return (
        <select
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          className={commonClass}
        >
          <option value="">Select {field.label}...</option>
          {field.options?.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      );
    case 'textarea':
      return <textarea 
        rows={4}
        value={value || ''} 
        onChange={(e) => onChange(e.target.value)}
        className={commonClass}
        placeholder={`Enter ${field.label.toLowerCase()}...`}
      />;
    case 'boolean':
      return (
        <label className="flex items-center gap-3 py-2 cursor-pointer group">
          <div className="relative">
            <input 
              type="checkbox"
              checked={!!value}
              onChange={(e) => onChange(e.target.checked)}
              className="peer sr-only"
            />
            <div className="w-10 h-6 bg-slate-200 rounded-full peer-checked:bg-indigo-600 transition-all"></div>
            <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-all peer-checked:left-5 shadow-sm"></div>
          </div>
          <span className="text-sm font-medium text-slate-600 group-hover:text-slate-900 transition-colors">
            {value ? 'Yes' : 'No'}
          </span>
        </label>
      );
    case 'date':
      return <input 
        type="date"
        value={value ? value.split('T')[0] : ''}
        onChange={(e) => onChange(e.target.value)}
        className={commonClass}
      />;
    case 'datetime':
      return <input 
        type="datetime-local"
        value={value ? value.split('.')[0] : ''}
        onChange={(e) => onChange(e.target.value)}
        className={commonClass}
      />;
    case 'currency':
    case 'number':
      return <input 
        type="number"
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className={commonClass}
        placeholder="0.00"
      />;
    default:
      return <input 
        type={field.type === 'email' ? 'email' : 'text'}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className={commonClass}
        placeholder={`Enter ${field.label.toLowerCase()}...`}
      />;
  }
};

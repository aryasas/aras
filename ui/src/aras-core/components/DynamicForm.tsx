import React, { useEffect, useState } from 'react';
import api from '../../lib/api';
import { Save, ArrowLeft, Plus } from 'lucide-react';
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

interface Metadata {
  resource: string;
  title: string;
  fields: Field[];
  children?: string[];
}

interface DynamicFormProps {
  resource: string;
  id?: number | string;
  onSave?: (data: any) => void;
  onCancel?: () => void;
}

export const DynamicForm: React.FC<DynamicFormProps> = ({ resource, id, onSave, onCancel }) => {
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [formData, setFormData] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const showError = useUIStore((state) => state.showError);

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        const metaRes = await api.get(`/${resource}/metadata`);
        setMetadata(metaRes.data);

        if (id && id !== 'new') {
          const dataRes = await api.get(`/${resource}/${id}`);
          setFormData(dataRes.data);
        } else {
          setFormData({});
        }
      } catch (err: any) {
        showError("Load Error", err.response?.data?.message || "Failed to load form");
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [resource, id, showError]);

  const handleChange = (name: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      let res;
      if (id && id !== 'new') {
        res = await api.put(`/${resource}/${id}`, formData);
      } else {
        res = await api.post(`/${resource}/`, formData);
      }
      if (onSave) onSave(res.data);
    } catch (err: any) {
      showError("Save Error", err.response?.data?.message || "Failed to save record");
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
            <h2 className="text-xl font-bold text-slate-900">
              {id && id !== 'new' ? `Edit ${metadata.title}` : `New ${metadata.title}`}
            </h2>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-widest">Resource: {resource}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button 
            type="button" 
            onClick={onCancel}
            className="px-4 py-2 text-sm font-bold text-slate-600 hover:bg-slate-50 rounded-xl transition-all"
          >
            Cancel
          </button>
          <button 
            onClick={handleSubmit}
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-xl text-sm font-bold hover:bg-indigo-700 transition-all shadow-md shadow-indigo-100 disabled:opacity-50"
          >
            <Save size={18} />
            <span>{saving ? 'Saving...' : 'Save Changes'}</span>
          </button>
        </div>
      </div>

      {/* ── Main Form Grid ────────────────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
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
                
                {field.read_only && <span className="text-[10px] text-slate-400 font-medium italic">Read-only system field</span>}
              </div>
            );
          })}
        </div>
      </form>

      {/* ── Child Tables Section ─────────────────────────────────────────── */}
      {id && id !== 'new' && metadata.children && metadata.children.length > 0 && (
        <div className="space-y-6">
          {metadata.children.map((childResource) => (
            <div key={childResource} className="space-y-3">
               <div className="flex items-center justify-between px-2">
                  <h3 className="text-lg font-bold text-slate-800 uppercase tracking-tight">{childResource.replace(/_/g, ' ')}</h3>
                  <button className="flex items-center gap-1 text-xs font-bold text-indigo-600 hover:bg-indigo-50 px-3 py-1.5 rounded-lg transition-all">
                    <Plus size={14} /> Add Line
                  </button>
               </div>
               <div className="h-[400px]">
                 <ListView 
                   resource={childResource} 
                   fixedFilters={{ [resource + "_id"]: id }}
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

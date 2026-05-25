import { useEffect, useState } from 'react';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import {
  Save, ArrowLeft, RefreshCw
} from 'lucide-react';
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

export const DynamicForm = ({ resource, id, initialData, onSave, onCancel }: any) => {
  const vocabulary = useVocabulary();
  const activeApps = useAuthStore((s) => s.activeApps);
  const optionalFeatures = useAuthStore((s) => s.optionalFeatures);
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [formData, setFormData] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [currentId, setCurrentId] = useState<any>(id !== 'new' ? id : undefined);
  
  const { notify } = useAras();

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const cleanResource = cleanResourcePath(resource);
        const metaRes = await api.get(`/metadata/${cleanResource}`);
        setMetadata(metaRes.data);
        setLoading(false);
      } catch (err) {
        notify("Failed to load metadata", "error");
      }
    };
    fetchMetadata();
  }, [resource, notify]);

  useEffect(() => {
    if (metadata && currentId) {
      api.get(`/${cleanResourcePath(metadata.api_path || resource)}/${currentId}`)
        .then(res => setFormData(res.data))
    } else if (metadata) {
      setFormData({ ...createDefaultRecord(metadata.fields), ...initialData })
    }
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
        <label className="text-xs font-bold text-[var(--aras-muted)] uppercase tracking-wide">{vocabulary.get(field.label)}</label>
        <Component 
           field={field} 
           value={formData[field.name]} 
           onChange={(val: any) => setFormData((prev: any) => ({...prev, [field.name]: val}))}
           formData={formData}
        />
      </DesignElement>
    );
  };

  if (loading || !metadata) return <div className="p-8 text-center text-[var(--aras-muted)]">Loading form...</div>

  return (
    <div className="aras-form-view mx-auto pb-20 space-y-6 max-w-5xl">
      <DesignContainer id="form-layout" className="flex flex-col gap-6">
        
        <DesignElement id="command-bar" className="flex items-center justify-between px-6 py-4 bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-[var(--shadow-premium)] sticky top-4 z-20">
          <DesignContainer id="command-bar-actions" className="flex items-center gap-4 w-full">
            <DesignElement id="btn-cancel" tagName="button" className="p-2 text-[var(--app-muted)] hover:text-[var(--app-text)] hover:bg-[var(--app-panel-soft)] rounded-[var(--app-radius)] transition-colors" style={{ border: 'none', background: 'transparent' }}>
              <span onClick={onCancel} className="cursor-pointer flex"><ArrowLeft size={20}/></span>
            </DesignElement>
            <DesignElement id="form-title" tagName="h2" className="flex-1 font-extrabold text-[calc(18px*var(--app-font-scale))] text-[var(--app-text)] truncate">
              {vocabulary.get(metadata.title)}
            </DesignElement>
            <DesignElement id="btn-save" tagName="button" className="bg-[var(--app-primary-action)] hover:bg-[var(--app-primary-action-strong)] text-white px-8 py-2.5 rounded-[var(--app-radius)] font-bold text-[calc(14px*var(--app-font-scale))] flex items-center gap-2 transition-transform hover:-translate-y-0.5 shadow-lg shadow-[var(--app-accent-glow)]">
              <span onClick={handleSubmit} className="flex items-center gap-2 cursor-pointer">
                 {saving ? <RefreshCw size={18} className="animate-spin" /> : <Save size={18}/>}
                 Save Changes
              </span>
            </DesignElement>
          </DesignContainer>
        </DesignElement>

        <DesignElement id="form-body" className="bg-[var(--app-panel)] p-8 md:p-12 rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-[var(--shadow-premium)]">
           <div className="mb-8 border-b border-[var(--app-border)] pb-4">
             <h3 className="text-[calc(16px*var(--app-font-scale))] font-extrabold text-[var(--app-text)]">General Information</h3>
             <p className="text-[calc(13px*var(--app-font-scale))] text-[var(--app-muted)] mt-1">Fill in the details for this record below.</p>
           </div>
           <DesignContainer id="fields-grid" className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-8">
              {metadata.fields.filter(isFieldVisible).map(renderField)}
           </DesignContainer>
        </DesignElement>

      </DesignContainer>
    </div>
  )
}

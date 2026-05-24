import { useEffect, useState } from 'react';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import {
  Save, ArrowLeft, RefreshCw, Zap
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
    <div className="aras-form-view mx-auto pb-20 space-y-6">
      <DesignContainer id="form-layout" className="flex flex-col gap-6">
        
        <DesignElement id="command-bar" className="flex items-center justify-between p-4 bg-[var(--aras-panel)] rounded-[var(--aras-radius)] border border-[var(--aras-border)] shadow-sm">
          <DesignContainer id="command-bar-actions" className="flex items-center gap-4">
            <DesignElement id="btn-cancel" tagName="button" className="p-2 hover:bg-[var(--aras-panel-soft)] rounded-[var(--aras-radius)]" style={{ border: 'none', background: 'transparent' }}>
              <span onClick={onCancel}><ArrowLeft size={18}/></span>
            </DesignElement>
            <DesignElement id="btn-save" tagName="button" className="bg-[var(--aras-accent)] text-white px-6 py-2 rounded-[var(--aras-radius)] font-bold flex items-center gap-2">
              <span onClick={handleSubmit} className="flex items-center gap-2">
                 {saving ? <RefreshCw size={16} className="animate-spin" /> : <Save size={16}/>}
                 Save
              </span>
            </DesignElement>
            <DesignElement id="form-title" tagName="h2" className="font-black text-[var(--aras-text)] ml-2">
              {vocabulary.get(metadata.title)}
            </DesignElement>
          </DesignContainer>
        </DesignElement>

        <DesignElement id="quick-actions" className="flex gap-2 p-4 bg-[var(--aras-panel-soft)] rounded-[var(--aras-radius)] border border-dashed border-[var(--aras-border)] items-center">
           <Zap size={14} className="text-amber-500" />
           <span className="text-xs font-bold text-[var(--aras-muted)] uppercase">Quick Actions</span>
        </DesignElement>

        <DesignElement id="form-body" className="bg-[var(--aras-panel)] p-8 rounded-[var(--aras-radius-lg)] border border-[var(--aras-border)] shadow-sm">
           <DesignContainer id="fields-grid" className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {metadata.fields.filter(isFieldVisible).slice(0, 10).map(renderField)}
           </DesignContainer>
        </DesignElement>

      </DesignContainer>
    </div>
  )
}

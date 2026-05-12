/**
 * Purpose: A "Universal Form" that generates inputs dynamically from model metadata.
 * Context: Frontend Core Component.
 * Impact: Eliminates the need to write custom forms for every new ERP model.
 */
import React, { useEffect, useState } from 'react';
import { MetadataService } from '../services/MetadataService';

interface DynamicFormProps {
  resource: string;
  initialData?: any;
  onSubmit: (data: any) => void;
}

export const DynamicForm: React.FC<DynamicFormProps> = ({ resource, initialData, onSubmit }) => {
  const [metadata, setMetadata] = useState<any>(null);
  const [formData, setFormData] = useState<any>(initialData || {});

  useEffect(() => {
    MetadataService.getResourceMetadata(resource).then(setMetadata);
  }, [resource]);

  if (!metadata) return <div>Loading metadata...</div>;

  const handleChange = (name: string, value: any) => {
    setFormData({ ...formData, [name]: value });
  };

  return (
    <form className="dynamic-form" onSubmit={(e) => { e.preventDefault(); onSubmit(formData); }}>
      <h3>{metadata.title}</h3>
      <div className="fields-grid">
        {metadata.fields.map((field: any) => {
          if (field.hidden) return null;

          return (
            <div key={field.name} className="field-group">
              <label>{field.label}</label>
              {field.type === 'textarea' ? (
                <textarea 
                  value={formData[field.name] || ''} 
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  readOnly={field.read_only}
                />
              ) : (
                <input 
                  type={field.type === 'email' ? 'email' : 'text'}
                  value={formData[field.name] || ''}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  readOnly={field.read_only}
                  required={field.required}
                />
              )}
            </div>
          );
        })}
      </div>
      <button type="submit">Save {metadata.title}</button>
    </form>
  );
};

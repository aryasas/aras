import React from 'react';
import Combobox from '../components/Combobox';
import MultiSelectCombobox from '../components/MultiSelectCombobox';
import { FileField } from '../components/FileField';

export interface FieldProps {
  value: any;
  onChange: (val: any) => void;
  field: any;
  formData: any;
  disabled?: boolean;
}

const DefaultInput: React.FC<FieldProps> = ({ value, onChange, field, disabled }) => {
  const commonClass = "w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all placeholder:text-slate-300";
  return (
    <input 
      type={field.type === 'email' ? 'email' : 'text'}
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      className={commonClass}
      disabled={disabled}
      placeholder={`Enter ${field.label.toLowerCase()}...`}
    />
  );
};

const NumberInput: React.FC<FieldProps> = ({ value, onChange, disabled }) => (
  <input 
    type="number"
    value={value || ''}
    onChange={(e) => onChange(e.target.value)}
    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
    disabled={disabled}
    placeholder="0.00"
  />
);

const BooleanInput: React.FC<FieldProps> = ({ value, onChange, disabled }) => (
  <label className={`flex items-center gap-3 py-2 cursor-pointer group ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
    <div className="relative">
      <input 
        type="checkbox"
        checked={!!value}
        onChange={(e) => !disabled && onChange(e.target.checked)}
        className="peer sr-only"
        disabled={disabled}
      />
      <div className="w-10 h-6 bg-slate-200 rounded-full peer-checked:bg-indigo-600 transition-all"></div>
      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-all peer-checked:left-5 shadow-sm"></div>
    </div>
    <span className="text-sm font-medium text-slate-600 group-hover:text-slate-900 transition-colors">
      {value ? 'Yes' : 'No'}
    </span>
  </label>
);

const DATE_CLASS = "w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed";

const DateInput: React.FC<FieldProps> = ({ value, onChange, disabled }) => (
  <input
    type="date"
    value={value ? value.split('T')[0] : ''}
    onChange={(e) => onChange(e.target.value)}
    className={DATE_CLASS}
    readOnly={disabled}
    tabIndex={disabled ? -1 : undefined}
  />
);

const DateTimeInput: React.FC<FieldProps> = ({ value, onChange, disabled }) => (
  <input
    type="datetime-local"
    value={value ? value.split('.')[0] : ''}
    onChange={(e) => onChange(e.target.value)}
    className={DATE_CLASS}
    readOnly={disabled}
    tabIndex={disabled ? -1 : undefined}
  />
);

const SelectInput: React.FC<FieldProps> = ({ value, onChange, field, disabled }) => (
  <select
    value={value || ''}
    onChange={(e) => onChange(e.target.value)}
    disabled={disabled}
    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
  >
    <option value="">Select {field.label}...</option>
    {field.options?.map((opt: any) => (
      <option key={opt.value} value={opt.value}>{opt.label}</option>
    ))}
  </select>
);

const TextAreaInput: React.FC<FieldProps> = ({ value, onChange, field, disabled }) => (
  <textarea 
    rows={4}
    value={value || ''} 
    onChange={(e) => onChange(e.target.value)}
    disabled={disabled}
    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
    placeholder={`Enter ${field.label.toLowerCase()}...`}
  />
);

class FieldRegistry {
  private components: Record<string, React.FC<FieldProps>> = {
    'string': DefaultInput,
    'email': DefaultInput,
    'number': NumberInput,
    'currency': NumberInput,
    'boolean': BooleanInput,
    'date': DateInput,
    'datetime': DateTimeInput,
    'select': SelectInput,
    'textarea': TextAreaInput,
    'file': (props) => <FileField {...props} label={props.field.label} />,
    'image': (props) => <FileField {...props} label={props.field.label} />,
    'lookup': (props) => (
      <Combobox 
        resource={props.field.target_resource || ''} 
        value={props.value} 
        onChange={props.onChange} 
        placeholder={`Select ${props.field.label}...`}
        disabled={props.disabled}
      />
    ),
    'bridge': (props) => (
      <MultiSelectCombobox 
        resource={props.field.target_resource || ''} 
        value={props.value || []} 
        onChange={props.onChange} 
        placeholder={`Select ${props.field.label}...`}
        disabled={props.disabled}
      />
    )
  };

  register(type: string, component: React.FC<FieldProps>) {
    this.components[type] = component;
  }

  get(type: string): React.FC<FieldProps> {
    return this.components[type] || DefaultInput;
  }
}

export const SchemaRegistry = new FieldRegistry();

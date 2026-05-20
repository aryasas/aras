import React from 'react';
import Combobox from './components/Combobox';
import MultiSelectCombobox from './components/MultiSelectCombobox';
import { FileField } from './components/FileField';

export interface FieldProps {
  value: any;
  onChange: (val: any) => void;
  field: any;
  formData: any;
  disabled?: boolean;
}

const DefaultInput: React.FC<FieldProps> = ({ value, onChange, field, disabled }) => {
  const commonClass = "w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:border-indigo-300 focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all placeholder:text-slate-300 shadow-sm";
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
    className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:border-indigo-300 focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all shadow-sm"
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
      <div className="w-10 h-6 bg-slate-200 rounded-full peer-checked:bg-indigo-600 transition-all peer-focus:ring-4 peer-focus:ring-indigo-500/20"></div>
      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-all peer-checked:left-5 shadow-sm"></div>
    </div>
    <span className="text-sm font-semibold text-slate-600 group-hover:text-indigo-600 transition-colors">
      {value ? 'Yes' : 'No'}
    </span>
  </label>
);

const DATE_CLASS = "w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:border-indigo-300 focus:ring-4 focus:ring-indigo-500/10 transition-all cursor-pointer shadow-sm disabled:opacity-50 disabled:cursor-not-allowed";

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
  <Combobox 
    options={field.options}
    value={value} 
    onChange={onChange} 
    placeholder={`Select ${field.label}...`}
    disabled={disabled}
  />
);


const TextAreaInput: React.FC<FieldProps> = ({ value, onChange, field, disabled }) => (
  <textarea 
    rows={4}
    value={value || ''} 
    onChange={(e) => onChange(e.target.value)}
    disabled={disabled}
    className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:border-indigo-300 focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all shadow-sm"
    placeholder={`Enter ${field.label.toLowerCase()}...`}
  />
);

const components: Record<string, React.FC<FieldProps>> = {
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
  'lookup': (props) => {
    const fkFilter = props.field.fk_filter as Record<string, string> | undefined;
    const fkFilterFallback = props.field.fk_filter_fallback as Record<string, string> | undefined;
    const resolvedFilter: Record<string, string> = fkFilter ? { ...fkFilter } : {};
    if (fkFilterFallback) {
      for (const [filterKey, srcKey] of Object.entries(fkFilterFallback)) {
        if (props.formData?.[srcKey] != null) resolvedFilter[filterKey] = srcKey;
      }
    }
    const extraFilters = Object.keys(resolvedFilter).length
      ? Object.fromEntries(
          Object.entries(resolvedFilter)
            .filter(([, srcKey]) => props.formData?.[srcKey] != null)
            .map(([filterKey, srcKey]) => [filterKey, props.formData[srcKey]])
        )
      : undefined;
    return (
      <Combobox
        resource={props.field.target_resource || ''}
        value={props.value}
        onChange={props.onChange}
        placeholder={`Select ${props.field.label}...`}
        disabled={props.disabled}
        extraFilters={Object.keys(extraFilters ?? {}).length ? extraFilters : undefined}
      />
    );
  },
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

export function resolveFieldComponent(field: any): React.ComponentType<FieldProps> {
  return components[field.type] || DefaultInput;
}

export function resolveFilterComponent(field: any): React.ComponentType<FieldProps> {
  // Filter components are usually simpler, often just an input or a combobox
  // based on field type. We'll add specific logic here if needed,
  // but for now, default to a basic input or a combobox for lookups/selects.
  if (field.type === 'lookup' && field.target_resource) {
    return (props) => (
      <Combobox 
        resource={props.field.target_resource || ''}
        value={props.value}
        onChange={props.onChange}
        placeholder={`Select ${props.field.label}...`}
      />
    );
  }
  if (field.type === 'select' && field.options) {
    return (props) => (
      <Combobox 
        options={props.field.options}
        value={props.value}
        onChange={props.onChange}
        placeholder={`Select ${props.field.label}...`}
      />
    );
  }
  // For boolean fields, a select with true/false could be better for filters
  if (field.type === 'boolean') {
    return (props) => (
      <select 
        value={props.value === true ? 'true' : props.value === false ? 'false' : ''}
        onChange={(e) => props.onChange(e.target.value === 'true' ? true : e.target.value === 'false' ? false : null)}
        className="text-xs bg-indigo-50 text-indigo-700 rounded-lg p-2 outline-none font-bold h-[42px]"
      >
        <option value="">Any</option>
        <option value="true">True</option>
        <option value="false">False</option>
      </select>
    );
  }
  // For date/datetime, a date picker
  if (field.type === 'date') {
    return (props) => (
      <input
        type="date"
        value={props.value ? props.value.split('T')[0] : ''}
        onChange={(e) => props.onChange(e.target.value)}
        className="w-full px-3 py-2.5 bg-white border border-slate-200 rounded-xl text-xs outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-500/10 transition-all shadow-sm"
      />
    );
  }
  if (field.type === 'datetime') {
    return (props) => (
      <input
        type="datetime-local"
        value={props.value ? props.value.split('.')[0] : ''}
        onChange={(e) => props.onChange(e.target.value)}
        className="w-full px-3 py-2.5 bg-white border border-slate-200 rounded-xl text-xs outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-500/10 transition-all shadow-sm"
      />
    );
  }
  return (props) => (
    <input 
      type="text" 
      value={props.value || ''}
      placeholder="Value..."
      onChange={(e) => props.onChange(e.target.value)}
      className="w-full px-3 py-2.5 bg-white border border-slate-200 rounded-xl text-xs outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-500/10 transition-all shadow-sm"
    />
  );
}

// Remove the old SchemaRegistry instance export
// export const SchemaRegistry = new FieldRegistry();

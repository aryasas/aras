import React from 'react';
import Combobox from './components/Combobox';
import MultiSelectCombobox from './components/MultiSelectCombobox';
import { FileField } from './components/FileField';

interface Option {
  label: string;
  value: string | number;
}

export interface Field {
  name?: string;
  type: string;
  label: string;
  options?: Option[];
  target_resource?: string;
  fk_filter?: Record<string, string>;
  fk_filter_fallback?: Record<string, string>;
}

export interface FieldProps {
  value: string | number | boolean | Array<string | number> | undefined | null;
  onChange: (val: string | number | boolean | Array<string | number> | null | undefined) => void;
  field: Field;
  formData: Record<string, unknown>;
  disabled?: boolean;
}

const inputValue = (value: FieldProps['value']): string | number | readonly string[] =>
  Array.isArray(value)
    ? value.map(String)
    : typeof value === 'string' || typeof value === 'number'
      ? value
      : '';

const scalarValue = (value: FieldProps['value']): string | number | null | undefined =>
  typeof value === 'string' || typeof value === 'number' || value == null ? value : undefined;

const stringValue = (value: FieldProps['value']): string =>
  typeof value === 'string' ? value : value == null ? '' : String(value);

const arrayValue = (value: FieldProps['value']): Array<string | number> =>
  Array.isArray(value) ? value : [];

const DefaultInput: React.FC<FieldProps> = ({ value, onChange, field, disabled }) => {
  const commonClass = "w-full h-9 px-3 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-[var(--aras-radius)] text-xs focus:border-[var(--aras-accent)] focus:ring-2 focus:ring-[var(--aras-accent)]/10 outline-none transition-all placeholder:text-[var(--aras-muted)] shadow-sm disabled:opacity-50 disabled:bg-[var(--aras-panel-soft)]";
  return (
    <input 
      type={field.type === 'email' ? 'email' : 'text'}
      value={inputValue(value)}
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
    value={inputValue(value)}
    onChange={(e) => onChange(e.target.value)}
    className="w-full h-9 px-3 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-[var(--aras-radius)] text-xs focus:border-[var(--aras-accent)] focus:ring-2 focus:ring-[var(--aras-accent)]/10 outline-none transition-all shadow-sm disabled:opacity-50 disabled:bg-[var(--aras-panel-soft)]"
    disabled={disabled}
    placeholder="0.00"
  />
);

const BooleanInput: React.FC<FieldProps> = ({ value, onChange, disabled }) => (
  <label className={`flex items-center gap-2 py-1 cursor-pointer group ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
    <div className="relative">
      <input 
        type="checkbox"
        checked={!!value}
        onChange={(e) => !disabled && onChange(e.target.checked)}
        className="peer sr-only"
        disabled={disabled}
      />
      <div className="w-8 h-4.5 bg-slate-200 rounded-full peer-checked:bg-[var(--aras-accent)] transition-all"></div>
      <div className="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full transition-all peer-checked:left-4 shadow-sm"></div>
    </div>
    <span className="text-xs font-semibold text-[var(--aras-muted)] group-hover:text-[var(--aras-accent)] transition-colors">
      {value ? 'Yes' : 'No'}
    </span>
  </label>
);

const DATE_CLASS = "w-full h-9 px-3 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-[var(--aras-radius)] text-xs focus:border-[var(--aras-accent)] focus:ring-2 focus:ring-[var(--aras-accent)]/10 transition-all cursor-pointer shadow-sm disabled:opacity-50 disabled:bg-[var(--aras-panel-soft)]";

const DateInput: React.FC<FieldProps> = ({ value, onChange, disabled }) => (
  <input
    type="date"
    value={stringValue(value).split('T')[0]}
    onChange={(e) => onChange(e.target.value)}
    className={DATE_CLASS}
    readOnly={disabled}
    tabIndex={disabled ? -1 : undefined}
  />
);

const DateTimeInput: React.FC<FieldProps> = ({ value, onChange, disabled }) => (
  <input
    type="datetime-local"
    value={stringValue(value).split('.')[0]}
    onChange={(e) => onChange(e.target.value)}
    className={DATE_CLASS}
    readOnly={disabled}
    tabIndex={disabled ? -1 : undefined}
  />
);

const SelectInput: React.FC<FieldProps> = ({ value, onChange, field, disabled }) => (
  <Combobox 
    options={field.options}
    value={scalarValue(value)} 
    onChange={onChange} 
    placeholder={`Select ${field.label}...`}
    disabled={disabled}
  />
);


const TextAreaInput: React.FC<FieldProps> = ({ value, onChange, field, disabled }) => (
  <textarea 
    rows={4}
    value={inputValue(value)} 
    onChange={(e) => onChange(e.target.value)}
    disabled={disabled}
    className="w-full px-3 py-2 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-[var(--aras-radius)] text-xs focus:border-[var(--aras-accent)] focus:ring-2 focus:ring-[var(--aras-accent)]/10 outline-none transition-all shadow-sm placeholder:text-[var(--aras-muted)] disabled:opacity-50 disabled:bg-[var(--aras-panel-soft)]"
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
  'file': (props) => <FileField value={stringValue(props.value)} onChange={props.onChange} label={props.field.label} />,
  'image': (props) => <FileField value={stringValue(props.value)} onChange={props.onChange} label={props.field.label} />,
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
        value={scalarValue(props.value)}
        onChange={props.onChange}
        placeholder={`Select ${props.field.label}...`}
        disabled={props.disabled}
        extraFilters={Object.keys(extraFilters ?? {}).length ? extraFilters as Record<string, string | number | boolean> : undefined}
      />
    );
  },
  'bridge': (props) => (
    <MultiSelectCombobox 
      resource={props.field.target_resource || ''} 
      value={arrayValue(props.value)} 
      onChange={props.onChange} 
      placeholder={`Select ${props.field.label}...`}
      disabled={props.disabled}
    />
  )
};

export function resolveFieldComponent(field: Field): React.ComponentType<FieldProps> {
  return components[field.type] || DefaultInput;
}

export function resolveFilterComponent(field: Field): React.ComponentType<FieldProps> {
  // Filter components are usually simpler, often just an input or a combobox
  // based on field type. We'll add specific logic here if needed,
  // but for now, default to a basic input or a combobox for lookups/selects.
  if (field.type === 'lookup' && field.target_resource) {
    return (props) => (
      <Combobox 
        resource={props.field.target_resource || ''}
        value={scalarValue(props.value)}
        onChange={props.onChange}
        placeholder={`Select ${props.field.label}...`}
      />
    );
  }
  if (field.type === 'select' && field.options) {
    return (props) => (
      <Combobox 
        options={props.field.options}
        value={scalarValue(props.value)}
        onChange={props.onChange}
        placeholder={`Select ${props.field.label}...`}
      />
    );
  }
  // For boolean fields, a custom combobox is better for filters
  if (field.type === 'boolean') {
    return (props) => (
      <Combobox 
        options={[
          { label: 'True', value: 'true' },
          { label: 'False', value: 'false' }
        ]}
        value={props.value === true ? 'true' : props.value === false ? 'false' : null}
        onChange={(val) => props.onChange(val === 'true' ? true : val === 'false' ? false : null)}
        placeholder="Any"
      />
    );
  }
  // For date/datetime, a date picker
  if (field.type === 'date') {
    return (props) => (
      <input
        type="date"
        value={stringValue(props.value).split('T')[0]}
        onChange={(e) => props.onChange(e.target.value)}
        className="w-full h-9 px-3 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-[var(--aras-radius)] text-xs outline-none focus:border-[var(--aras-accent)] transition-all shadow-sm"
      />
    );
  }
  if (field.type === 'datetime') {
    return (props) => (
      <input
        type="datetime-local"
        value={stringValue(props.value).split('.')[0]}
        onChange={(e) => props.onChange(e.target.value)}
        className="w-full h-9 px-3 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-[var(--aras-radius)] text-xs outline-none focus:border-[var(--aras-accent)] transition-all shadow-sm"
      />
    );
  }
  return (props) => (
    <input 
      type="text" 
      value={inputValue(props.value)}
      placeholder="Value..."
      onChange={(e) => props.onChange(e.target.value)}
      className="w-full h-9 px-3 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-[var(--aras-radius)] text-xs outline-none focus:border-[var(--aras-accent)] transition-all shadow-sm"
    />
  );
}

// Remove the old SchemaRegistry instance export
// export const SchemaRegistry = new FieldRegistry();

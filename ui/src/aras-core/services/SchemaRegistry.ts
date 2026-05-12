/**
 * Purpose: Registry that maps Aras metadata types to specialized React components.
 * Context: Frontend Core. Used by DynamicForm to pick the right input.
 * Impact: Enables 100% automated UI generation for any Resource.
 */
import React from 'react';

// Placeholder components for different types
const CurrencyInput = ({ value, onChange }: any) => (
  <div className="input-group">
    <span className="prefix">$</span>
    <input type="number" value={value} onChange={(e) => onChange(e.target.value)} />
  </div>
);

const DateInput = ({ value, onChange }: any) => (
  <input type="date" value={value} onChange={(e) => onChange(e.target.value)} />
);

const TextArea = ({ value, onChange }: any) => (
  <textarea value={value} onChange={(e) => onChange(e.target.value)} />
);

export const SchemaRegistry: Record<string, React.FC<any>> = {
  'currency': CurrencyInput,
  'date': DateInput,
  'textarea': TextArea,
  'string': (props) => <input type="text" {...props} />,
  'email': (props) => <input type="email" {...props} />,
  'number': (props) => <input type="number" {...props} />,
};

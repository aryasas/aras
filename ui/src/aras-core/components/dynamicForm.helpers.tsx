// claude-sonnet-4-6
// Pure/presentational helpers extracted from DynamicForm.tsx: the per-field renderer,
// the status badge, and the display-token finder. Keeping them here shrinks the form
// component and makes the field-render contract independently testable.
import { resolveFieldComponent, type FieldProps } from '../SchemaRegistry';
import { DesignElement } from './design/DesignElement';

export interface Field {
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
  options?: { label: string; value: string | number }[];
  allow_full_list?: boolean;
  min_length?: number;
  max_length?: number;
  pattern?: string;
  info?: { pattern_hint?: string; ui_type?: string };
  col_span?: number;
}

export interface RenderFieldOptions {
  field: Field;
  value: FieldProps['value'];
  onChange: (value: FieldProps['value']) => void;
  formData: Record<string, unknown>;
  error?: string;
  disabled?: boolean;
  vocabularyGet?: (value: string) => string;
  isVisible?: (field: Field) => boolean;
  builderEditMode?: boolean;
  onDragStart?: () => void;
  onDragOver?: (event: React.DragEvent) => void;
  onDrop?: () => void;
}

// claude-opus-4-8 (extracted by claude-sonnet-4-6)
export function renderField({
  field,
  value,
  onChange,
  formData,
  error,
  disabled,
  vocabularyGet = (label) => label,
  isVisible = () => true,
  builderEditMode = false,
  onDragStart,
  onDragOver,
  onDrop,
}: RenderFieldOptions) {
  if (!isVisible(field)) return null;
  const Component = resolveFieldComponent(field);
  const colSpan = Math.max(1, Math.min(Number(field.col_span || 1), 3));
  const errorId = `error-${field.name}`;
  const dndProps = builderEditMode ? {
    draggable: true,
    onDragStart,
    onDragOver,
    onDrop,
    style: { gridColumn: `span ${colSpan} / span ${colSpan}`, cursor: 'grab', outline: '1px dashed rgba(99,102,241,0.4)', outlineOffset: '4px' },
  } : { style: { gridColumn: `span ${colSpan} / span ${colSpan}` } }
  return (
    <DesignElement id={`field-${field.name}`} key={field.name} className="flex flex-col gap-1.5 w-full" {...dndProps} data-field-name={field.name}>
      <label className="text-[10px] font-bold text-[var(--text-3)] uppercase tracking-[0.14em]">{vocabularyGet(field.label)}</label>
      <Component
         field={field}
         value={value}
         onChange={onChange}
         formData={formData}
         disabled={disabled}
         aria-invalid={!!error}
         aria-describedby={error ? errorId : undefined}
      />
      {error && <div id={errorId} className="text-[11px] font-medium text-rose-600">{error}</div>}
    </DesignElement>
  );
}

// claude-opus-4-7
const STATUS_GLYPH: Record<string, { ch: string; color: string; label?: string }> = {
  draft:       { ch: '○', color: 'var(--text-3)' },
  in_progress: { ch: '◐', color: 'var(--accent)' },
  in_review:   { ch: '△', color: '#d97706', label: 'In review' },
  pending:     { ch: '△', color: '#d97706' },
  released:    { ch: '●', color: '#059669' },
  active:      { ch: '●', color: '#059669' },
  approved:    { ch: '●', color: '#059669' },
  blocked:     { ch: '✕', color: '#e11d48' },
  cancelled:   { ch: '✕', color: '#e11d48' },
  rejected:    { ch: '✕', color: '#e11d48' },
};

// claude-opus-4-7
export function StatusBadge({ value }: { value: any }) {
  if (value == null || value === '') return null;
  const raw = String(value).toLowerCase().trim().replace(/\s+/g, '_');
  const g = STATUS_GLYPH[raw] || { ch: '○', color: 'var(--text-3)' };
  const label = g.label || String(value).replace(/_/g, ' ');
  return (
    <span className="inline-flex items-center gap-1.5 text-[12px] capitalize text-[var(--text-2)]">
      <span style={{ color: g.color, fontFamily: 'Geist Mono, ui-monospace, monospace', fontSize: 13 }}>{g.ch}</span>
      {label}
    </span>
  );
}

// claude-opus-4-7
export function findDisplayToken(value: any): string | null {
  if (!value || typeof value !== 'object') return null;
  if (typeof value.display_token === 'string') return value.display_token;
  return findDisplayToken(value.data) || findDisplayToken(value.result);
}

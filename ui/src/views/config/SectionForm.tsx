import { useEffect, useMemo, useState } from 'react'
import { Eye, KeyRound, Save, Upload } from 'lucide-react'
import type { ConfigChoice, ConfigFieldSchema, ConfigSectionDetail } from '../../lib/config'
import { useRotateSecret, useSaveSection } from '../../lib/config'
import { useUIStore } from '../../store/uiStore'
import SimpleCombobox from '../../aras-core/components/SimpleCombobox'

interface SectionFormProps {
  section: ConfigSectionDetail
  onSaved?: () => void
}

type FormValues = Record<string, unknown>
type FormErrors = Record<string, string>
type ChoiceInput = ConfigChoice | [string | number | boolean, string] | string

function normalizeChoice(choice: ChoiceInput): ConfigChoice {
  if (Array.isArray(choice)) return { value: choice[0], label: String(choice[1] ?? choice[0]) }
  if (typeof choice === 'object' && choice !== null && 'value' in choice) return choice as ConfigChoice
  return { value: String(choice), label: String(choice) }
}

function valueFromField(field: ConfigFieldSchema) {
  if (field.value !== undefined) return field.value
  if (field.default !== undefined) return field.default
  if (field.type === 'bool') return false
  if (field.type === 'list') return []
  return ''
}

function validateField(field: ConfigFieldSchema, value: unknown) {
  if (field.required && (value === '' || value === null || value === undefined)) return `${field.label || field.key} is required.`
  if (field.type === 'number' && value !== '' && Number.isNaN(Number(value))) return `${field.label || field.key} must be a number.`
  if (field.type === 'color' && value && !/^#[0-9a-f]{6}$/i.test(String(value))) return 'Use a hex color like #E89B6C.'
  return ''
}

function inputClass(hasError?: boolean) {
  return [
    'w-full rounded-[var(--aras-radius)] border bg-[var(--aras-panel)] px-3 py-2 text-[13px] text-[var(--aras-text)] outline-none transition-colors',
    hasError ? 'border-[var(--danger)]' : 'border-[var(--aras-border)] focus:border-[var(--aras-accent)]',
  ].join(' ')
}

export default function SectionForm({ section, onSaved }: SectionFormProps) {
  const showAlert = useUIStore((state) => state.showAlert)
  const showPrompt = useUIStore((state) => state.showPrompt)
  const saveMutation = useSaveSection()
  const rotateMutation = useRotateSecret()
  const [values, setValues] = useState<FormValues>({})
  const [errors, setErrors] = useState<FormErrors>({})
  const [dirty, setDirty] = useState(false)

  useEffect(() => {
    const next = section.fields.reduce<FormValues>((acc, field) => {
      acc[field.key] = valueFromField(field)
      return acc
    }, {})
    setValues(next)
    setErrors({})
    setDirty(false)
  }, [section])

  const visibleFields = useMemo(() => section.fields.filter((field) => {
    if (!field.depends_on) return true
    return Boolean(values[field.depends_on])
  }), [section.fields, values])

  const updateValue = (field: ConfigFieldSchema, value: unknown) => {
    setValues((current) => ({ ...current, [field.key]: value }))
    setErrors((current) => ({ ...current, [field.key]: validateField(field, value) }))
    setDirty(true)
  }

  const validateAll = () => {
    const nextErrors = visibleFields.reduce<FormErrors>((acc, field) => {
      const message = validateField(field, values[field.key])
      if (message) acc[field.key] = message
      return acc
    }, {})
    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const handleSave = async () => {
    if (!validateAll()) return
    const payload = visibleFields.reduce<FormValues>((acc, field) => {
      if (field.secret && values[field.key] === '••••') return acc
      acc[field.key] = values[field.key]
      return acc
    }, {})
    await saveMutation.mutateAsync({ key: section.key, values: payload })
    setDirty(false)
    onSaved?.()
  }

  const handleReveal = () => {
    showAlert('Re-authentication required', 'Re-authentication is required before secrets can be revealed.')
  }

  const handleRotate = async (field: ConfigFieldSchema) => {
    showPrompt(
      `Rotate ${field.label || field.key}`,
      `Enter a new value for ${field.label || field.key}.`,
      async (nextValue) => {
        if (!nextValue) return
        await rotateMutation.mutateAsync({ sectionKey: section.key, fieldKey: field.key, value: nextValue })
      },
      { confirmLabel: 'Rotate' },
    )
  }

  const renderField = (field: ConfigFieldSchema) => {
    const value = values[field.key]
    const error = errors[field.key]
    const type = field.secret ? 'secret' : field.type

    if (type === 'bool') {
      return (
        <button
          type="button"
          role="switch"
          aria-checked={Boolean(value)}
          onClick={() => updateValue(field, !value)}
          className={`relative h-7 w-12 rounded-full border transition-colors ${value ? 'border-[var(--aras-accent)] bg-[var(--aras-accent)]' : 'border-[var(--aras-border)] bg-[var(--aras-panel-soft)]'}`}
        >
          <span className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow-sm transition-transform ${value ? 'translate-x-5' : 'translate-x-1'}`} />
        </button>
      )
    }

    if (type === 'choice') {
      const choiceOptions = (field.choices || []).map((choice) => {
        const normalized = normalizeChoice(choice)
        return { value: String(normalized.value), label: String(normalized.label) }
      })
      return (
        <SimpleCombobox
          options={choiceOptions}
          value={String(value ?? '')}
          onChange={(v) => updateValue(field, v)}
          placeholder="Select..."
        />
      )
    }

    if (type === 'text' || type === 'list') {
      return (
        <textarea
          className={`${inputClass(Boolean(error))} min-h-28 resize-y`}
          value={Array.isArray(value) ? value.join('\n') : String(value ?? '')}
          onChange={(event) => updateValue(field, type === 'list' ? event.target.value.split('\n').filter(Boolean) : event.target.value)}
        />
      )
    }

    if (type === 'color') {
      return (
        <div className="flex items-center gap-2">
          <input className="h-9 w-11 rounded-[var(--aras-radius)] border border-[var(--aras-border)] bg-transparent p-1" type="color" value={String(value || '#E89B6C')} onChange={(event) => updateValue(field, event.target.value)} />
          <input className={inputClass(Boolean(error))} value={String(value ?? '')} onChange={(event) => updateValue(field, event.target.value)} />
        </div>
      )
    }

    if (type === 'image') {
      return (
        <div className="flex items-center gap-3">
          {value ? <img src={String(value)} alt="" className="h-12 w-12 rounded-[var(--aras-radius)] border border-[var(--aras-border)] object-contain" /> : null}
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-[var(--aras-radius)] border border-[var(--aras-border)] px-3 py-2 text-[12px] font-semibold text-[var(--aras-text)]">
            <Upload size={14} />
            <span>Upload</span>
            <input className="hidden" type="file" accept="image/*" onChange={(event) => updateValue(field, event.target.files?.[0]?.name || '')} />
          </label>
        </div>
      )
    }

    if (type === 'secret') {
      return (
        <div className="flex flex-wrap items-center gap-2">
          <input className={`${inputClass(Boolean(error))} max-w-sm`} type="password" value={String(value || '••••')} onChange={(event) => updateValue(field, event.target.value)} />
          <button type="button" onClick={handleReveal} className="inline-flex items-center gap-2 rounded-[var(--aras-radius)] border border-[var(--aras-border)] px-3 py-2 text-[12px] font-semibold text-[var(--aras-text)]">
            <Eye size={14} />
            Reveal
          </button>
          <button type="button" onClick={() => handleRotate(field)} className="inline-flex items-center gap-2 rounded-[var(--aras-radius)] border border-[var(--aras-border)] px-3 py-2 text-[12px] font-semibold text-[var(--aras-text)]">
            <KeyRound size={14} />
            Rotate
          </button>
        </div>
      )
    }

    return (
      <input
        className={inputClass(Boolean(error))}
        type={type === 'number' ? 'number' : 'text'}
        value={String(value ?? '')}
        onChange={(event) => updateValue(field, type === 'number' ? Number(event.target.value) : event.target.value)}
      />
    )
  }

  return (
    <div className="mx-auto flex w-full max-w-[880px] flex-col gap-6 pb-24">
      <div>
        <h1 className="text-[22px] font-semibold text-[var(--aras-text)]">{section.label}</h1>
        <p className="mt-1 text-[13px] text-[var(--aras-muted)]">{section.key}</p>
      </div>

      <div className="flex flex-col gap-5">
        {visibleFields.map((field) => (
          <label key={field.key} className="grid gap-2 border-b border-[var(--aras-border)] pb-5 md:grid-cols-[220px_1fr] md:gap-6">
            <span>
              <span className="block text-[13px] font-semibold text-[var(--aras-text)]">{field.label || field.key}</span>
              {field.help ? <span className="mt-1 block text-[12px] leading-5 text-[var(--aras-muted)]">{field.help}</span> : null}
            </span>
            <span>
              {renderField(field)}
              {errors[field.key] ? <span className="mt-1 block text-[12px] text-[var(--danger)]">{errors[field.key]}</span> : null}
            </span>
          </label>
        ))}
      </div>

      <div className="sticky bottom-0 z-20 -mx-4 border-t border-[var(--aras-border)] bg-[color-mix(in_oklch,var(--aras-bg-main)_92%,transparent)] px-4 py-3 backdrop-blur md:mx-0">
        <div className="mx-auto flex max-w-[880px] items-center justify-between gap-3">
          <span className="text-[12px] text-[var(--aras-muted)]">{dirty ? 'Unsaved changes' : 'Saved values are current'}</span>
          <button
            type="button"
            onClick={handleSave}
            disabled={!dirty || saveMutation.isPending}
            className="inline-flex items-center gap-2 rounded-[var(--aras-radius)] bg-[var(--aras-accent)] px-4 py-2 text-[12px] font-semibold text-[var(--aras-button-text)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Save size={14} />
            {saveMutation.isPending ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

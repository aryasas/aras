import { useEffect, useMemo, useState } from 'react'
import { Save, Settings } from 'lucide-react'
import { renderField, type Field } from '../../aras-core/components/DynamicForm'
import { useAras } from '../../aras-core/hooks/useAras'
import { settingsApi, type SettingsFieldSchema, type SettingsSchema, type SettingsSectionSchema, type SettingsValues } from '../../lib/api'
import { useUIStore } from '../../store/uiStore'

interface SettingsFormProps {
  namespace: string
  onDirtyChange?: (dirty: boolean) => void
}

type FormErrors = Record<string, Record<string, string>>

function normalizeType(type: string) {
  if (type === 'bool') return 'boolean'
  if (type === 'choice') return 'select'
  if (type === 'secret') return 'string'
  if (type === 'text' || type === 'list') return 'textarea'
  return type
}

function normalizeChoice(choice: NonNullable<SettingsFieldSchema['choices']>[number]) {
  if (Array.isArray(choice)) return { value: typeof choice[0] === 'boolean' ? String(choice[0]) : choice[0], label: String(choice[1] ?? choice[0]) }
  if (typeof choice === 'object' && choice !== null && 'value' in choice) {
    return { ...choice, value: typeof choice.value === 'boolean' ? String(choice.value) : choice.value }
  }
  return { value: String(choice), label: String(choice) }
}

function toDynamicField(field: SettingsFieldSchema): Field {
  return {
    name: field.key,
    label: field.label || field.key,
    type: normalizeType(field.type),
    required: Boolean(field.required),
    read_only: false,
    hidden: false,
    options: field.choices?.map(normalizeChoice),
    info: field.secret ? { ui_type: 'string' } : undefined,
  }
}

function normalizeSchema(schema: SettingsSchema | SettingsSectionSchema[]): SettingsSectionSchema[] {
  return Array.isArray(schema) ? schema : schema.sections || []
}

function readApiErrors(err: any): FormErrors {
  const payload = err?.response?.data
  const detail = payload?.detail || payload?.error?.detail || payload?.error
  if (!detail || typeof detail !== 'object') return {}
  return detail as FormErrors
}

function hasSectionChanges(section: SettingsSectionSchema, values: SettingsValues, initialValues: SettingsValues) {
  return section.fields.some((field) => values[section.key]?.[field.key] !== initialValues[section.key]?.[field.key])
}

export default function SettingsForm({ namespace, onDirtyChange }: SettingsFormProps) {
  const { notify } = useAras()
  const setDirty = useUIStore((state) => state.setDirty)
  const [sections, setSections] = useState<SettingsSectionSchema[]>([])
  const [values, setValues] = useState<SettingsValues>({})
  const [initialValues, setInitialValues] = useState<SettingsValues>({})
  const [errors, setErrors] = useState<FormErrors>({})
  const [loading, setLoading] = useState(true)
  const [savingSection, setSavingSection] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setErrors({})
    Promise.all([
      settingsApi.getSchema(namespace),
      settingsApi.getValues(namespace),
    ])
      .then(([schema, nextValues]) => {
        if (cancelled) return
        const nextSections = normalizeSchema(schema).sort((a, b) => (a.order || 100) - (b.order || 100))
        setSections(nextSections)
        setValues(nextValues || {})
        setInitialValues(nextValues || {})
      })
      .catch((err) => {
        if (!cancelled) notify(err.message || 'Failed to load settings', 'error')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [namespace, notify])

  const dirty = useMemo(() => JSON.stringify(values) !== JSON.stringify(initialValues), [values, initialValues])
  const dirtyKey = `settings:${namespace}`

  useEffect(() => {
    setDirty(dirtyKey, dirty)
    onDirtyChange?.(dirty)
    return () => setDirty(dirtyKey, false)
  }, [dirty, dirtyKey, onDirtyChange, setDirty])

  const updateValue = (sectionKey: string, fieldKey: string, value: unknown) => {
    setValues((current) => ({
      ...current,
      [sectionKey]: {
        ...(current[sectionKey] || {}),
        [fieldKey]: value,
      },
    }))
    setErrors((current) => {
      if (!current[sectionKey]?.[fieldKey]) return current
      const nextSection = { ...current[sectionKey] }
      delete nextSection[fieldKey]
      return { ...current, [sectionKey]: nextSection }
    })
  }

  const saveSection = async (section: SettingsSectionSchema) => {
    const changedValues = section.fields.reduce<Record<string, unknown>>((acc, field) => {
      const nextValue = values[section.key]?.[field.key]
      if (nextValue !== initialValues[section.key]?.[field.key]) acc[field.key] = nextValue
      return acc
    }, {})
    if (Object.keys(changedValues).length === 0) return

    setSavingSection(section.key)
    try {
      await settingsApi.saveValues(namespace, { [section.key]: changedValues })
      setInitialValues((current) => ({
        ...current,
        [section.key]: {
          ...(current[section.key] || {}),
          ...changedValues,
        },
      }))
      setErrors((current) => ({ ...current, [section.key]: {} }))
      notify('Settings saved', 'success')
    } catch (err: any) {
      const apiErrors = readApiErrors(err)
      if (Object.keys(apiErrors).length > 0) setErrors(apiErrors)
      notify(err.message || 'Failed to save settings', 'error')
    } finally {
      setSavingSection(null)
    }
  }

  if (loading) {
    return (
      <div className="flex max-w-[920px] flex-col gap-4">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-5">
            <div className="h-4 w-48 animate-pulse rounded bg-[var(--surface-2)]" />
            <div className="mt-5 grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((__, fieldIndex) => (
                <div key={fieldIndex} className="h-14 animate-pulse rounded bg-[var(--surface-2)]" />
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (sections.length === 0) {
    return (
      <div className="max-w-[920px] rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-8 text-center text-[13px] text-[var(--text-3)]">
        No settings sections are registered for this namespace.
      </div>
    )
  }

  return (
    <div className="flex max-w-[920px] flex-col gap-5 pb-20">
      {sections.map((section) => {
        const sectionDirty = hasSectionChanges(section, values, initialValues)
        return (
          <section key={section.key} className="rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)] shadow-sm">
            <div className="flex items-center justify-between gap-3 border-b border-[var(--line)] px-5 py-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <Settings size={15} className="text-[var(--accent)]" />
                  <h2 className="truncate text-[15px] font-semibold text-[var(--text)]">{section.label}</h2>
                </div>
                <div className="arc-mono mt-1 text-[10px] uppercase tracking-[0.14em] text-[var(--text-3)]">{section.key}</div>
              </div>
              <button
                type="button"
                onClick={() => saveSection(section)}
                disabled={!sectionDirty || savingSection !== null}
                className="inline-flex h-8 items-center gap-2 rounded-[var(--aras-radius)] bg-[var(--accent)] px-3 text-[12px] font-semibold text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Save size={13} />
                {savingSection === section.key ? 'Saving...' : 'Save'}
              </button>
            </div>
            {section.fields.length === 0 ? (
              <div className="px-5 py-6 text-[12px] text-[var(--text-3)]">No fields are registered for this section.</div>
            ) : (
              <div className="grid grid-cols-1 gap-x-6 gap-y-5 p-5 md:grid-cols-2 lg:grid-cols-3">
                {section.fields.map((field) => {
                  const dynamicField = toDynamicField(field)
                  return renderField({
                    field: dynamicField,
                    value: field.type === 'list' && Array.isArray(values[section.key]?.[field.key])
                      ? (values[section.key]?.[field.key] as unknown[]).join('\n')
                      : values[section.key]?.[field.key],
                    onChange: (value) => updateValue(section.key, field.key, field.type === 'list' ? String(value || '').split('\n').filter(Boolean) : value),
                    formData: values[section.key] || {},
                    error: errors[section.key]?.[field.key],
                    disabled: savingSection !== null,
                  })
                })}
              </div>
            )}
          </section>
        )
      })}
    </div>
  )
}

export interface ValidatableField {
  name: string
  label?: string
  required?: boolean
  min_length?: number
  max_length?: number
  pattern?: string
  info?: { pattern_hint?: string }
}

export function validateField(field: ValidatableField, value: unknown): string | null {
  const label = field.label || field.name
  const textValue = value == null ? '' : String(value)

  if (field.required && (value == null || textValue.trim() === '' || (Array.isArray(value) && value.length === 0))) {
    return `${label} is required`
  }
  if (field.min_length && textValue && textValue.length < field.min_length) {
    return `${label} must be at least ${field.min_length} characters`
  }
  if (field.max_length && textValue && textValue.length > field.max_length) {
    return `${label} must be ${field.max_length} characters or fewer`
  }
  if (field.pattern && textValue) {
    try {
      if (!new RegExp(field.pattern).test(textValue)) return field.info?.pattern_hint || 'Format is invalid'
    } catch {
      return `${label} validation pattern is invalid`
    }
  }

  return null
}

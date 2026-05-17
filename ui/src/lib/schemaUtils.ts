export interface FieldMeta {
  name: string
  type?: string
  default_value?: unknown
  series?: string
}

export function createDefaultRecord(metadata: FieldMeta[]): Record<string, unknown> {
  const today = new Date().toISOString().split('T')[0]
  const now = new Date().toISOString().split('.')[0]
  const record: Record<string, unknown> = {}

  metadata.forEach((field) => {
    if (field.default_value !== undefined && field.default_value !== null && field.default_value !== '') {
      if (field.type === 'boolean') record[field.name] = field.default_value === true || field.default_value === 'true'
      else if (field.type === 'number' || field.type === 'currency') record[field.name] = Number(field.default_value)
      else record[field.name] = field.default_value
      return
    }

    if (field.series) {
      record[field.name] = field.series
      return
    }

    if (field.type === 'boolean') record[field.name] = false
    else if (field.type === 'number' || field.type === 'currency') record[field.name] = 0
    else if (field.type === 'date') record[field.name] = today
    else if (field.type === 'datetime') record[field.name] = now
    else if (field.type === 'lookup' || field.type === 'm2m') record[field.name] = field.type === 'm2m' ? [] : null
    else record[field.name] = ''
  })

  return record
}

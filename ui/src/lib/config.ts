import { QueryClient, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from './api'

export type ConfigScope = 'core' | 'module' | 'shared' | 'feature'
export type ConfigFieldType = 'string' | 'text' | 'number' | 'bool' | 'choice' | 'color' | 'image' | 'secret' | 'list'

export interface ConfigSectionSummary {
  key: string
  label: string
  icon?: string
  scope: ConfigScope
  app?: string
}

export interface ConfigChoice {
  label: string
  value: string | number | boolean
}

export interface ConfigFieldSchema {
  key: string
  label?: string
  type: ConfigFieldType | string
  value?: unknown
  default?: unknown
  help?: string
  required?: boolean
  secret?: boolean
  choices?: Array<ConfigChoice | [string | number | boolean, string] | string>
  validator?: string
  depends_on?: string | null
}

export interface ConfigSectionDetail extends ConfigSectionSummary {
  fields: ConfigFieldSchema[]
}

export const configQueryClient = new QueryClient()

export const configKeys = {
  sections: ['config', 'sections'] as const,
  section: (key: string) => ['config', 'section', key] as const,
  value: (key: string) => ['config', 'value', key] as const,
}

export function splitConfigKey(key: string) {
  const parts = key.split('.')
  if (parts.length < 3) throw new Error(`Invalid config key: ${key}`)
  return {
    sectionKey: parts.slice(0, -1).join('.'),
    fieldKey: parts[parts.length - 1],
  }
}

export async function getSections(params?: { scope?: ConfigScope }) {
  const res = await api.get<ConfigSectionSummary[]>('/settings/sections', { params })
  return res.data
}

export async function getSection(key: string): Promise<ConfigSectionDetail> {
  const res = await api.get<ConfigSectionDetail>(`/settings/sections/${encodeURIComponent(key)}`)
  return res.data
}

export async function saveSection(key: string, values: Record<string, any>): Promise<void> {
  const res = await api.put(`/settings/sections/${encodeURIComponent(key)}`, values)
  return res.data
}

export async function rotateSecret(sectionKey: string, fieldKey: string): Promise<any> {
  const res = await api.post(
    `/settings/sections/${encodeURIComponent(sectionKey)}/rotate-secret/${encodeURIComponent(fieldKey)}`,
    {}
  )
  return res.data
}


export async function setConfig(key: string, value: unknown) {
  const { sectionKey, fieldKey } = splitConfigKey(key)
  const result = await saveSection(sectionKey, { [fieldKey]: value })
  await configQueryClient.invalidateQueries({ queryKey: ['config'] })
  return result
}

export function useSections(params?: { scope?: ConfigScope }) {
  return useQuery({
    queryKey: params?.scope ? [...configKeys.sections, params.scope] : configKeys.sections,
    queryFn: () => getSections(params),
  })
}

export function useSection(key: string | null | undefined) {
  return useQuery({
    queryKey: configKeys.section(key || ''),
    queryFn: () => getSection(key || ''),
    enabled: Boolean(key),
  })
}

export function useConfig(key: string) {
  const { sectionKey, fieldKey } = splitConfigKey(key)
  return useQuery({
    queryKey: configKeys.value(key),
    queryFn: async () => {
      const section = await getSection(sectionKey)
      return section.fields.find((field) => field.key === fieldKey)?.value
    },
  })
}

export function useSaveSection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ key, values }: { key: string; values: Record<string, unknown> }) => saveSection(key, values),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: configKeys.sections })
      queryClient.invalidateQueries({ queryKey: configKeys.section(variables.key) })
      queryClient.invalidateQueries({ queryKey: ['config'] })
      configQueryClient.invalidateQueries({ queryKey: ['config'] })
    },
  })
}

export function useRotateSecret() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ sectionKey, fieldKey }: { sectionKey: string; fieldKey: string; value: string }) =>
      rotateSecret(sectionKey, fieldKey),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: configKeys.section(variables.sectionKey) })
      configQueryClient.invalidateQueries({ queryKey: ['config'] })
    },
  })
}

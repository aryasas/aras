import axios from 'axios'
import { cleanResourcePath } from './resourceUtils'
import en from '../locales/en.json'
import id from '../locales/id.json'

const DEV_MULTI_TENANT = import.meta.env.VITE_DEV_MULTI_TENANT === 'true'
const TENANT_STORAGE_KEY = 'tenant_id'
const TOKEN_STORAGE_KEY = 'aras_token'

function getAuthToken() {
  const sessionToken = sessionStorage.getItem(TOKEN_STORAGE_KEY)
  if (sessionToken) return sessionToken

  const legacyToken = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (legacyToken) {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, legacyToken)
    localStorage.removeItem(TOKEN_STORAGE_KEY)
  }
  return legacyToken
}

function clearAuthToken() {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

interface ApiEnvelope<T = unknown> {
  success: boolean
  data: T
  message?: string | null
  error?: string | { message?: string; detail?: unknown } | null
  detail?: string | null
  error_key?: string | null
}

type Lang = 'en' | 'id'
const LOCALES: Record<Lang, Record<string, unknown>> = { en, id }

function getEnvelopeErrorMessage(value: ApiEnvelope | Record<string, any>): string {
  const translated = getEnvelopeErrorTranslation(value)
  if (translated) return translated
  const error = value.error
  if (typeof error === 'string') return error
  if (error && typeof error === 'object' && typeof error.message === 'string') return error.message
  if (typeof value.detail === 'string') return value.detail
  if (typeof value.message === 'string') return value.message
  return 'Request failed'
}

function getEnvelopeErrorKey(value: ApiEnvelope | Record<string, any>): string | undefined {
  const error = value.error
  if (typeof value.error_key === 'string' && value.error_key) return value.error_key
  if (typeof (value as any).error_key === 'string' && (value as any).error_key) return (value as any).error_key
  if (error && typeof error === 'object') {
    if (typeof (error as any).error_key === 'string' && (error as any).error_key) return (error as any).error_key
    if (typeof (error as any).key === 'string' && (error as any).key) return (error as any).key
  }
  return undefined
}

function lookupLocaleString(locale: Record<string, unknown>, key: string): string | undefined {
  if (!key) return undefined
  const direct = locale[key]
  if (typeof direct === 'string') return direct

  const parts = key.split('.')
  let current: unknown = locale
  for (const part of parts) {
    if (current && typeof current === 'object' && part in current) {
      current = (current as Record<string, unknown>)[part]
    } else {
      return undefined
    }
  }
  return typeof current === 'string' ? current : undefined
}

function getEnvelopeErrorTranslation(value: ApiEnvelope | Record<string, any>): string | undefined {
  const key = getEnvelopeErrorKey(value)
  if (!key) return undefined
  const lang = (localStorage.getItem('aras_lang') === 'id' ? 'id' : 'en') as Lang
  return lookupLocaleString(LOCALES[lang], key)
}

function getEnvelopeErrorCode(value: ApiEnvelope | Record<string, any>): string | undefined {
  const error = value.error
  if (error && typeof error === 'object' && typeof (error as any).code === 'string') return (error as any).code
  if (typeof (value as any).code === 'string') return (value as any).code
  return undefined
}

function isApiEnvelope(value: unknown): value is ApiEnvelope {
  return (
    typeof value === 'object' &&
    value !== null &&
    'success' in value &&
    typeof (value as { success?: unknown }).success === 'boolean'
  )
}



const api = axios.create({
  baseURL: '/api/v1',
})

// Attach JWT to every request
api.interceptors.request.use((config) => {
  if (config.url && !/^https?:\/\//i.test(config.url)) {
    const [path, query] = config.url.split('?')
    const leadingSlash = path.startsWith('/') ? '/' : ''
    config.url = `${leadingSlash}${cleanResourcePath(path)}${query ? `?${query}` : ''}`
  }

  const token = getAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  const orgId = localStorage.getItem('org_id')
  if (orgId && orgId !== '-1') {
    config.headers['X-Org-ID'] = orgId
  }

  if (DEV_MULTI_TENANT) {
    const tenantId = localStorage.getItem(TENANT_STORAGE_KEY)
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId
    }
  }

  return config
})

      // Normalize error responses and handle 401
api.interceptors.response.use(
  (response) => {
    if (isApiEnvelope(response.data)) {
      if (!response.data.success) {
        // Prefer `error` from envelope, then `message`, then fallback
        const errorMessage = getEnvelopeErrorMessage(response.data);

        // Ensure the error object passed to consumers has the right structure
        const errorData = {
          ...response.data, // Preserve original data
          message: errorMessage,
          detail: errorMessage,
          error: errorMessage,
          error_key: response.data.error_key || getEnvelopeErrorKey(response.data),
        };

        const error = new Error(errorMessage) as Error & { response?: typeof response; code?: string };
        error.code = getEnvelopeErrorCode(response.data);
        error.response = { ...response, data: errorData }; // Attach enriched error data to response
        return Promise.reject(error);
      }
      response.data = response.data.data; // Extract actual data for successful responses
    }
    return response;
  },
  (error) => {
    if (error.response?.data) {
      const d = error.response.data;
      let errorMessage = 'Request failed';

      if (isApiEnvelope(d)) {
        errorMessage = getEnvelopeErrorMessage(d);
      } else if (typeof d === 'object') {
        // For non-envelope responses (e.g., FastAPI validation errors)
        errorMessage = getEnvelopeErrorMessage(d);
      } else if (typeof d === 'string') {
        errorMessage = d;
      }

      // Ensure error.message reflects the primary error message
      error.message = errorMessage;
      error.code = getEnvelopeErrorCode(d);

      // Normalize error.response.data to contain 'error', 'detail', and 'message'
      // This makes it consistent for consumers
      error.response.data = {
        ...d, // Preserve original data
        error: errorMessage,
        detail: errorMessage,
        message: errorMessage,
        code: d.code || error.code,
        error_key: d.error_key || getEnvelopeErrorKey(d),
      };
    }
    if (error.response?.status === 401) {
      clearAuthToken();
      const path = window.location.pathname;
      const publicPaths = ['/login', '/welcome', '/signup', '/portal', '/portal/setup', '/forgot-password', '/reset-password', '/contact'];
      const isPublic = publicPaths.some((p) => path === p || path.startsWith(p + '/')) || path.startsWith('/p/');
      if (!isPublic) {
        window.location.href = '/login';
      }
    } else if (error.response?.status === 402) {
      const path = window.location.pathname;
      if (!path.startsWith('/portal')) {
        window.location.href = '/portal?tab=billing';
      }
    }
    return Promise.reject(error);
  }
);

export interface SettingsNamespace {
  name: string
  label: string
  icon?: string
}

export interface SettingsSetupStep {
  key: string
  label: string
  icon?: string
  setup_step: number
  complete: boolean
}

export interface VocabularyLabels {
  trx_in: string
  trx_out: string
  party: string
  pot: string
}

export interface VocabularyProfile {
  key: string
  display_name: string
  description: string
  labels: VocabularyLabels
}

export interface MasterDataEntity {
  key: string
  label: string
  icon?: string
  scope: string
  app: string
  model_table: string
  resource_url: string
  can_write?: boolean
  can_admin?: boolean
  help?: string
  order?: number
}

export interface MasterDataGroup {
  key: string
  label: string
  entities: MasterDataEntity[]
}

export interface MasterDataSchema {
  groups: MasterDataGroup[]
}

export interface SettingsFieldSchema {
  key: string
  label?: string
  type: string
  default?: unknown
  help?: string
  required?: boolean
  secret?: boolean
  choices?: Array<{ label: string; value: string | number | boolean } | [string | number | boolean, string] | string>
  depends_on?: string | null
  resource?: string | null
}

export interface SettingsSectionSchema {
  key: string
  label: string
  icon?: string
  order?: number
  scope?: string
  fields: SettingsFieldSchema[]
}

export interface SettingsSchema {
  namespace?: string
  sections: SettingsSectionSchema[]
}

export type SettingsValues = Record<string, Record<string, unknown>>

export interface SeedCatalogSeed {
  key: string
  label: string
  optional: boolean
  app_name: string
}

export interface SeedCatalogEntry {
  app_name: string
  app_label: string
  seeds: SeedCatalogSeed[]
}

export interface SeedRunResult {
  key: string
  status: 'ran' | 'skipped' | 'error'
  message: string
}

export interface TradeDashboardRecentDocument {
  type: string
  number: string
  status?: string | null
  doc_date?: string | null
  party_name?: string | null
  amount?: number | null
}

export interface TradeDashboardLowStockItem {
  code?: string | null
  name?: string | null
  uom?: string | null
  balance?: number | null
}

export interface TradeDashboardData {
  today_sales: number
  month_profit: number
  month_profit_change_pct: number
  receivables_total: number
  overdue_count: number
  labels?: VocabularyLabels | null
  low_stock_count: number
  low_stock_items: TradeDashboardLowStockItem[]
  recent_documents: TradeDashboardRecentDocument[]
}

const tradeDashboardCache = new Map<number | 'default', TradeDashboardData>()
const tradeDashboardPromiseCache = new Map<number | 'default', Promise<TradeDashboardData>>()

// claude-opus-4-8
function getTradeDashboardCacheKey(orgId?: number) {
  return typeof orgId === 'number' ? orgId : 'default'
}

// claude-opus-4-8
async function fetchTradeDashboard(orgId?: number) {
  const query = typeof orgId === 'number' ? `?org_id=${orgId}` : ''
  const res = await api.get<TradeDashboardData>(`/report/dashboard${query}`)
  return res.data
}

// claude-opus-4-8
export function invalidateTradeDashboard(orgId?: number) {
  if (typeof orgId === 'number') {
    tradeDashboardCache.delete(orgId)
    tradeDashboardPromiseCache.delete(orgId)
    return
  }
  tradeDashboardCache.clear()
  tradeDashboardPromiseCache.clear()
}

// claude-opus-4-8
export function getTradeDashboard(orgId?: number) {
  const key = getTradeDashboardCacheKey(orgId)
  const cached = tradeDashboardCache.get(key)
  if (cached) return Promise.resolve(cached)

  const inFlight = tradeDashboardPromiseCache.get(key)
  if (inFlight) return inFlight

  const request = fetchTradeDashboard(orgId)
    .then((payload) => {
      tradeDashboardCache.set(key, payload)
      return payload
    })
    .finally(() => {
      tradeDashboardPromiseCache.delete(key)
    })

  tradeDashboardPromiseCache.set(key, request)
  return request
}

export const settingsApi = {
  async listNamespaces() {
    const res = await api.get<SettingsNamespace[]>('/settings')
    return res.data
  },
  async getSetup() {
    const res = await api.get<SettingsSetupStep[]>('/settings/setup')
    return res.data
  },
  async getSchema(namespace: string) {
    const res = await api.get<SettingsSchema | SettingsSectionSchema[]>(`/settings/${encodeURIComponent(namespace)}/schema`)
    return res.data
  },
  async getValues(namespace: string) {
    const res = await api.get<SettingsValues>(`/settings/${encodeURIComponent(namespace)}`)
    return res.data
  },
  async saveValues(namespace: string, payload: SettingsValues) {
    const res = await api.put(`/settings/${encodeURIComponent(namespace)}`, payload)
    return res.data
  },
}

export const masterDataApi = {
  async listEntities() {
    const res = await api.get<MasterDataEntity[]>('/master-data')
    return res.data
  },
  async getSchema() {
    const res = await api.get<MasterDataSchema>('/master-data/schema')
    return res.data
  },
}

export const seedApi = {
  async list() {
    const res = await api.get<SeedCatalogEntry[]>('/dev/seeds')
    return res.data
  },
  async run(keys: string[], orgId: number) {
    const res = await api.post<SeedRunResult[]>('/dev/seeds/run', {
      keys,
      org_id: orgId,
    })
    return res.data
  },
}

export const reportApi = {
  async dashboard(orgId?: number) {
    return fetchTradeDashboard(orgId)
  },
}

export const vocabularyApi = {
  async listProfiles() {
    const res = await api.get<VocabularyProfile[]>('/accounting/vocabulary/profiles')
    return res.data
  },
  async updateOrganizationProfile(orgId: number, profile: string) {
    const res = await api.put<{ profile: string; labels: VocabularyLabels }>(`/accounting/organizations/${orgId}/profile`, { profile })
    return res.data
  },
}

export default api

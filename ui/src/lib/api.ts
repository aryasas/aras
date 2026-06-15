import axios, { type InternalAxiosRequestConfig } from 'axios'
import { cleanResourcePath } from './resourceUtils'
import en from '../locales/en.json'
import id from '../locales/id.json'
import { useAuthStore } from '../store/authStore'

const DEV_MULTI_TENANT = import.meta.env.VITE_DEV_MULTI_TENANT === 'true'
const TENANT_STORAGE_KEY = 'tenant_id'
const TOKEN_STORAGE_KEY = 'aras_token'
const REFRESH_TOKEN_STORAGE_KEY = 'aras_refresh_token'
const PORTAL_TOKEN_STORAGE_KEY = 'portal_token'
export const PUBLIC_PATHS = ['/login', '/welcome', '/signup', '/portal', '/portal/setup', '/forgot-password', '/reset-password', '/contact']
const AUTH_REFRESH_SKIP_PATHS = new Set(['/auth/token', '/auth/refresh'])

type RetryableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean
  skipAuthRefresh?: boolean
  portalAuth?: boolean
}

export type ApiRequestConfig = RetryableRequestConfig

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

export interface AuthSessionPayload {
  access_token: string
  refresh_token?: string
  token_type?: string
}

export interface ConsentPolicy {
  version: string
  text: Record<Lang, string>
}

let refreshTokenMemory: string | null = null
let refreshRequest: Promise<AuthSessionPayload> | null = null

// gpt-5.4
function getAuthToken() {
  return sessionStorage.getItem(TOKEN_STORAGE_KEY)
}

// gpt-5.4
function clearAuthToken() {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

function getRefreshToken() {
  return sessionStorage.getItem(REFRESH_TOKEN_STORAGE_KEY)
}

function clearRefreshToken() {
  sessionStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY)
}

function getPortalToken() {
  return sessionStorage.getItem(PORTAL_TOKEN_STORAGE_KEY)
}

// gpt-5.4
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

// gpt-5.4
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

// gpt-5.4
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

// gpt-5.4
function getEnvelopeErrorTranslation(value: ApiEnvelope | Record<string, any>): string | undefined {
  const key = getEnvelopeErrorKey(value)
  if (!key) return undefined
  const lang = (localStorage.getItem('aras_lang') === 'id' ? 'id' : 'en') as Lang
  return lookupLocaleString(LOCALES[lang], key)
}

// gpt-5.4
function getEnvelopeErrorCode(value: ApiEnvelope | Record<string, any>): string | undefined {
  const error = value.error
  if (error && typeof error === 'object' && typeof (error as any).code === 'string') return (error as any).code
  if (typeof (value as any).code === 'string') return (value as any).code
  return undefined
}

// gpt-5.4
function isApiEnvelope(value: unknown): value is ApiEnvelope {
  return (
    typeof value === 'object' &&
    value !== null &&
    'success' in value &&
    typeof (value as { success?: unknown }).success === 'boolean'
  )
}

// gpt-5.4
function setRefreshToken(token: string | null) {
  refreshTokenMemory = token
  if (token) {
    sessionStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, token)
  } else {
    clearRefreshToken()
  }
}

// gpt-5.4
function syncAccessToken(token: string | null) {
  const store = useAuthStore.getState()
  if (store.token !== token) {
    store.setToken(token)
  }
  if (!token) {
    clearAuthToken()
  }
}

// gpt-5.4
function setRequestHeader(config: RetryableRequestConfig, key: string, value: string) {
  const headers = config.headers ?? {}
  if (typeof (headers as { set?: (name: string, val: string) => void }).set === 'function') {
    ;(headers as { set: (name: string, val: string) => void }).set(key, value)
  } else {
    ;(headers as Record<string, string>)[key] = value
  }
  config.headers = headers
}

// gpt-5.4
function getApiPath(url?: string) {
  if (!url) return ''
  const withoutOrigin = url.replace(/^https?:\/\/[^/]+/i, '')
  const [path] = withoutOrigin.split('?')
  const normalized = path.startsWith('/api/v1') ? path.slice('/api/v1'.length) || '/' : path
  return normalized.startsWith('/') ? normalized : `/${normalized}`
}

// gpt-5.4
export function isPublicPath(pathname: string) {
  return PUBLIC_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`)) || pathname.startsWith('/p/')
}

// gpt-5.4
function hardLogout(redirectToLogin = true) {
  setRefreshToken(null)
  useAuthStore.getState().logout()
  clearAuthToken()
  clearRefreshToken()

  if (!redirectToLogin) return

  if (!isPublicPath(window.location.pathname)) {
    window.location.href = '/login'
  }
}

// gpt-5.4
function storeAuthPayload(path: string, payload: unknown) {
  if (!AUTH_REFRESH_SKIP_PATHS.has(path)) return
  if (!payload || typeof payload !== 'object') return

  const tokenPayload = payload as Partial<AuthSessionPayload>
  if (typeof tokenPayload.access_token === 'string' && tokenPayload.access_token) {
    syncAccessToken(tokenPayload.access_token)
  }
  if (typeof tokenPayload.refresh_token === 'string' && tokenPayload.refresh_token) {
    setRefreshToken(tokenPayload.refresh_token)
  }
}

// gpt-5.4
function normalizeConsentPolicy(payload: unknown): ConsentPolicy {
  const source = (payload && typeof payload === 'object' ? payload : {}) as Record<string, any>
  const version = typeof source.version === 'string' && source.version ? source.version : 'unknown'
  const textSource =
    (source.text && typeof source.text === 'object' ? source.text : null) ||
    (source.canonical_text && typeof source.canonical_text === 'object' ? source.canonical_text : null)

  return {
    version,
    text: {
      en:
        (typeof textSource?.en === 'string' && textSource.en) ||
        (typeof source.text_en === 'string' && source.text_en) ||
        '',
      id:
        (typeof textSource?.id === 'string' && textSource.id) ||
        (typeof source.text_id === 'string' && source.text_id) ||
        '',
    },
  }
}

// gpt-5.4
async function refreshSession(): Promise<AuthSessionPayload> {
  if (refreshRequest) return refreshRequest

  const refreshToken = getRefreshToken() || refreshTokenMemory
  const payload = refreshToken ? { refresh_token: refreshToken } : undefined

  refreshRequest = api
    .post<AuthSessionPayload>('/auth/refresh', payload, { skipAuthRefresh: true } as RetryableRequestConfig)
    .then((response) => {
      const session = response.data
      if (!session?.access_token) {
        throw new Error('Refresh response missing access token')
      }
      storeAuthPayload('/auth/refresh', session)
      return session
    })
    .catch((error) => {
      hardLogout()
      throw error
    })
    .finally(() => {
      refreshRequest = null
    })

  return refreshRequest
}

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const requestConfig = config as RetryableRequestConfig

  if (requestConfig.url && !/^https?:\/\//i.test(requestConfig.url)) {
    const [path, query] = requestConfig.url.split('?')
    const leadingSlash = path.startsWith('/') ? '/' : ''
    requestConfig.url = `${leadingSlash}${cleanResourcePath(path)}${query ? `?${query}` : ''}`
  }

  const token = requestConfig.portalAuth ? getPortalToken() : (useAuthStore.getState().token ?? getAuthToken())
  if (token) {
    setRequestHeader(requestConfig, 'Authorization', `Bearer ${token}`)
  }

  const orgId = localStorage.getItem('org_id')
  if (orgId && orgId !== '-1') {
    setRequestHeader(requestConfig, 'X-Org-ID', orgId)
  }

  if (DEV_MULTI_TENANT) {
    const tenantId = localStorage.getItem(TENANT_STORAGE_KEY)
    if (tenantId) {
      setRequestHeader(requestConfig, 'X-Tenant-ID', tenantId)
    }
  }

  return requestConfig
})

api.interceptors.response.use(
  (response) => {
    const path = getApiPath(response.config.url)

    if (isApiEnvelope(response.data)) {
      if (!response.data.success) {
        const errorMessage = getEnvelopeErrorMessage(response.data)
        const errorData = {
          ...response.data,
          message: errorMessage,
          detail: errorMessage,
          error: errorMessage,
          error_key: response.data.error_key || getEnvelopeErrorKey(response.data),
        }

        const envelopeError = new Error(errorMessage) as Error & { response?: typeof response; code?: string }
        envelopeError.code = getEnvelopeErrorCode(response.data)
        envelopeError.response = { ...response, data: errorData }
        return Promise.reject(envelopeError)
      }
      response.data = response.data.data
    }

    storeAuthPayload(path, response.data)
    return response
  },
  async (error) => {
    if (error.response?.data) {
      const d = error.response.data
      let errorMessage = 'Request failed'

      if (isApiEnvelope(d)) {
        errorMessage = getEnvelopeErrorMessage(d)
      } else if (typeof d === 'object') {
        errorMessage = getEnvelopeErrorMessage(d)
      } else if (typeof d === 'string') {
        errorMessage = d
      }

      error.message = errorMessage
      error.code = getEnvelopeErrorCode(d)
      error.response.data = {
        ...d,
        error: errorMessage,
        detail: errorMessage,
        message: errorMessage,
        code: d.code || error.code,
        error_key: d.error_key || getEnvelopeErrorKey(d),
      }
    }

    const requestConfig = (error.config || {}) as RetryableRequestConfig
    const path = getApiPath(requestConfig.url)

    if (error.response?.status === 401) {
      if (requestConfig.portalAuth) {
        return Promise.reject(error)
      }
      if (!requestConfig._retry && !requestConfig.skipAuthRefresh && !AUTH_REFRESH_SKIP_PATHS.has(path)) {
        requestConfig._retry = true
        try {
          const session = await refreshSession()
          setRequestHeader(requestConfig, 'Authorization', `Bearer ${session.access_token}`)
          return api(requestConfig)
        } catch (refreshError) {
          return Promise.reject(refreshError)
        }
      }

      hardLogout()
    } else if (error.response?.status === 402) {
      const currentPath = window.location.pathname
      if (!currentPath.startsWith('/portal')) {
        window.location.href = '/portal?tab=billing'
      }
    }

    return Promise.reject(error)
  },
)
export interface SettingsNamespace {
  name: string
  label: string
  icon?: string
  level?: 'organization' | 'app' | 'security' | 'system'
  section_count?: number
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
  resource?: string
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
  const res = await api.get<TradeDashboardData>(`/accounting/dashboard${query}`)
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

export const authApi = {
  async refresh() {
    return refreshSession()
  },
  async logout() {
    const refreshToken = refreshTokenMemory
    try {
      const res = await api.post(
        '/auth/logout',
        refreshToken ? { refresh_token: refreshToken } : undefined,
        { skipAuthRefresh: true } as RetryableRequestConfig,
      )
      return res.data
    } finally {
      hardLogout(false)
    }
  },
}

export const consentApi = {
  async getPolicy() {
    const res = await api.get<ConsentPolicy>('/consent/policy')
    return normalizeConsentPolicy(res.data)
  },
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

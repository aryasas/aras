import axios from 'axios'
import React, { useEffect, useMemo, useState } from 'react'
import { Check, ChevronRight, Clock3, Copy, Download, History, Loader2, Pin, Play, RefreshCw, Save, Search, Shield, Trash2, Upload, Wand2 } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import DataGrid from '../../aras-core/components/DataGrid'
import { getBackendOrigin, getOpenApiJsonUrl } from '../../lib/apiDocs'

type JsonSchema = {
  type?: string
  format?: string
  enum?: unknown[]
  items?: JsonSchema
  properties?: Record<string, JsonSchema>
  required?: string[]
  $ref?: string
  default?: unknown
  description?: string
  anyOf?: JsonSchema[]
  allOf?: JsonSchema[]
}

type Param = { name: string; in: 'query' | 'path' | 'header'; required?: boolean; schema?: JsonSchema; description?: string }

type Operation = {
  method: string
  path: string
  summary?: string
  tags: string[]
  parameters: Param[]
  bodySchema?: JsonSchema
}

type OpenAPI = {
  paths: Record<string, Record<string, {
    summary?: string
    tags?: string[]
    parameters?: Param[]
    requestBody?: { content?: Record<string, { schema?: JsonSchema }> }
  }>>
  components?: { schemas?: Record<string, JsonSchema> }
}

type AuthMode = 'session' | 'anonymous' | 'bearer'
type WorkspaceMode = 'run' | 'explore' | 'debug'

type TestDraft = {
  operationKey: string
  pathVals: Record<string, string>
  queryVals: Record<string, string>
  headerVals: Record<string, string>
  body: Record<string, unknown>
  headersText: string
  authMode: AuthMode
  bearerToken: string
  baseUrl: string
  expectedStatus: string
  mustInclude: string
  maxMs: string
  captureText: string
}

type SavedTest = {
  id: string
  name: string
  note: string
  tags: string[]
  pinned: boolean
  captureText: string
  draft: TestDraft
}

type SavedProfile = {
  id: string
  name: string
  note: string
  baseUrl: string
  authMode: AuthMode
  bearerToken: string
  headersText: string
}

type SnapshotRecord = {
  id: string
  name: string
  operationKey: string
  response: ResponseState
  responseText: string
  diffBaseId?: string
}

type ScenarioStep = {
  id: string
  name: string
  captureText: string
  draft: TestDraft
}

type ScenarioStepResult = {
  stepId: string
  name: string
  operationKey: string
  status: number
  ms: number
  ok: boolean
}

type ScenarioReport = {
  id: string
  at: number
  name: string
  ok: boolean
  finalStatus: number | null
  finalMs: number | null
  steps: ScenarioStepResult[]
}

type ScenarioTemplateStep = {
  method: string
  path: string
  name?: string
  captureText?: string
  expectedStatus?: string
}

type ScenarioTemplate = {
  id: string
  name: string
  description: string
  steps: ScenarioTemplateStep[]
}

type RunCheck = {
  label: string
  ok: boolean
  detail: string
}

type RunRecord = {
  id: string
  at: number
  operation: string
  method: string
  path: string
  status: number
  ms: number
  ok: boolean
  summary: string
  pinned?: boolean
  draft: TestDraft
}

type ResponseState = {
  status: number
  data: unknown
  headers: Record<string, unknown>
  ms: number
  url: string
}

const METHODS = ['get', 'post', 'put', 'patch', 'delete']
const methodColor: Record<string, string> = {
  get: 'bg-emerald-100 text-emerald-700',
  post: 'bg-blue-100 text-blue-700',
  put: 'bg-amber-100 text-amber-700',
  patch: 'bg-amber-100 text-amber-700',
  delete: 'bg-red-100 text-red-700',
}

const SCENARIO_TEMPLATES: ScenarioTemplate[] = [
  {
    id: 'dev-snapshot',
    name: 'Dev Snapshot',
    description: 'Collect the core runtime and app diagnostics endpoints in one pass.',
    steps: [
      { method: 'get', path: '/dev/info', name: 'Runtime info', captureText: 'python = python_version' },
      { method: 'get', path: '/dev/stats', name: 'Request stats' },
      { method: 'get', path: '/dev/dev/system-info', name: 'App system info' },
      { method: 'get', path: '/dev/dev/metrics', name: 'App metrics', captureText: 'requests = total_requests' },
    ],
  },
  {
    id: 'route-audit',
    name: 'Route Audit',
    description: 'Verify the route inventory and model registry together.',
    steps: [
      { method: 'get', path: '/dev/inspect/routes', name: 'Inspect routes' },
      { method: 'get', path: '/dev/inspect/models', name: 'Inspect models' },
    ],
  },
  {
    id: 'system-watch',
    name: 'System Watch',
    description: 'Read the live system status and error surface back to back.',
    steps: [
      { method: 'get', path: '/dev/dev/system-info', name: 'System info' },
      { method: 'get', path: '/dev/dev/metrics', name: 'Live metrics' },
      { method: 'get', path: '/dev/dev/errors', name: 'Recent errors' },
    ],
  },
]

const STORAGE_KEYS = {
  mode: 'devtools:test-lab:mode',
  baseUrl: 'devtools:test-lab:base-url',
  authMode: 'devtools:test-lab:auth-mode',
  bearerToken: 'devtools:test-lab:bearer-token',
  headersText: 'devtools:test-lab:headers',
  profiles: 'devtools:test-lab:profiles',
  savedTests: 'devtools:test-lab:saved-tests',
  snapshots: 'devtools:test-lab:snapshots',
  scenario: 'devtools:test-lab:scenario',
  history: 'devtools:test-lab:history',
  historySearch: 'devtools:test-lab:history-search',
  selectedCase: 'devtools:test-lab:selected-case',
  selectedProfile: 'devtools:test-lab:selected-profile',
}

function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function writeJson(key: string, value: unknown) {
  localStorage.setItem(key, JSON.stringify(value))
}

function normalizeSavedTests(value: SavedTest[]) {
  return value.map(test => ({
    ...test,
    tags: Array.isArray(test.tags) ? test.tags : [],
    pinned: Boolean(test.pinned),
    captureText: test.captureText || '',
    draft: {
      ...test.draft,
      captureText: test.draft?.captureText || test.captureText || '',
      headerVals: test.draft?.headerVals || {},
    },
  }))
}

function uid() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function normalizeBaseUrl(value: string) {
  const trimmed = value.trim()
  const fallback = `${getBackendOrigin().replace(/\/+$/, '')}/api/v1`
  if (!trimmed) return fallback

  const candidate = /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`
  try {
    const parsed = new URL(candidate)
    const pathname = parsed.pathname.replace(/\/+$/, '') || '/api/v1'
    return `${parsed.origin}${pathname}${parsed.search}`
  } catch {
    return fallback
  }
}

function cleanApiPath(path: string) {
  return path.replace(/^\/api\/v1/, '').replace(/\/+$/, '') || '/'
}

function sameOperation(a: Operation, b: Operation) {
  return a.method === b.method && cleanApiPath(a.path).toLowerCase() === cleanApiPath(b.path).toLowerCase()
}

function operationKey(operation: Operation) {
  return `${operation.method}:${operation.path}`
}

function resolveSchema(schema: JsonSchema | undefined, schemas: Record<string, JsonSchema>, depth = 0): JsonSchema {
  if (!schema || depth > 6) return {}
  if (schema.$ref) {
    const name = schema.$ref.split('/').pop() || ''
    return resolveSchema(schemas[name], schemas, depth + 1)
  }
  if (schema.allOf?.length) {
    const merged: JsonSchema = { type: 'object', properties: {}, required: [] }
    for (const part of schema.allOf) {
      const resolved = resolveSchema(part, schemas, depth + 1)
      Object.assign(merged.properties!, resolved.properties)
      if (resolved.required) merged.required!.push(...resolved.required)
    }
    return merged
  }
  if (schema.anyOf?.length) {
    const branch = schema.anyOf.find(item => item.type !== 'null') || schema.anyOf[0]
    return resolveSchema(branch, schemas, depth + 1)
  }
  return schema
}

function defaultFor(schema: JsonSchema): unknown {
  if (schema.default !== undefined) return schema.default
  switch (schema.type) {
    case 'integer':
    case 'number':
      return ''
    case 'boolean':
      return false
    case 'array':
      return ''
    case 'object':
      return {}
    default:
      return ''
  }
}

function parseSpec(spec: OpenAPI): Operation[] {
  const schemas = spec.components?.schemas || {}
  const ops: Operation[] = []
  for (const [path, methods] of Object.entries(spec.paths || {})) {
    for (const method of METHODS) {
      const op = methods[method]
      if (!op) continue
      const json = op.requestBody?.content?.['application/json']?.schema
      ops.push({
        method,
        path,
        summary: op.summary,
        tags: op.tags?.length ? op.tags : ['untagged'],
        parameters: (op.parameters || []).map(param => ({ ...param, schema: resolveSchema(param.schema, schemas) })),
        bodySchema: json ? resolveSchema(json, schemas) : undefined,
      })
    }
  }
  return ops
}

function buildInitialBody(schema?: JsonSchema) {
  const initial: Record<string, unknown> = {}
  if (!schema?.properties) return initial
  for (const [key, property] of Object.entries(schema.properties)) {
    initial[key] = defaultFor(property)
  }
  return initial
}

function buildDraft(operation: Operation, state: {
  pathVals: Record<string, string>
  queryVals: Record<string, string>
  headerVals: Record<string, string>
  body: Record<string, unknown>
  headersText: string
  authMode: AuthMode
  bearerToken: string
  baseUrl: string
  expectedStatus: string
  mustInclude: string
  maxMs: string
  captureText: string
}): TestDraft {
  return {
    operationKey: operationKey(operation),
    pathVals: state.pathVals,
    queryVals: state.queryVals,
    headerVals: state.headerVals,
    body: state.body,
    headersText: state.headersText,
    authMode: state.authMode,
    bearerToken: state.bearerToken,
    baseUrl: state.baseUrl,
    expectedStatus: state.expectedStatus,
    mustInclude: state.mustInclude,
    maxMs: state.maxMs,
    captureText: state.captureText,
  }
}

function parseHeadersText(text: string) {
  return parseHeadersJson(text)
}

function buildUrl(baseUrl: string, path: string) {
  return `${normalizeBaseUrl(baseUrl)}${cleanApiPath(path)}`
}

function buildCurl(request: {
  method: string
  url: string
  headers: Record<string, string>
  body?: unknown
}) {
  const parts = ['curl', '-X', request.method.toUpperCase(), `'${request.url.replace(/'/g, `'\"'\"'`)}'`]
  for (const [key, value] of Object.entries(request.headers)) {
    parts.push('-H', `'${`${key}: ${value}`.replace(/'/g, `'\"'\"'`)}'`)
  }
  if (request.body !== undefined) {
    const payload = typeof request.body === 'string' ? request.body : JSON.stringify(request.body, null, 2)
    parts.push('--data-raw', `'${payload.replace(/'/g, `'\"'\"'`)}'`)
  }
  return parts.join(' ')
}

function asRows(data: unknown): Record<string, unknown>[] | null {
  if (Array.isArray(data) && data.length && typeof data[0] === 'object' && data[0] !== null && !Array.isArray(data[0])) {
    return data as Record<string, unknown>[]
  }
  const items = (data as { items?: unknown })?.items
  if (Array.isArray(items) && items.length && typeof items[0] === 'object' && items[0] !== null && !Array.isArray(items[0])) {
    return items as Record<string, unknown>[]
  }
  return null
}

function getStoredToken() {
  return sessionStorage.getItem('aras_token') || localStorage.getItem('aras_token') || ''
}

function splitHeaders(headers: Record<string, unknown>) {
  return Object.entries(headers).map(([key, value]) => ({
    key,
    value: Array.isArray(value) ? value.join(', ') : String(value ?? ''),
  }))
}

function interpolateString(value: string, vars: Record<string, unknown>) {
  return value.replace(/\{\{([^}]+)\}\}/g, (_, rawKey) => {
    const key = rawKey.trim()
    const replacement = vars[key]
    return replacement === undefined || replacement === null ? '' : String(replacement)
  })
}

function interpolateValue(value: unknown, vars: Record<string, unknown>): unknown {
  if (typeof value === 'string') return interpolateString(value, vars)
  if (Array.isArray(value)) return value.map(item => interpolateValue(item, vars))
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {}
    for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
      out[key] = interpolateValue(item, vars)
    }
    return out
  }
  return value
}

function getValueByPath(value: unknown, path: string) {
  const tokens = path
    .replace(/\[(\d+)\]/g, '.$1')
    .split('.')
    .map(part => part.trim())
    .filter(Boolean)
  let current: unknown = value
  for (const token of tokens) {
    if (current === null || current === undefined) return undefined
    if (Array.isArray(current)) {
      const index = Number(token)
      current = Number.isInteger(index) ? current[index] : undefined
      continue
    }
    if (typeof current === 'object') {
      current = (current as Record<string, unknown>)[token]
      continue
    }
    return undefined
  }
  return current
}

function parseCaptureText(text: string) {
  return text
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)
    .map(line => {
      const separatorIndex = line.indexOf('=') >= 0 ? line.indexOf('=') : line.indexOf(':')
      if (separatorIndex < 0) return null
      const key = line.slice(0, separatorIndex).trim()
      const value = line.slice(separatorIndex + 1).trim()
      if (!key || !value) return null
      return { key, path: value }
    })
    .filter(Boolean) as Array<{ key: string; path: string }>
}

function extractVariables(response: ResponseState | null, captureText: string) {
  const vars: Record<string, unknown> = {}
  if (!response) return vars
  vars.status = response.status
  vars.ms = response.ms
  vars.url = response.url
  const captures = parseCaptureText(captureText)
  for (const capture of captures) {
    const extracted = getValueByPath(response.data, capture.path)
    if (extracted !== undefined) vars[capture.key] = extracted
  }
  return vars
}

function safeJson(value: unknown) {
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

function diffLines(left: string, right: string) {
  const leftLines = left.split('\n')
  const rightLines = right.split('\n')
  const max = Math.max(leftLines.length, rightLines.length)
  const output: Array<{ left?: string; right?: string; same: boolean }> = []
  for (let index = 0; index < max; index += 1) {
    const leftLine = leftLines[index]
    const rightLine = rightLines[index]
    output.push({ left: leftLine, right: rightLine, same: leftLine === rightLine })
  }
  return output
}

function parseHeadersJson(text: string) {
  if (!text.trim()) return {}
  const parsed = JSON.parse(text)
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('Headers must be a JSON object.')
  }
  const headers: Record<string, string> = {}
  for (const [key, value] of Object.entries(parsed as Record<string, unknown>)) {
    if (value === null || value === undefined) continue
    headers[key] = String(value)
  }
  return headers
}

function matchOperation(ops: Operation[], input: string) {
  const query = input.trim().toLowerCase()
  if (!query) return null
  const normalizedQuery = cleanApiPath(query)
  return (
    ops.find(operation => `${operation.method} ${cleanApiPath(operation.path).toLowerCase()}` === query) ||
    ops.find(operation => cleanApiPath(operation.path).toLowerCase() === normalizedQuery) ||
    ops.find(operation => operation.path.toLowerCase() === query) ||
    ops.find(operation =>
      cleanApiPath(operation.path).toLowerCase().includes(normalizedQuery) ||
      (operation.summary || '').toLowerCase().includes(query) ||
      operation.tags.some(tag => tag.toLowerCase().includes(query))
    ) ||
    null
  )
}

function formatMs(ms: number) {
  return `${ms} ms`
}

function findOperationByPath(ops: Operation[], method: string, path: string) {
  const normalizedPath = cleanApiPath(path).toLowerCase()
  return ops.find(operation =>
    operation.method === method &&
    cleanApiPath(operation.path).toLowerCase() === normalizedPath
  ) || null
}

export default function ApiConsole() {
  const location = useLocation()
  const [ops, setOps] = useState<Operation[]>([])
  const [loadingSpec, setLoadingSpec] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [mode, setMode] = useState<WorkspaceMode>(() => (localStorage.getItem(STORAGE_KEYS.mode) as WorkspaceMode) || 'run')
  const [filter, setFilter] = useState('')
  const [pathLookup, setPathLookup] = useState('')
  const [selected, setSelected] = useState<Operation | null>(null)
  const [pathVals, setPathVals] = useState<Record<string, string>>({})
  const [queryVals, setQueryVals] = useState<Record<string, string>>({})
  const [headerVals, setHeaderVals] = useState<Record<string, string>>({})
  const [body, setBody] = useState<Record<string, unknown>>({})
  const [headersText, setHeadersText] = useState(() => localStorage.getItem(STORAGE_KEYS.headersText) || '{}')
  const [baseUrl, setBaseUrl] = useState(() => localStorage.getItem(STORAGE_KEYS.baseUrl) || `${getBackendOrigin().replace(/\/+$/, '')}/api/v1`)
  const [authMode, setAuthMode] = useState<AuthMode>(() => (localStorage.getItem(STORAGE_KEYS.authMode) as AuthMode) || 'session')
  const [bearerToken, setBearerToken] = useState(() => localStorage.getItem(STORAGE_KEYS.bearerToken) || getStoredToken())
  const [profiles, setProfiles] = useState<SavedProfile[]>(() => readJson(STORAGE_KEYS.profiles, []))
  const [expectedStatus, setExpectedStatus] = useState('200')
  const [mustInclude, setMustInclude] = useState('')
  const [maxMs, setMaxMs] = useState('')
  const [requestTimeoutMs, setRequestTimeoutMs] = useState('')
  const [artificialDelayMs, setArtificialDelayMs] = useState('')
  const [savedName, setSavedName] = useState('')
  const [savedNote, setSavedNote] = useState('')
  const [savedTags, setSavedTags] = useState('')
  const [captureText, setCaptureText] = useState('')
  const [savedTests, setSavedTests] = useState<SavedTest[]>(() => normalizeSavedTests(readJson(STORAGE_KEYS.savedTests, [])))
  const [snapshots, setSnapshots] = useState<SnapshotRecord[]>(() => readJson(STORAGE_KEYS.snapshots, []))
  const [scenarioSteps, setScenarioSteps] = useState<ScenarioStep[]>(() => readJson(STORAGE_KEYS.scenario, []))
  const [history, setHistory] = useState<RunRecord[]>(() => readJson(STORAGE_KEYS.history, []))
  const [historySearch, setHistorySearch] = useState(() => localStorage.getItem(STORAGE_KEYS.historySearch) || '')
  const [importText, setImportText] = useState('')
  const [response, setResponse] = useState<ResponseState | null>(null)
  const [runtimeVars, setRuntimeVars] = useState<Record<string, unknown>>({})
  const [snapshotBaseId, setSnapshotBaseId] = useState('')
  const [snapshotName, setSnapshotName] = useState('')
  const [profileName, setProfileName] = useState('')
  const [profileNote, setProfileNote] = useState('')
  const [scenarioName, setScenarioName] = useState('')
  const [scenarioCaptureText, setScenarioCaptureText] = useState('')
  const [scenarioStatus, setScenarioStatus] = useState('')
  const [scenarioReport, setScenarioReport] = useState<ScenarioReport | null>(null)
  const [selectedSnapshotId, setSelectedSnapshotId] = useState('')
  const [selectedHistoryId, setSelectedHistoryId] = useState('')
  const [selectedProfileId, setSelectedProfileId] = useState('')
  const [checks, setChecks] = useState<RunCheck[]>([])
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [lastCurl, setLastCurl] = useState('')
  const [savedMessage, setSavedMessage] = useState('')

  const headerParams = selected?.parameters.filter(param => param.in === 'header') || []
  const pathParams = selected?.parameters.filter(param => param.in === 'path') || []
  const queryParams = selected?.parameters.filter(param => param.in === 'query') || []
  useEffect(() => {
    setLoadingSpec(true)
    fetch(getOpenApiJsonUrl())
      .then(response => response.json())
      .then((spec: OpenAPI) => {
        const parsed = parseSpec(spec)
        setOps(parsed)
        const params = new URLSearchParams(location.search)
        const initialPath = params.get('path') || ''
        const initialCase = params.get('case') || ''
        const initialProfile = params.get('profile') || ''
        if (initialProfile) {
          const profile = profiles.find(item => item.id === initialProfile)
          if (profile) applyProfile(profile)
        }
        if (initialCase) {
          const saved = savedTests.find(item => item.id === initialCase)
          if (saved) {
            const operation = parsed.find(item => operationKey(item) === saved.draft.operationKey)
            if (operation) {
              applyDraft(operation, saved.draft)
              setSavedName(saved.name)
              setSavedNote(saved.note)
              setSavedTags(saved.tags.join(', '))
              setCaptureText(saved.captureText)
            }
          }
        } else if (initialPath) {
          const selectedFromPath = matchOperation(parsed, initialPath)
          if (selectedFromPath) {
            selectOperation(selectedFromPath)
          } else if (parsed[0]) {
            selectOperation(parsed[0])
          }
        } else if (parsed[0]) {
          selectOperation(parsed[0])
        }
      })
      .catch(() => setLoadError('Could not load /openapi.json'))
      .finally(() => setLoadingSpec(false))
  }, [])

  useEffect(() => {
    if (!ops.length) return
    const initialPath = new URLSearchParams(location.search).get('path') || ''
    if (!initialPath) return
    const selectedFromPath = matchOperation(ops, initialPath)
    if (selectedFromPath && (!selected || !sameOperation(selectedFromPath, selected))) {
      selectOperation(selectedFromPath)
    }
  }, [ops, location.search])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.baseUrl, baseUrl)
  }, [baseUrl])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.authMode, authMode)
  }, [authMode])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.bearerToken, bearerToken)
  }, [bearerToken])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.headersText, headersText)
  }, [headersText])

  useEffect(() => {
    writeJson(STORAGE_KEYS.profiles, profiles)
  }, [profiles])

  useEffect(() => {
    writeJson(STORAGE_KEYS.savedTests, savedTests)
  }, [savedTests])

  useEffect(() => {
    writeJson(STORAGE_KEYS.snapshots, snapshots)
  }, [snapshots])

  useEffect(() => {
    writeJson(STORAGE_KEYS.scenario, scenarioSteps)
  }, [scenarioSteps])

  useEffect(() => {
    writeJson(STORAGE_KEYS.history, history)
  }, [history])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.historySearch, historySearch)
  }, [historySearch])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.mode, mode)
  }, [mode])

  const groupedOps = useMemo(() => {
    const q = filter.trim().toLowerCase()
    const filtered = ops.filter(operation => {
      if (!q) return true
      return `${operation.method} ${operation.path} ${(operation.summary || '')} ${(operation.tags || []).join(' ')}`.toLowerCase().includes(q)
    })
    const groups: Record<string, Operation[]> = {}
    for (const operation of filtered) {
      for (const tag of operation.tags.length ? operation.tags : ['untagged']) {
        (groups[tag] ||= []).push(operation)
      }
    }
    return Object.entries(groups).sort((left, right) => left[0].localeCompare(right[0]))
  }, [ops, filter])

  const visibleHistory = useMemo(() => {
    const q = historySearch.trim().toLowerCase()
    return [...history]
      .sort((left, right) => Number(!!right.pinned) - Number(!!left.pinned) || right.at - left.at)
      .filter(item => !q || `${item.summary} ${item.path} ${item.method} ${item.status}`.toLowerCase().includes(q))
  }, [history, historySearch])

  const selectedSnapshot = snapshots.find(snapshot => snapshot.id === selectedSnapshotId) || null
  const latestRun = history[0] || null
  const showWorkspace = mode !== 'run'
  const showAdvanced = mode === 'debug'
  const showHistory = mode !== 'run'
  const showSnapshots = mode !== 'run'

  const draft = selected ? buildDraft(selected, {
    pathVals,
    queryVals,
    headerVals,
    body,
    headersText,
    authMode,
    bearerToken,
    baseUrl,
    expectedStatus,
    mustInclude,
    maxMs,
    captureText,
  }) : null

  const exportCurrentDraft = () => {
    if (!selected || !draft) return ''
    return JSON.stringify({
      kind: 'test-lab-case',
      draft,
      name: savedName || `${selected.method.toUpperCase()} ${selected.path}`,
      note: savedNote,
      tags: savedTags,
      captureText,
      profile: selectedProfileId,
      faults: {
        requestTimeoutMs,
        artificialDelayMs,
      },
      scenario: {
        name: scenarioName,
        captureText: scenarioCaptureText,
        steps: scenarioSteps,
      },
    }, null, 2)
  }

  const currentExport = useMemo(() => exportCurrentDraft(), [selected, draft, savedName, savedNote, savedTags, captureText, selectedProfileId, requestTimeoutMs, artificialDelayMs, scenarioName, scenarioCaptureText, scenarioSteps])

  const applyDraft = (operation: Operation, incomingDraft: TestDraft) => {
    setSelected(operation)
    setPathLookup(operation.path)
    syncQueryState({ path: operation.path, profileId: currentProfileQueryId() })
    setPathVals(incomingDraft.pathVals)
    setQueryVals(incomingDraft.queryVals)
    setHeaderVals(incomingDraft.headerVals || {})
    setBody(incomingDraft.body)
    setHeadersText(incomingDraft.headersText)
    setAuthMode(incomingDraft.authMode)
    setBearerToken(incomingDraft.bearerToken)
    setBaseUrl(incomingDraft.baseUrl)
    setExpectedStatus(incomingDraft.expectedStatus)
    setMustInclude(incomingDraft.mustInclude)
    setMaxMs(incomingDraft.maxMs)
  }

  const resolveDraftOperation = (incomingDraft: TestDraft) => ops.find(operation => operationKey(operation) === incomingDraft.operationKey) || null

  const syncQueryState = (values: { path?: string; caseId?: string; profileId?: string }) => {
    const params = new URLSearchParams(location.search)
    if (values.path) params.set('path', values.path)
    else params.delete('path')
    if (values.caseId) params.set('case', values.caseId)
    else params.delete('case')
    if (values.profileId) params.set('profile', values.profileId)
    else params.delete('profile')
    window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`)
  }

  const currentProfileQueryId = () => new URLSearchParams(location.search).get('profile') || selectedProfileId || undefined

  const applyProfile = (profile: SavedProfile) => {
    setProfileName(profile.name)
    setProfileNote(profile.note)
    setBaseUrl(profile.baseUrl)
    setAuthMode(profile.authMode)
    setBearerToken(profile.bearerToken)
    setHeadersText(profile.headersText)
    setSelectedProfileId(profile.id)
    syncQueryState({ path: selected?.path, profileId: profile.id })
  }

  const saveProfile = () => {
    const name = profileName.trim()
    if (!name) {
      setError('Profile name is required.')
      return
    }
    const next: SavedProfile = {
      id: uid(),
      name,
      note: profileNote.trim(),
      baseUrl,
      authMode,
      bearerToken,
      headersText,
    }
    setProfiles(current => [next, ...current.filter(item => item.name !== name)].slice(0, 20))
    setSelectedProfileId(next.id)
    syncQueryState({ path: selected?.path, profileId: next.id })
    setSavedMessage(`Saved profile "${name}".`)
    setTimeout(() => setSavedMessage(''), 1800)
  }

  const buildSavedTest = (currentDraft: TestDraft | null): SavedTest | null => {
    if (!selected || !currentDraft) return null
    return {
      id: uid(),
      name: savedName.trim() || `${selected.method.toUpperCase()} ${selected.path}`,
      note: savedNote.trim(),
      tags: savedTags.split(',').map(tag => tag.trim()).filter(Boolean),
      pinned: false,
      captureText: captureText.trim(),
      draft: currentDraft,
    }
  }

  const prepareDraftForRun = (source: TestDraft, vars: Record<string, unknown>): TestDraft => ({
    ...source,
    pathVals: Object.fromEntries(Object.entries(source.pathVals).map(([key, value]) => [key, interpolateString(value, vars)])),
    queryVals: Object.fromEntries(Object.entries(source.queryVals).map(([key, value]) => [key, interpolateString(value, vars)])),
    headerVals: Object.fromEntries(Object.entries(source.headerVals).map(([key, value]) => [key, interpolateString(value, vars)])),
    body: interpolateValue(source.body, vars) as Record<string, unknown>,
    headersText: interpolateString(source.headersText, vars),
    baseUrl: interpolateString(source.baseUrl, vars),
    bearerToken: interpolateString(source.bearerToken, vars),
    mustInclude: interpolateString(source.mustInclude, vars),
    captureText: interpolateString(source.captureText, vars),
  })

  const selectOperation = (operation: Operation) => {
    setSelected(operation)
    setPathLookup(operation.path)
    setPathVals(Object.fromEntries((operation.parameters || []).filter(param => param.in === 'path').map(param => [param.name, ''])))
    setQueryVals(Object.fromEntries((operation.parameters || []).filter(param => param.in === 'query').map(param => [param.name, ''])))
    setHeaderVals(Object.fromEntries((operation.parameters || []).filter(param => param.in === 'header').map(param => [param.name, ''])))
    setBody(buildInitialBody(operation.bodySchema))
    setRuntimeVars({})
    setResponse(null)
    setChecks([])
    setError('')
    setSavedMessage('')
    if (!savedName.trim()) {
      setSavedName(`${operation.method.toUpperCase()} ${operation.path}`)
    }
    syncQueryState({ path: operation.path, profileId: currentProfileQueryId() })
  }

  const openPath = (value: string) => {
    const match = matchOperation(ops, value)
    if (!match) {
      setError(`No endpoint matches "${value}".`)
      return
    }
    setPathLookup(value)
    selectOperation(match)
  }

  const executeDraft = async (incomingDraft: TestDraft, operationOverride?: Operation, vars: Record<string, unknown> = runtimeVars) => {
    const operation = operationOverride || resolveDraftOperation(incomingDraft)
    if (!operation) {
      setError('Selected endpoint is no longer available in the current OpenAPI spec.')
      return null
    }
    const draftForRun = prepareDraftForRun(incomingDraft, vars)

    setRunning(true)
    setError('')
    setSavedMessage('')
    setResponse(null)
    setChecks([])

    const start = performance.now()
    let requestHeaders: Record<string, string> = { Accept: 'application/json' }
    try {
      const headerOverrides = parseHeadersText(draftForRun.headersText)
      const authHeaders: Record<string, string> = {}
      if (draftForRun.authMode === 'session') {
        const token = getStoredToken()
        if (token) authHeaders.Authorization = `Bearer ${token}`
        const orgId = localStorage.getItem('org_id')
        if (orgId && orgId !== '-1') authHeaders['X-Org-ID'] = orgId
        const tenantId = localStorage.getItem('tenant_id')
        if (tenantId) authHeaders['X-Tenant-ID'] = tenantId
      } else if (draftForRun.authMode === 'bearer') {
        if (draftForRun.bearerToken.trim()) authHeaders.Authorization = `Bearer ${draftForRun.bearerToken.trim()}`
      }

      const pathHeaders: Record<string, string> = {}
      for (const param of operation.parameters.filter(item => item.in === 'header')) {
        const value = draftForRun.headerVals[param.name] || ''
        if (value !== '') pathHeaders[param.name] = String(value)
      }

      requestHeaders = {
        ...requestHeaders,
        ...authHeaders,
        ...pathHeaders,
        ...headerOverrides,
      }

      const params: Record<string, string> = {}
      for (const param of operation.parameters.filter(item => item.in === 'query')) {
        const value = draftForRun.queryVals[param.name]
        if (value !== undefined && value !== '') params[param.name] = value
      }

      let requestPath = cleanApiPath(operation.path)
      for (const param of operation.parameters.filter(item => item.in === 'path')) {
        requestPath = requestPath.replace(`{${param.name}}`, encodeURIComponent(draftForRun.pathVals[param.name] || ''))
      }

      const hasBody = operation.method !== 'get' && operation.method !== 'delete' && !!operation.bodySchema
      const requestBody = hasBody ? coerceBody(draftForRun.body, operation.bodySchema!) : undefined
      if (requestBody !== undefined) requestHeaders['Content-Type'] = 'application/json'
      const timeoutValue = Number(interpolateString(requestTimeoutMs, vars))
      const artificialDelayValue = Number(interpolateString(artificialDelayMs, vars))
      if (Number.isFinite(artificialDelayValue) && artificialDelayValue > 0) {
        await new Promise(resolve => setTimeout(resolve, artificialDelayValue))
      }

      const url = buildUrl(draftForRun.baseUrl, requestPath)
      const res = await axios.request({
        method: operation.method,
        url,
        params,
        data: requestBody,
        headers: requestHeaders,
        timeout: Number.isFinite(timeoutValue) && timeoutValue > 0 ? timeoutValue : undefined,
        validateStatus: () => true,
      })

      const ms = Math.round(performance.now() - start)
      const responseState: ResponseState = {
        status: res.status,
        data: res.data,
        headers: res.headers as Record<string, unknown>,
        ms,
        url,
      }
      setResponse(responseState)

      const nextChecks: RunCheck[] = []
      if (draftForRun.expectedStatus.trim()) {
        const expected = Number(draftForRun.expectedStatus)
        const ok = Number.isFinite(expected) ? res.status === expected : false
        nextChecks.push({
          label: `Status ${draftForRun.expectedStatus}`,
          ok,
          detail: ok ? `Received ${res.status}` : `Received ${res.status}`,
        })
      }
      if (draftForRun.mustInclude.trim()) {
        const needle = draftForRun.mustInclude.toLowerCase()
        const haystack = `${JSON.stringify(res.data)} ${JSON.stringify(res.headers)}`.toLowerCase()
        const ok = haystack.includes(needle)
        nextChecks.push({
          label: `Contains "${draftForRun.mustInclude}"`,
          ok,
          detail: ok ? 'Found in response payload or headers.' : 'Not found in response payload or headers.',
        })
      }
      if (draftForRun.maxMs.trim()) {
        const threshold = Number(draftForRun.maxMs)
        const ok = Number.isFinite(threshold) ? ms <= threshold : false
        nextChecks.push({
          label: `<= ${draftForRun.maxMs} ms`,
          ok,
          detail: ok ? `Completed in ${ms} ms` : `Completed in ${ms} ms`,
        })
      }
      setChecks(nextChecks)

      const overallOk = nextChecks.length ? nextChecks.every(item => item.ok) : res.status < 400
      const summary = `${operation.method.toUpperCase()} ${operation.path} -> ${res.status} in ${ms} ms`
      const nextVars = {
        ...vars,
        ...extractVariables(responseState, draftForRun.captureText),
      }
      setRuntimeVars(nextVars)
      const record: RunRecord = {
        id: uid(),
        at: Date.now(),
        operation: operation.path,
        method: operation.method.toUpperCase(),
        path: operation.path,
        status: res.status,
        ms,
        ok: overallOk,
        summary,
        draft: draftForRun,
      }
      setHistory(current => [record, ...current].slice(0, 30))
      setLastCurl(buildCurl({
        method: operation.method,
        url,
        headers: requestHeaders,
        body: requestBody,
      }))
      return { response: responseState, vars: nextVars, ok: overallOk }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'request failed'
      setError(errorMessage)
      return null
    } finally {
      setRunning(false)
    }
  }

  const runCurrent = () => {
    if (!draft || !selected) return
    executeDraft(draft, selected).catch(() => {})
  }

  const runSaved = (test: SavedTest) => {
    const operation = resolveDraftOperation(test.draft)
    if (!operation) {
      setError(`"${test.name}" points to an endpoint that is no longer available.`)
      return
    }
    const draft = { ...test.draft, captureText: test.captureText || '' }
    applyDraft(operation, draft)
    syncQueryState({ path: operation.path, caseId: test.id, profileId: currentProfileQueryId() })
    executeDraft(draft, operation).catch(() => {})
  }

  const saveCurrent = () => {
    const next = buildSavedTest(draft)
    if (!next) return
    setSavedTests(current => [next, ...current.filter(item => item.name !== next.name)].slice(0, 20))
    syncQueryState({ path: selected?.path, caseId: next.id, profileId: currentProfileQueryId() })
    setSavedMessage(`Saved "${next.name}".`)
    setTimeout(() => setSavedMessage(''), 2000)
  }

  const loadSaved = (test: SavedTest) => {
    const operation = resolveDraftOperation(test.draft)
    if (!operation) {
      setError(`"${test.name}" points to an endpoint that is no longer available.`)
      return
    }
    const draft = { ...test.draft, captureText: test.captureText }
    applyDraft(operation, draft)
    setSavedName(test.name)
    setSavedNote(test.note)
    setSavedTags(Array.isArray(test.tags) ? test.tags.join(', ') : '')
    setCaptureText(test.captureText || '')
    setSelectedHistoryId('')
    syncQueryState({ path: operation.path, caseId: test.id, profileId: currentProfileQueryId() })
  }

  const saveSnapshot = () => {
    if (!selected || !response) {
      setError('Run a request before saving a snapshot.')
      return
    }
    const next: SnapshotRecord = {
      id: uid(),
      name: snapshotName.trim() || `${selected.method.toUpperCase()} ${selected.path} @ ${new Date().toISOString()}`,
      operationKey: operationKey(selected),
      response,
      responseText: safeJson(response.data),
      diffBaseId: snapshotBaseId || undefined,
    }
    setSnapshots(current => [next, ...current].slice(0, 30))
    setSelectedSnapshotId(next.id)
    setSavedMessage(`Saved snapshot "${next.name}".`)
    setTimeout(() => setSavedMessage(''), 1800)
  }

  const addScenarioStep = () => {
    if (!selected || !draft) {
      setError('Select an endpoint before adding a scenario step.')
      return
    }
    const step: ScenarioStep = {
      id: uid(),
      name: savedName.trim() || `${selected.method.toUpperCase()} ${selected.path}`,
      captureText: scenarioCaptureText.trim(),
      draft,
    }
    setScenarioSteps(current => [...current, step])
    setSavedMessage(`Added "${step.name}" to the scenario.`)
    setTimeout(() => setSavedMessage(''), 1800)
  }

  const buildTemplateDraft = (operation: Operation, captureText = '', expectedStatus = ''): TestDraft => buildDraft(operation, {
    pathVals: Object.fromEntries((operation.parameters || []).filter(param => param.in === 'path').map(param => [param.name, ''])),
    queryVals: Object.fromEntries((operation.parameters || []).filter(param => param.in === 'query').map(param => [param.name, ''])),
    headerVals: Object.fromEntries((operation.parameters || []).filter(param => param.in === 'header').map(param => [param.name, ''])),
    body: buildInitialBody(operation.bodySchema),
    headersText,
    authMode,
    bearerToken,
    baseUrl,
    expectedStatus: expectedStatus || (operation.method === 'post' ? '201' : '200'),
    mustInclude: '',
    maxMs: '',
    captureText,
  })

  const loadScenarioTemplate = (template: ScenarioTemplate) => {
    const builtSteps = template.steps.map(step => {
      const operation = findOperationByPath(ops, step.method, step.path)
      if (!operation) return null
      return {
        id: uid(),
        name: step.name || `${operation.method.toUpperCase()} ${operation.path}`,
        captureText: step.captureText || '',
        draft: buildTemplateDraft(operation, step.captureText || '', step.expectedStatus || ''),
      }
    }).filter(Boolean) as ScenarioStep[]

    if (!builtSteps.length) {
      setError(`No matching endpoints found for "${template.name}".`)
      return
    }

    setError('')
    setScenarioName(template.name)
    setScenarioCaptureText('')
    setScenarioSteps(builtSteps)
    setSavedMessage(`Loaded scenario "${template.name}".`)
    setTimeout(() => setSavedMessage(''), 1800)
  }

  const removeScenarioStep = (id: string) => {
    setScenarioSteps(current => current.filter(step => step.id !== id))
  }

  const runScenario = async () => {
    if (!scenarioSteps.length) {
      setError('Add at least one step to the scenario.')
      return
    }
    setScenarioStatus(`Running scenario${scenarioName ? `: ${scenarioName}` : ''}...`)
    setScenarioReport(null)
    let vars = { ...runtimeVars }
    let lastResult: { response: ResponseState; vars: Record<string, unknown>; ok: boolean } | null = null
    const stepResults: ScenarioStepResult[] = []
    let completedAll = true
    for (const step of scenarioSteps) {
      const operation = resolveDraftOperation(step.draft)
      if (!operation) {
        setScenarioStatus(`Skipped missing endpoint in "${step.name}".`)
        completedAll = false
        break
      }
      const mergedDraft: TestDraft = {
        ...step.draft,
        captureText: step.captureText || step.draft.captureText,
      }
      lastResult = await executeDraft(mergedDraft, operation, vars)
      if (!lastResult) {
        setScenarioStatus(`Stopped at "${step.name}".`)
        return
      }
      stepResults.push({
        stepId: step.id,
        name: step.name,
        operationKey: step.draft.operationKey,
        status: lastResult.response.status,
        ms: lastResult.response.ms,
        ok: lastResult.ok,
      })
      vars = { ...lastResult.vars, ...extractVariables(lastResult.response, step.captureText) }
    }
    setRuntimeVars(vars)
    const completed = Boolean(lastResult)
    const finalStatus = lastResult ? lastResult.response.status : null
    const finalMs = lastResult ? lastResult.response.ms : null
    setScenarioReport({
      id: uid(),
      at: Date.now(),
      name: scenarioName.trim() || 'Untitled scenario',
      ok: completed && completedAll,
      finalStatus,
      finalMs,
      steps: stepResults,
    })
    setScenarioStatus(completed && completedAll ? 'Scenario complete.' : 'Scenario stopped.')
    setTimeout(() => setScenarioStatus(''), 2200)
  }

  const toggleHistoryPin = (id: string) => {
    setHistory(current => current.map(item => item.id === id ? { ...item, pinned: !item.pinned } : item))
  }

  const importCase = () => {
    if (!importText.trim()) return
    try {
      const parsed = JSON.parse(importText)
      if (parsed?.kind !== 'test-lab-case' || !parsed.draft) {
        setError('Import must be a Test Lab JSON export.')
        return
      }
      const imported = parsed as { draft: TestDraft; name?: string; note?: string; tags?: string; captureText?: string; profile?: string; faults?: { requestTimeoutMs?: string; artificialDelayMs?: string }; scenario?: { name?: string; captureText?: string; steps?: ScenarioStep[] } }
      const operation = resolveDraftOperation(imported.draft)
      if (!operation) {
        setError('Imported case targets an endpoint that no longer exists.')
        return
      }
      applyDraft(operation, { ...imported.draft, captureText: imported.captureText || imported.draft.captureText })
      setSavedName(imported.name || `${operation.method.toUpperCase()} ${operation.path}`)
      setSavedNote(imported.note || '')
      setSavedTags(imported.tags || '')
      setCaptureText(imported.captureText || '')
      setSelectedProfileId(imported.profile || '')
      setRequestTimeoutMs(imported.faults?.requestTimeoutMs || '')
      setArtificialDelayMs(imported.faults?.artificialDelayMs || '')
      setScenarioName(imported.scenario?.name || '')
      setScenarioCaptureText(imported.scenario?.captureText || '')
      setScenarioSteps(Array.isArray(imported.scenario?.steps)
        ? imported.scenario.steps.map(step => ({
            ...step,
            captureText: step.captureText || '',
            draft: {
              ...step.draft,
              captureText: step.draft?.captureText || step.captureText || '',
              headerVals: step.draft?.headerVals || {},
            },
          }))
        : [])
      setImportText('')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Import failed.')
    }
  }

  const deleteSaved = (id: string) => {
    setSavedTests(current => current.filter(test => test.id !== id))
  }

  const refreshSpec = () => {
    setLoadError('')
    setLoadingSpec(true)
    fetch(getOpenApiJsonUrl())
      .then(response => response.json())
      .then((spec: OpenAPI) => setOps(parseSpec(spec)))
      .catch(() => setLoadError('Could not reload /openapi.json'))
      .finally(() => setLoadingSpec(false))
  }

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (!(event.metaKey || event.ctrlKey)) return
      const key = event.key.toLowerCase()
      if (key === 'enter' && draft && selected) {
        event.preventDefault()
        runCurrent()
      } else if (event.shiftKey && key === 's' && draft && selected) {
        event.preventDefault()
        saveCurrent()
      } else if (event.shiftKey && key === 'r') {
        event.preventDefault()
        refreshSpec()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [draft, selected, runCurrent, saveCurrent, refreshSpec])

  const copyCurl = async () => {
    if (!draft || !selected) return
    const operation = resolveDraftOperation(draft) || selected
    const draftForRun = prepareDraftForRun(draft, runtimeVars)
    let requestHeaders: Record<string, string> = { Accept: 'application/json' }
    try {
      const headerOverrides = parseHeadersText(draftForRun.headersText)
      const authHeaders: Record<string, string> = {}
      if (draftForRun.authMode === 'session') {
        const token = getStoredToken()
        if (token) authHeaders.Authorization = `Bearer ${token}`
        const orgId = localStorage.getItem('org_id')
        if (orgId && orgId !== '-1') authHeaders['X-Org-ID'] = orgId
        const tenantId = localStorage.getItem('tenant_id')
        if (tenantId) authHeaders['X-Tenant-ID'] = tenantId
      } else if (draftForRun.authMode === 'bearer' && draftForRun.bearerToken.trim()) {
        authHeaders.Authorization = `Bearer ${draftForRun.bearerToken.trim()}`
      }
      requestHeaders = {
        ...requestHeaders,
        ...authHeaders,
        ...headerOverrides,
      }
      const requestBody = operation.method !== 'get' && operation.method !== 'delete' && operation.bodySchema
        ? coerceBody(draftForRun.body, operation.bodySchema)
        : undefined
      if (requestBody !== undefined) requestHeaders['Content-Type'] = 'application/json'
      const requestPath = cleanApiPath(operation.path).replace(/\{([^}]+)\}/g, (_, name) => encodeURIComponent(draftForRun.pathVals[name] || ''))
      const url = buildUrl(draftForRun.baseUrl, requestPath)
      const curl = buildCurl({ method: operation.method, url, headers: requestHeaders, body: requestBody })
      await navigator.clipboard.writeText(curl)
      setSavedMessage('cURL copied.')
      setTimeout(() => setSavedMessage(''), 1400)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not copy cURL.')
    }
  }

  const responseRows = asRows(response?.data)
  const responseHeaders = response ? splitHeaders(response.headers) : []
  const pathSearchValue = pathLookup
  const defaultSavedName = selected ? `${selected.method.toUpperCase()} ${selected.path}` : ''

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-black text-[var(--text)]">Test Lab</h2>
            <span className="rounded-full border border-[var(--line)] bg-[var(--surface)] px-2.5 py-1 text-[11px] font-black uppercase tracking-[0.14em] text-[var(--text-3)]">
              OpenAPI runner
            </span>
            <span className="rounded-full border border-[var(--line)] bg-[var(--surface-2)] px-2.5 py-1 text-[11px] font-black uppercase tracking-[0.14em] text-[var(--text-3)]">
              {mode}
            </span>
          </div>
          <p className="mt-1 text-sm font-medium text-[var(--text-3)]">
            Run endpoints, switch auth context, save repeatable cases, and replay failures with assertions.
          </p>
        </div>

        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <div className="flex rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] p-1">
            {([
              { key: 'run', label: 'Run' },
              { key: 'explore', label: 'Explore' },
              { key: 'debug', label: 'Debug' },
            ] as const).map(option => (
              <button
                key={option.key}
                onClick={() => setMode(option.key)}
                className={`h-8 rounded-[var(--radius)] px-3 text-xs font-black ${
                  mode === option.key
                    ? 'border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] shadow-sm'
                    : 'text-[var(--text-3)] hover:text-[var(--text-2)]'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
          <button
            onClick={refreshSpec}
            className="flex h-9 items-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 text-xs font-black text-[var(--text)] hover:bg-[var(--surface-2)]"
          >
            <RefreshCw size={14} className={loadingSpec ? 'animate-spin' : ''} />
            Refresh Spec
          </button>
          <button
            onClick={copyCurl}
            disabled={!selected}
            className="flex h-9 items-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 text-xs font-black text-[var(--text)] hover:bg-[var(--surface-2)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Copy size={14} />
            Copy cURL
          </button>
          <button
            onClick={runCurrent}
            disabled={!selected || running}
            className="flex h-9 items-center gap-2 rounded-[var(--radius)] bg-[var(--accent)] px-3 text-xs font-black text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Run
          </button>
        </div>
      </div>

      {loadError && <div className="rounded-[var(--radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{loadError}</div>}
      {savedMessage && <div className="rounded-[var(--radius)] border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700">{savedMessage}</div>}
      {error && <div className="rounded-[var(--radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</div>}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[360px_1fr]">
        <aside className="space-y-5">
          <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-black text-[var(--text)]">
              <Shield size={16} />
              Request Context
            </div>
            <div className="space-y-3">
              <div>
                <label className="mb-1.5 block text-[10px] font-black uppercase tracking-[0.14em] text-[var(--text-3)]">Base URL</label>
                <input
                  value={baseUrl}
                  onChange={event => setBaseUrl(event.target.value)}
                  placeholder={getBackendOrigin()}
                  className="h-9 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-sm font-semibold text-[var(--text)] outline-none focus:border-[var(--accent)]"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-[10px] font-black uppercase tracking-[0.14em] text-[var(--text-3)]">Auth</label>
                <div className="flex rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] p-1">
                  {([
                    { key: 'session', label: 'Current' },
                    { key: 'anonymous', label: 'Anon' },
                    { key: 'bearer', label: 'Bearer' },
                  ] as const).map(option => (
                    <button
                      key={option.key}
                      onClick={() => setAuthMode(option.key)}
                      className={`flex-1 rounded-[var(--radius)] px-2 py-1.5 text-xs font-black ${
                        authMode === option.key
                          ? 'bg-[var(--surface)] text-[var(--text)] shadow-sm border border-[var(--line)]'
                          : 'text-[var(--text-3)] hover:text-[var(--text-2)]'
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              {authMode === 'bearer' && (
                <div>
                  <label className="mb-1.5 block text-[10px] font-black uppercase tracking-[0.14em] text-[var(--text-3)]">Bearer Token</label>
                  <input
                    value={bearerToken}
                    onChange={event => setBearerToken(event.target.value)}
                    placeholder="paste token"
                    className="h-9 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-sm font-mono text-[var(--text)] outline-none focus:border-[var(--accent)]"
                  />
                </div>
              )}

              <div>
                <label className="mb-1.5 block text-[10px] font-black uppercase tracking-[0.14em] text-[var(--text-3)]">Custom Headers</label>
                <textarea
                  value={headersText}
                  onChange={event => setHeadersText(event.target.value)}
                  rows={4}
                  className="w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-2 text-xs font-mono text-[var(--text)] outline-none focus:border-[var(--accent)]"
                  placeholder='{"X-Debug":"1"}'
                />
              </div>

                <div className={showAdvanced ? 'grid grid-cols-2 gap-2' : 'hidden'}>
                  <div>
                    <label className="mb-1.5 block text-[10px] font-black uppercase tracking-[0.14em] text-[var(--text-3)]">Timeout ms</label>
                    <input
                      value={requestTimeoutMs}
                      onChange={event => setRequestTimeoutMs(event.target.value)}
                      placeholder="5000"
                      className="h-9 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-sm font-semibold text-[var(--text)] outline-none focus:border-[var(--accent)]"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-[10px] font-black uppercase tracking-[0.14em] text-[var(--text-3)]">Delay ms</label>
                    <input
                      value={artificialDelayMs}
                      onChange={event => setArtificialDelayMs(event.target.value)}
                      placeholder="0"
                      className="h-9 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-sm font-semibold text-[var(--text)] outline-none focus:border-[var(--accent)]"
                    />
                  </div>
                </div>

              <div>
                <label className="mb-1.5 block text-[10px] font-black uppercase tracking-[0.14em] text-[var(--text-3)]">Jump to path</label>
                <div className="flex gap-2">
                  <input
                    value={pathSearchValue}
                    onChange={event => setPathLookup(event.target.value)}
                    onKeyDown={event => event.key === 'Enter' && openPath(pathSearchValue)}
                    placeholder="/api/v1/dev/info"
                    className="h-9 min-w-0 flex-1 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-sm font-mono text-[var(--text)] outline-none focus:border-[var(--accent)]"
                  />
                  <button
                    onClick={() => openPath(pathSearchValue)}
                    className="flex h-9 items-center gap-2 rounded-[var(--radius)] bg-[var(--accent)] px-3 text-xs font-black text-white hover:opacity-90"
                  >
                    <ChevronRight size={14} />
                    Open
                  </button>
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-black text-[var(--text)]">
                <Search size={16} />
                Endpoints
              </div>
              <span className="text-xs font-bold text-[var(--text-3)]">{ops.length}</span>
            </div>
            <div className="mb-3 flex items-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-2">
              <Search size={14} className="text-[var(--text-3)]" />
              <input
                value={filter}
                onChange={event => setFilter(event.target.value)}
                placeholder="Filter path, tag, summary"
                className="min-w-0 flex-1 bg-transparent text-sm font-semibold text-[var(--text)] outline-none"
              />
            </div>
            <div className="max-h-[460px] overflow-auto pr-1">
              {groupedOps.map(([tag, list]) => (
                <div key={tag} className="mb-3 last:mb-0">
                  <div className="sticky top-0 z-10 mb-1 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.16em] text-[var(--text-3)]">
                    {tag}
                  </div>
                  <div className="space-y-1">
                    {list.map(operation => {
                      const active = selected ? sameOperation(operation, selected) : false
                      return (
                        <button
                          key={`${operation.method}:${operation.path}`}
                          onClick={() => setSelected(operation)}
                          className={`w-full rounded-[var(--radius)] border px-3 py-2 text-left transition-colors ${
                            active
                              ? 'border-[var(--accent)] bg-[var(--accent)]/8'
                              : 'border-[var(--line)] bg-[var(--surface)] hover:bg-[var(--surface-2)]'
                          }`}
                        >
                          <div className="flex items-start gap-2">
                            <span className={`mt-0.5 rounded px-1.5 py-0.5 text-[9px] font-black uppercase ${methodColor[operation.method]}`}>{operation.method}</span>
                            <div className="min-w-0 flex-1">
                              <code className="block truncate text-xs font-bold text-[var(--accent)]">{operation.path}</code>
                              <div className="mt-0.5 truncate text-[11px] font-semibold text-[var(--text-3)]">{operation.summary || 'No summary'}</div>
                            </div>
                          </div>
                        </button>
                      )
                    })}
                  </div>
                </div>
              ))}
              {!groupedOps.length && (
                <div className="py-8 text-center text-sm font-semibold text-[var(--text-3)]">No endpoints match.</div>
              )}
            </div>
          </section>

          <section className={`rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4 ${showWorkspace ? '' : 'hidden'}`}>
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-black text-[var(--text)]">
                <Save size={16} />
                Saved Cases
              </div>
              <span className="text-xs font-bold text-[var(--text-3)]">{savedTests.length}</span>
            </div>
            <div className="space-y-2">
              <input
                value={savedName}
                onChange={event => setSavedName(event.target.value)}
                placeholder={defaultSavedName}
                className="h-9 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-sm font-semibold text-[var(--text)] outline-none focus:border-[var(--accent)]"
              />
              <textarea
                value={savedNote}
                onChange={event => setSavedNote(event.target.value)}
                placeholder="Optional note"
                rows={2}
                className="w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-2 text-xs font-medium text-[var(--text)] outline-none focus:border-[var(--accent)]"
              />
              <input
                value={savedTags}
                onChange={event => setSavedTags(event.target.value)}
                placeholder="tags, separated, by commas"
                className="h-9 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-sm font-semibold text-[var(--text)] outline-none focus:border-[var(--accent)]"
              />
              <textarea
                value={captureText}
                onChange={event => setCaptureText(event.target.value)}
                placeholder="capture lines, e.g. token = data.token"
                rows={2}
                className="w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-2 text-xs font-mono text-[var(--text)] outline-none focus:border-[var(--accent)]"
              />
              <button
                onClick={saveCurrent}
                disabled={!selected}
                className="flex h-9 w-full items-center justify-center gap-2 rounded-[var(--radius)] bg-[var(--accent)] px-3 text-xs font-black text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Save size={14} />
                Save Current Case
              </button>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={addScenarioStep}
                  disabled={!selected}
                  className="flex h-9 items-center justify-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 text-xs font-black text-[var(--text)] hover:bg-[var(--surface-2)] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Play size={14} />
                  Add Step
                </button>
                <button
                  onClick={saveSnapshot}
                  disabled={!response}
                  className="flex h-9 items-center justify-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 text-xs font-black text-[var(--text)] hover:bg-[var(--surface-2)] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Download size={14} />
                  Snapshot
                </button>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setImportText(currentExport)}
                  disabled={!currentExport}
                  className="flex h-9 items-center justify-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 text-xs font-black text-[var(--text)] hover:bg-[var(--surface-2)] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Download size={14} />
                  Export
                </button>
                <button
                  onClick={importCase}
                  disabled={!importText.trim()}
                  className="flex h-9 items-center justify-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 text-xs font-black text-[var(--text)] hover:bg-[var(--surface-2)] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Upload size={14} />
                  Import
                </button>
              </div>
            </div>
            <div className="mt-3 max-h-[280px] space-y-2 overflow-auto pr-1">
              {savedTests.length ? savedTests.map(test => (
                <div key={test.id} className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <div className="truncate text-sm font-black text-[var(--text)]">{test.name}</div>
                        {test.pinned && <Pin size={11} className="text-[var(--accent)]" />}
                      </div>
                      <div className="mt-0.5 truncate text-xs font-mono text-[var(--text-3)]">{test.draft.operationKey}</div>
                      {test.tags.length > 0 && <div className="mt-1 flex flex-wrap gap-1">{test.tags.map(tag => <span key={tag} className="rounded-full bg-[var(--surface)] px-2 py-0.5 text-[10px] font-black uppercase text-[var(--text-3)]">{tag}</span>)}</div>}
                      {test.note && <div className="mt-1 text-xs text-[var(--text-3)]">{test.note}</div>}
                      {test.captureText && <div className="mt-1 whitespace-pre-wrap text-[10px] font-mono text-[var(--text-3)]">{test.captureText}</div>}
                    </div>
                    <button
                      onClick={() => deleteSaved(test.id)}
                      className="rounded-[var(--radius)] p-1.5 text-[var(--text-3)] hover:bg-[var(--surface)] hover:text-red-600"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={() => loadSaved(test)}
                      className="flex-1 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-1.5 text-xs font-bold text-[var(--text)] hover:bg-[var(--surface)]"
                    >
                      Load
                    </button>
                    <button
                      onClick={() => runSaved(test)}
                      className="flex-1 rounded-[var(--radius)] bg-[var(--accent)] px-3 py-1.5 text-xs font-black text-white hover:opacity-90"
                    >
                      Run
                    </button>
                    <button
                      onClick={() => setSavedTests(current => current.map(item => item.id === test.id ? { ...item, pinned: !item.pinned } : item))}
                      className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-1.5 text-xs font-black text-[var(--text)] hover:bg-[var(--surface)]"
                    >
                      <Pin size={13} />
                    </button>
                  </div>
                </div>
              )) : (
                <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-4 text-sm font-semibold text-[var(--text-3)]">
                  Save a request once, then replay it with one click.
                </div>
              )}
            </div>
          </section>
          <section className={`rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4 ${showAdvanced ? '' : 'hidden'}`}>
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-black text-[var(--text)]">
                <Shield size={16} />
                Profiles
              </div>
              <span className="text-xs font-bold text-[var(--text-3)]">{profiles.length}</span>
            </div>
            <div className="space-y-2">
              <input value={profileName} onChange={event => setProfileName(event.target.value)} placeholder="Profile name" className="h-9 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-sm font-semibold text-[var(--text)] outline-none focus:border-[var(--accent)]" />
              <textarea value={profileNote} onChange={event => setProfileNote(event.target.value)} placeholder="Optional note" rows={2} className="w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-2 text-xs font-medium text-[var(--text)] outline-none focus:border-[var(--accent)]" />
              <button onClick={saveProfile} className="flex h-9 w-full items-center justify-center gap-2 rounded-[var(--radius)] bg-[var(--accent)] px-3 text-xs font-black text-white hover:opacity-90">
                <Save size={14} />
                Save Profile
              </button>
            </div>
            <div className="mt-3 max-h-[220px] space-y-2 overflow-auto pr-1">
              {profiles.length ? profiles.map(profile => (
                <div key={profile.id} className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-black text-[var(--text)]">{profile.name}</div>
                      {profile.note && <div className="mt-1 text-xs text-[var(--text-3)]">{profile.note}</div>}
                      <div className="mt-1 truncate text-[10px] font-mono text-[var(--text-3)]">{profile.baseUrl}</div>
                    </div>
                    <button onClick={() => setProfiles(current => current.filter(item => item.id !== profile.id))} className="rounded-[var(--radius)] p-1.5 text-[var(--text-3)] hover:bg-[var(--surface)] hover:text-red-600">
                      <Trash2 size={13} />
                    </button>
                  </div>
                  <button onClick={() => applyProfile(profile)} className={`mt-3 w-full rounded-[var(--radius)] border px-3 py-1.5 text-xs font-black ${selectedProfileId === profile.id ? 'border-[var(--accent)] bg-[var(--accent)]/8 text-[var(--text)]' : 'border-[var(--line)] bg-[var(--surface)] text-[var(--text)] hover:bg-[var(--surface)]'}`}>
                    Apply
                  </button>
                </div>
              )) : <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-4 text-sm font-semibold text-[var(--text-3)]">Store auth and base URL presets here.</div>}
            </div>
          </section>

          <section className={`rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4 ${showWorkspace ? '' : 'hidden'}`}>
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-black text-[var(--text)]">
                <Play size={16} />
                Scenario
              </div>
              <span className="text-xs font-bold text-[var(--text-3)]">{scenarioSteps.length}</span>
            </div>
            <div className="space-y-2">
              <div className="space-y-2">
                {SCENARIO_TEMPLATES.map(template => (
                  <button
                    key={template.id}
                    onClick={() => loadScenarioTemplate(template)}
                    className="w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-2 text-left hover:bg-[var(--surface)]"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate text-xs font-black text-[var(--text)]">{template.name}</div>
                        <div className="mt-0.5 truncate text-[11px] text-[var(--text-3)]">{template.description}</div>
                      </div>
                      <Wand2 size={13} className="shrink-0 text-[var(--accent)]" />
                    </div>
                  </button>
                ))}
              </div>
              <input value={scenarioName} onChange={event => setScenarioName(event.target.value)} placeholder="Scenario name" className="h-9 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-sm font-semibold text-[var(--text)] outline-none focus:border-[var(--accent)]" />
              <textarea value={scenarioCaptureText} onChange={event => setScenarioCaptureText(event.target.value)} placeholder="capture lines for the current step" rows={2} className="w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-2 text-xs font-mono text-[var(--text)] outline-none focus:border-[var(--accent)]" />
              <button onClick={runScenario} disabled={!scenarioSteps.length || running} className="flex h-9 w-full items-center justify-center gap-2 rounded-[var(--radius)] bg-[var(--accent)] px-3 text-xs font-black text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50">
                {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                Run Scenario
              </button>
              {scenarioStatus && <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-2 text-xs font-semibold text-[var(--text-3)]">{scenarioStatus}</div>}
              {scenarioReport && (
                <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-black text-[var(--text)]">{scenarioReport.name}</div>
                      <div className="mt-0.5 text-[11px] text-[var(--text-3)]">
                        {new Date(scenarioReport.at).toLocaleString()} · {scenarioReport.steps.length} step{scenarioReport.steps.length === 1 ? '' : 's'}
                      </div>
                    </div>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-black uppercase ${scenarioReport.ok ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                      {scenarioReport.ok ? 'PASS' : 'FAIL'}
                    </span>
                  </div>
                  <div className="mt-3 space-y-2">
                    {scenarioReport.steps.map(step => (
                      <div key={step.stepId} className={`flex items-center justify-between gap-3 rounded-[var(--radius)] px-3 py-2 text-xs ${step.ok ? 'bg-emerald-50 text-emerald-800' : 'bg-red-50 text-red-700'}`}>
                        <div className="min-w-0">
                          <div className="truncate font-bold">{step.name}</div>
                          <div className="mt-0.5 truncate font-mono opacity-80">{step.operationKey}</div>
                        </div>
                        <div className="flex shrink-0 items-center gap-3 font-mono">
                          <span>{step.status}</span>
                          <span>{step.ms} ms</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 text-xs font-semibold text-[var(--text-3)]">
                    Final response: {scenarioReport.finalStatus ?? '-'} {scenarioReport.finalMs !== null ? `· ${scenarioReport.finalMs} ms` : ''}
                  </div>
                </div>
              )}
            </div>
            <div className="mt-3 max-h-[220px] space-y-2 overflow-auto pr-1">
              {scenarioSteps.length ? scenarioSteps.map((step, index) => (
                <div key={step.id} className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-black text-[var(--text)]">{index + 1}. {step.name}</div>
                      <div className="mt-0.5 truncate text-xs font-mono text-[var(--text-3)]">{step.draft.operationKey}</div>
                    </div>
                    <button onClick={() => removeScenarioStep(step.id)} className="rounded-[var(--radius)] p-1.5 text-[var(--text-3)] hover:bg-[var(--surface)] hover:text-red-600">
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              )) : <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-4 text-sm font-semibold text-[var(--text-3)]">Add one or more steps from the current request.</div>}
            </div>
          </section>

          <section className={`rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4 ${showWorkspace ? '' : 'hidden'}`}>
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-black text-[var(--text)]">
                <Upload size={16} />
                Import / Export
              </div>
            </div>
            <textarea value={importText || currentExport} onChange={event => setImportText(event.target.value)} rows={8} className="w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-2 text-xs font-mono text-[var(--text)] outline-none focus:border-[var(--accent)]" placeholder="Paste a Test Lab JSON export here..." />
            <div className="mt-2 flex gap-2">
              <button onClick={() => navigator.clipboard.writeText(currentExport)} disabled={!currentExport} className="flex-1 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-1.5 text-xs font-black text-[var(--text)] hover:bg-[var(--surface-2)] disabled:cursor-not-allowed disabled:opacity-50">Copy Export</button>
              <button onClick={importCase} disabled={!importText.trim()} className="flex-1 rounded-[var(--radius)] bg-[var(--accent)] px-3 py-1.5 text-xs font-black text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50">Import</button>
            </div>
          </section>
        </aside>

        <main className="space-y-5">
          <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-5">
            {selected ? (
              <div className="space-y-5">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`rounded px-2 py-1 text-[10px] font-black uppercase ${methodColor[selected.method]}`}>{selected.method}</span>
                      <code className="break-all text-base font-black text-[var(--text)]">{selected.path}</code>
                    </div>
                    {selected.summary && <p className="mt-2 text-sm text-[var(--text-3)]">{selected.summary}</p>}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => selected && setPathLookup(selected.path)}
                      className="flex h-9 items-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-xs font-black text-[var(--text)] hover:bg-[var(--surface)]"
                    >
                      <Clock3 size={14} />
                      Current Path
                    </button>
                    <button
                      onClick={copyCurl}
                      className="flex h-9 items-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-xs font-black text-[var(--text)] hover:bg-[var(--surface)]"
                    >
                      <Copy size={14} />
                      Copy cURL
                    </button>
                    <button
                      onClick={runCurrent}
                      disabled={running}
                      className="flex h-9 items-center gap-2 rounded-[var(--radius)] bg-[var(--accent)] px-3 text-xs font-black text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                      Run Request
                    </button>
                  </div>
                </div>

                {latestRun && (
                  <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] p-3">
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                      <div className="min-w-0">
                        <div className="text-[10px] font-black uppercase tracking-[0.16em] text-[var(--text-3)]">Run report</div>
                        <div className="mt-1 truncate text-sm font-black text-[var(--text)]">{latestRun.summary}</div>
                        <div className="mt-0.5 text-xs font-mono text-[var(--text-3)]">
                          {new Date(latestRun.at).toLocaleString()} · {latestRun.method} · {latestRun.path}
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase ${
                          latestRun.ok ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {latestRun.ok ? 'PASS' : 'FAIL'}
                        </span>
                        <span className="rounded-full border border-[var(--line)] bg-[var(--surface)] px-2.5 py-1 text-[10px] font-black uppercase text-[var(--text-3)]">
                          {latestRun.status} · {latestRun.ms} ms
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {pathParams.length > 0 && (
                  <FieldGroup title="Path Parameters">
                    {pathParams.map(param => (
                      <Field
                        key={param.name}
                        label={param.name}
                        required={param.required}
                        schema={param.schema}
                        value={pathVals[param.name] ?? ''}
                        onChange={value => setPathVals(current => ({ ...current, [param.name]: String(value ?? '') }))}
                      />
                    ))}
                  </FieldGroup>
                )}

                {queryParams.length > 0 && (
                  <FieldGroup title="Query Parameters">
                    {queryParams.map(param => (
                      <Field
                        key={param.name}
                        label={param.name}
                        required={param.required}
                        schema={param.schema}
                        value={queryVals[param.name] ?? ''}
                        onChange={value => setQueryVals(current => ({ ...current, [param.name]: String(value ?? '') }))}
                      />
                    ))}
                  </FieldGroup>
                )}

                {headerParams.length > 0 && (
                  <FieldGroup title="Header Parameters">
                    {headerParams.map(param => (
                      <Field
                        key={param.name}
                        label={param.name}
                        required={param.required}
                        schema={param.schema}
                        value={headerVals[param.name] ?? ''}
                        onChange={value => setHeaderVals(current => ({ ...current, [param.name]: String(value ?? '') }))}
                      />
                    ))}
                  </FieldGroup>
                )}

                {selected.bodySchema?.properties && (
                  <FieldGroup title="Body">
                    {Object.entries(selected.bodySchema.properties).map(([key, schema]) => (
                      <Field
                        key={key}
                        label={key}
                        required={selected.bodySchema?.required?.includes(key)}
                        schema={schema}
                        value={body[key] as unknown}
                        onChange={value => setBody(current => ({ ...current, [key]: value }))}
                        multiline={schema.type === 'object' || schema.type === 'array'}
                      />
                    ))}
                  </FieldGroup>
                )}

                <FieldGroup title="Assertions">
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                    <Field
                      label="Expected Status"
                      schema={{ type: 'integer' }}
                      value={expectedStatus}
                      onChange={value => setExpectedStatus(String(value ?? ''))}
                    />
                    <Field
                      label="Response Contains"
                      schema={{ type: 'string' }}
                      value={mustInclude}
                      onChange={value => setMustInclude(String(value ?? ''))}
                    />
                    <Field
                      label="Max Time (ms)"
                      schema={{ type: 'integer' }}
                      value={maxMs}
                      onChange={value => setMaxMs(String(value ?? ''))}
                    />
                  </div>
                </FieldGroup>
              </div>
            ) : (
              <div className="flex min-h-[300px] items-center justify-center rounded-[var(--radius)] border border-dashed border-[var(--line)] bg-[var(--surface-2)] text-sm font-semibold text-[var(--text-3)]">
                Select an endpoint to start testing.
              </div>
            )}
          </section>

          <section className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
            <div className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-5">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-black text-[var(--text)]">
                  <Wand2 size={16} />
                  Latest Response
                </div>
                {response && (
                  <div className={`rounded-full px-2.5 py-1 text-[11px] font-black uppercase tracking-[0.12em] ${
                    response.status < 300
                      ? 'bg-emerald-100 text-emerald-700'
                      : response.status < 500
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-red-100 text-red-700'
                  }`}>
                    {response.status}
                  </div>
                )}
              </div>

              {response ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                    <Fact label="URL" value={response.url} mono />
                    <Fact label="Latency" value={formatMs(response.ms)} />
                    <Fact label="Checks" value={`${checks.filter(item => item.ok).length}/${checks.length || 0}`} />
                  </div>

                  {checks.length > 0 && (
                    <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] p-3">
                      <div className="mb-2 text-[10px] font-black uppercase tracking-[0.16em] text-[var(--text-3)]">Assertions</div>
                      <div className="space-y-1.5">
                        {checks.map(check => (
                          <div key={check.label} className={`flex items-start gap-2 rounded-[var(--radius)] px-2 py-1.5 text-sm ${
                            check.ok ? 'bg-emerald-50 text-emerald-800' : 'bg-red-50 text-red-700'
                          }`}>
                            {check.ok ? <Check size={14} className="mt-0.5" /> : <Trash2 size={14} className="mt-0.5" />}
                            <div className="min-w-0">
                              <div className="font-bold">{check.label}</div>
                              <div className="text-xs opacity-80">{check.detail}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {responseHeaders.length > 0 && (
                    <div>
                      <div className="mb-2 text-[10px] font-black uppercase tracking-[0.16em] text-[var(--text-3)]">Response Headers</div>
                      <DataGrid columns={['key', 'value']} rows={responseHeaders} maxHeight={180} />
                    </div>
                  )}

                  {responseRows ? (
                    <DataGrid columns={Object.keys(responseRows[0] || {})} rows={responseRows} maxHeight={360} />
                  ) : (
                    <pre className="max-h-[420px] overflow-auto rounded-[var(--radius)] border border-[var(--line)] bg-slate-950 p-4 text-xs text-slate-200">
                      {JSON.stringify(response.data, null, 2)}
                    </pre>
                  )}
                </div>
              ) : (
                <div className="rounded-[var(--radius)] border border-dashed border-[var(--line)] bg-[var(--surface-2)] px-4 py-10 text-center text-sm font-semibold text-[var(--text-3)]">
                  Run the request to inspect the response here.
                </div>
              )}
            </div>

            <div className="space-y-5">
              <section className={`rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4 ${showHistory ? '' : 'hidden'}`}>
                <div className="mb-2 flex items-center gap-2 text-sm font-black text-[var(--text)]">
                  <Copy size={16} />
                  Request Preview
                </div>
                <pre className="max-h-[260px] overflow-auto rounded-[var(--radius)] border border-[var(--line)] bg-slate-950 p-4 text-xs text-slate-200">
                  {lastCurl || 'Run a request to generate cURL.'}
                </pre>
              </section>

              <section className={`rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4 ${showHistory ? '' : 'hidden'}`}>
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-sm font-black text-[var(--text)]">
                    <History size={16} />
                    Recent Runs
                  </div>
                  <input
                    value={historySearch}
                    onChange={event => setHistorySearch(event.target.value)}
                    placeholder="Filter"
                    className="h-8 w-28 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-2 text-[11px] font-semibold text-[var(--text)] outline-none focus:border-[var(--accent)]"
                  />
                </div>
                <div className="max-h-[340px] space-y-2 overflow-auto pr-1">
                  {visibleHistory.length ? visibleHistory.map(item => (
                    <div key={item.id} className={`rounded-[var(--radius)] border p-3 ${selectedHistoryId === item.id ? 'border-[var(--accent)] bg-[var(--accent)]/8' : 'border-[var(--line)] bg-[var(--surface-2)]'}`}>
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <div className="truncate text-sm font-black text-[var(--text)]">{item.summary}</div>
                            {item.pinned && <Pin size={11} className="text-[var(--accent)]" />}
                          </div>
                          <div className="mt-1 text-xs font-mono text-[var(--text-3)]">
                            {new Date(item.at).toLocaleTimeString('en-GB', { hour12: false })}
                          </div>
                        </div>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-black uppercase ${
                          item.ok ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {item.ok ? 'PASS' : 'FAIL'}
                        </span>
                      </div>
                      <div className="mt-3 flex gap-2">
                        <button
                          onClick={() => {
                            setSelectedHistoryId(item.id)
                            executeDraft(item.draft, resolveDraftOperation(item.draft) || undefined).catch(() => {})
                          }}
                          className="flex-1 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-1.5 text-xs font-bold text-[var(--text)] hover:bg-[var(--surface)]"
                        >
                          Replay
                        </button>
                        <button
                          onClick={() => {
                            const operation = resolveDraftOperation(item.draft)
                            if (!operation) {
                              setError(`"${item.summary}" points to an endpoint that is no longer available.`)
                              return
                            }
                            setSelectedHistoryId(item.id)
                            applyDraft(operation, item.draft)
                          }}
                          className="flex-1 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-1.5 text-xs font-bold text-[var(--text)] hover:bg-[var(--surface)]"
                        >
                          Load case
                        </button>
                        <button
                          onClick={() => toggleHistoryPin(item.id)}
                          className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-1.5 text-xs font-black text-[var(--text)] hover:bg-[var(--surface)]"
                        >
                          <Pin size={13} />
                        </button>
                      </div>
                    </div>
                  )) : (
                    <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-4 text-sm font-semibold text-[var(--text-3)]">
                      Every run is recorded here so you can replay failures quickly.
                    </div>
                  )}
                </div>
              </section>

              <section className={`rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4 ${showSnapshots ? '' : 'hidden'}`}>
                <div className="mb-3 flex items-center gap-2 text-sm font-black text-[var(--text)]">
                  <Download size={16} />
                  Snapshots
                </div>
                <div className="space-y-2">
                  <input value={snapshotName} onChange={event => setSnapshotName(event.target.value)} placeholder="Snapshot name" className="h-9 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-sm font-semibold text-[var(--text)] outline-none focus:border-[var(--accent)]" />
                  <select value={snapshotBaseId} onChange={event => setSnapshotBaseId(event.target.value)} className="h-9 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 text-sm font-semibold text-[var(--text)] outline-none focus:border-[var(--accent)]">
                    <option value="">No base snapshot</option>
                    {snapshots.map(snapshot => <option key={snapshot.id} value={snapshot.id}>{snapshot.name}</option>)}
                  </select>
                  <button onClick={saveSnapshot} disabled={!response} className="flex h-9 w-full items-center justify-center gap-2 rounded-[var(--radius)] bg-[var(--accent)] px-3 text-xs font-black text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50">
                    <Download size={14} />
                    Save Snapshot
                  </button>
                </div>
                <div className="mt-3 max-h-[240px] space-y-2 overflow-auto pr-1">
                  {snapshots.length ? snapshots.map(snapshot => (
                    <div key={snapshot.id} className={`rounded-[var(--radius)] border p-3 ${selectedSnapshotId === snapshot.id ? 'border-[var(--accent)] bg-[var(--accent)]/8' : 'border-[var(--line)] bg-[var(--surface-2)]'}`}>
                      <div className="min-w-0">
                        <div className="truncate text-sm font-black text-[var(--text)]">{snapshot.name}</div>
                        <div className="mt-0.5 truncate text-xs font-mono text-[var(--text-3)]">{snapshot.operationKey}</div>
                      </div>
                      <div className="mt-2 flex gap-2">
                        <button onClick={() => setSelectedSnapshotId(snapshot.id)} className="flex-1 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-1.5 text-xs font-bold text-[var(--text)] hover:bg-[var(--surface)]">Select</button>
                        <button onClick={() => navigator.clipboard.writeText(snapshot.responseText)} className="flex-1 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-1.5 text-xs font-bold text-[var(--text)] hover:bg-[var(--surface)]">Copy</button>
                      </div>
                    </div>
                  )) : <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-4 text-sm font-semibold text-[var(--text-3)]">Save a response to compare later.</div>}
                </div>
                {selectedSnapshot && response && (
                  <div className="mt-3 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] p-3">
                    <div className="mb-2 text-[10px] font-black uppercase tracking-[0.16em] text-[var(--text-3)]">Diff</div>
                    <div className="max-h-[220px] overflow-auto font-mono text-[11px] leading-5 text-[var(--text)]">
                      {diffLines(selectedSnapshot.responseText, safeJson(response.data)).slice(0, 60).map((line, index) => (
                        <div key={index} className={line.same ? 'text-[var(--text-2)]' : 'text-red-700'}>
                          {line.same ? ' ' : line.left === undefined ? '+' : line.right === undefined ? '-' : '~'} {line.right ?? line.left}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}

function FieldGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2.5">
      <h4 className="text-[10px] font-black uppercase tracking-[0.16em] text-[var(--text-3)]">{title}</h4>
      {children}
    </div>
  )
}

function Field({
  label,
  required,
  schema,
  value,
  onChange,
  multiline = false,
}: {
  label: string
  required?: boolean
  schema?: JsonSchema
  value: unknown
  onChange: (value: unknown) => void
  multiline?: boolean
}) {
  const currentSchema = schema || {}
  const base = 'w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-2 text-sm font-mono text-[var(--text)] outline-none focus:border-[var(--accent)]'
  let input: React.ReactNode

  if (currentSchema.enum?.length) {
    input = (
      <select value={String(value ?? '')} onChange={event => onChange(event.target.value)} className={base}>
        <option value="">—</option>
        {currentSchema.enum.map(option => <option key={String(option)} value={String(option)}>{String(option)}</option>)}
      </select>
    )
  } else if (currentSchema.type === 'boolean') {
    input = <input type="checkbox" checked={Boolean(value)} onChange={event => onChange(event.target.checked)} className="h-4 w-4 accent-[var(--accent)]" />
  } else if (currentSchema.type === 'integer' || currentSchema.type === 'number') {
    input = <input type="number" value={String(value ?? '')} onChange={event => onChange(event.target.value)} className={base} />
  } else if (multiline || currentSchema.type === 'object' || currentSchema.type === 'array') {
    input = <textarea rows={4} value={typeof value === 'string' ? value : JSON.stringify(value, null, 2)} onChange={event => onChange(event.target.value)} className={`${base} resize-y`} />
  } else {
    input = <input type="text" value={String(value ?? '')} onChange={event => onChange(event.target.value)} className={base} />
  }

  return (
    <label className="block">
      <span className="mb-1 flex items-center gap-1 text-xs font-semibold text-[var(--text-2)]">
        {label}
        {required && <span className="text-red-500">*</span>}
        {currentSchema.type && <span className="font-mono font-normal text-[var(--text-3)]">{currentSchema.type}</span>}
      </span>
      {input}
    </label>
  )
}

function Fact({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="min-w-0 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] p-3">
      <div className="text-[10px] font-black uppercase tracking-[0.14em] text-[var(--text-3)]">{label}</div>
      <div className={`mt-1 truncate text-sm font-bold text-[var(--text)] ${mono ? 'font-mono' : ''}`} title={value}>{value}</div>
    </div>
  )
}

function coerceBody(body: Record<string, unknown>, schema: JsonSchema): Record<string, unknown> {
  const output: Record<string, unknown> = {}
  const properties = schema.properties || {}
  for (const [key, value] of Object.entries(body)) {
    const type = properties[key]?.type
    if (value === '' && !schema.required?.includes(key)) continue
    if ((type === 'object' || type === 'array') && typeof value === 'string') {
      try {
        output[key] = value.trim() ? JSON.parse(value) : (type === 'array' ? [] : {})
      } catch {
        output[key] = value
      }
    } else if (type === 'integer' || type === 'number') {
      output[key] = value === '' ? null : Number(value)
    } else {
      output[key] = value
    }
  }
  return output
}

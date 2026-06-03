import { expect, test } from '@playwright/test'

const authMe = {
  username: 'admin',
  email: 'admin@example.com',
  full_name: 'Admin User',
  is_admin: true,
  organizations: [{ id: 1, name: 'Org' }],
}

const devInfo = {
  framework: 'Aras',
  version: '1.0.0',
  engine: 'FastAPI + SQLAlchemy',
  apps_discovered: ['dev'],
  total_models: 12,
}

const devStats = [
  { table: 'core_apps', rows: 1 },
  { table: 'core_settings', rows: 12 },
  { table: 'dev_handoff_runs', rows: 0 },
]

const systemInfo = {
  os: 'Linux',
  os_release: '6.1',
  cpu_count: 8,
  python_version: '3.12.0',
  memory: { total: 8589934592, available: 4294967296, percent: 50 },
  process: { memory_usage: 12345678, cpu_percent: 3.5, threads: 12, uptime_seconds: 1234 },
}

const metrics = {
  uptime_seconds: 1234,
  total_requests: 42,
  total_errors: 0,
  error_rate: 0,
  rate_per_second: 1.2,
  latency_p50: 10,
  latency_p95: 20,
  latency_p99: 30,
  recent_requests: [
    { ts: 1710000000, method: 'GET', path: '/api/v1/dev/info', status: 200, ms: 11 },
    { ts: 1710000001, method: 'GET', path: '/api/v1/dev/dev/system-info', status: 200, ms: 17 },
  ],
  spark: [1, 2, 3, 2, 4, 3, 1],
  by_status: { '200': 2 },
}

const appsStatus = [
  { name: 'dev', label: 'Developer Tools', type: 'framework', models_count: 8, routers_count: 5 },
]

const routes = [
  {
    path: '/api/v1/dev/info',
    name: 'Framework info',
    methods: ['GET'],
    tags: ['Developer Tools'],
    summary: 'Framework version and registry counts',
    endpoint: 'core.api.dev:get_framework_info',
    auth: 'admin',
  },
  {
    path: '/api/v1/dev/dev/system-info',
    name: 'System info',
    methods: ['GET'],
    tags: ['Developer Tools'],
    summary: 'Runtime diagnostics',
    endpoint: 'apps.dev.dev_router:get_system_info',
    auth: 'admin',
  },
]

const openApi = {
  openapi: '3.1.0',
  info: { title: 'Aras API', version: '1.0.0' },
  paths: {
    '/api/v1/dev/info': {
      get: {
        tags: ['Developer Tools'],
        summary: 'Framework info',
        responses: { 200: { description: 'OK' } },
      },
    },
    '/api/v1/dev/stats': {
      get: {
        tags: ['Developer Tools'],
        summary: 'Registry stats',
        responses: { 200: { description: 'OK' } },
      },
    },
    '/api/v1/dev/inspect/routes': {
      get: {
        tags: ['Developer Tools'],
        summary: 'Inspect routes',
        responses: { 200: { description: 'OK' } },
      },
    },
    '/api/v1/dev/inspect/models': {
      get: {
        tags: ['Developer Tools'],
        summary: 'Inspect models',
        responses: { 200: { description: 'OK' } },
      },
    },
    '/api/v1/dev/dev/system-info': {
      get: {
        tags: ['Developer UI Tools'],
        summary: 'System info',
        responses: { 200: { description: 'OK' } },
      },
    },
    '/api/v1/dev/dev/metrics': {
      get: {
        tags: ['Developer Metrics'],
        summary: 'Live metrics',
        responses: { 200: { description: 'OK' } },
      },
    },
    '/api/v1/dev/dev/apps-status': {
      get: {
        tags: ['Developer UI Tools'],
        summary: 'App status',
        responses: { 200: { description: 'OK' } },
      },
    },
    '/api/v1/dev/dev/errors': {
      get: {
        tags: ['Developer Core'],
        summary: 'Recent errors',
        responses: { 200: { description: 'OK' } },
      },
    },
  },
  components: { schemas: {} },
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    sessionStorage.setItem('aras_token', 'test-token')
    localStorage.setItem('aras_token', 'test-token')
    localStorage.setItem('org_id', '1')
    localStorage.setItem('template-builder:expo-url', 'http://127.0.0.1:8081')
  })

  await page.route('**/api/v1/**', route => {
    const path = new URL(route.request().url()).pathname
    if (path === '/api/v1/sidebar') {
      return route.fulfill(jsonEnvelope([
        { name: 'dev', label: 'Developer Tools', path: '/dev', type: 'framework', hide_from_sidebar: false, have_home: true },
      ]))
    }
    if (path === '/api/v1/app-menu/dev') {
      return route.fulfill(jsonEnvelope({
        app_name: 'dev',
        app_label: 'Developer Tools',
        have_home: true,
        menu: [],
        sub_apps: [],
      }))
    }
    if (path === '/api/v1/auth/me') return route.fulfill(jsonEnvelope(authMe))
    if (path === '/api/v1/admin/apps/capabilities') return route.fulfill(jsonEnvelope({ active_apps: ['dev'], optional_features: {} }))
    if (path === '/api/v1/config/organizations/1/vocabulary') return route.fulfill(jsonEnvelope({ vocabulary: { trx_in: 'Inflow', trx_out: 'Outflow', party: 'Party', pot: 'Point of Sale' } }))
    if (path === '/api/v1/settings/core') return route.fulfill(jsonEnvelope({
      general: {
        date_format: 'YYYY-MM-DD',
        number_format: '#,###.##',
        decimal_precision: '2',
        currency_symbol: 'USD',
        language_default: 'en',
      },
    }))
    if (path === '/api/v1/dev/info') return route.fulfill(jsonEnvelope(devInfo))
    if (path === '/api/v1/dev/stats') return route.fulfill(jsonEnvelope(devStats))
    if (path === '/api/v1/dev/dev/info') return route.fulfill(jsonEnvelope(devInfo))
    if (path === '/api/v1/dev/dev/metrics') return route.fulfill(jsonEnvelope(metrics))
    if (path === '/api/v1/dev/dev/system-info') return route.fulfill(jsonEnvelope(systemInfo))
    if (path === '/api/v1/dev/dev/apps-status') return route.fulfill(jsonEnvelope(appsStatus))
    if (path === '/api/v1/dev/dev/errors') return route.fulfill(jsonEnvelope([]))
    if (path === '/api/v1/dev/inspect/routes') return route.fulfill(jsonEnvelope(routes))
    if (path === '/api/v1/dev/inspect/models') return route.fulfill(jsonEnvelope([{ name: 'User', table: 'auth_users' }]))
    if (path === '/api/v1/dev/dev/style-overrides') return route.fulfill(jsonEnvelope([]))
    return route.fulfill(jsonEnvelope({}))
  })
  await page.route('**/openapi.json', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(openApi) }))
  await page.route('http://127.0.0.1:8081/**', route => route.abort())
})

test('DevTools renders core panels and routes', async ({ page }) => {
  await page.goto('/dev?tab=overview')

  await expect(page.getByRole('heading', { name: 'DevTools', exact: true })).toBeVisible()
  await expect(page.getByText('DevTools Health')).toBeVisible()
  await expect(page.getByText('/api/v1/dev/info')).toBeVisible()
  await expect(page.getByText('/api/v1/dev/dev/*')).toBeVisible()

  await page.getByRole('button', { name: 'System' }).click()
  await expect(page.getByRole('heading', { name: 'System' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Live Metrics' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Loaded Apps' })).toBeVisible()

  await page.getByRole('button', { name: 'Routes' }).click()
  await expect(page.getByText('Route Debugger', { exact: true }).first()).toBeVisible()
  await expect(page.getByRole('button', { name: /GET \/api\/v1\/dev\/info/ })).toBeVisible()

  await page.getByRole('button', { name: 'Test Lab' }).click()
  await expect(page.getByRole('heading', { name: 'Test Lab' })).toBeVisible()
  await expect(page.getByText('OpenAPI runner', { exact: true })).toBeVisible()
})

test('Test Lab loads the Dev Snapshot scenario and reports a pass', async ({ page }) => {
  await page.goto('/dev?tab=console')

  await expect(page.getByRole('heading', { name: 'Test Lab' })).toBeVisible()
  await page.getByRole('button', { name: 'Dev Snapshot' }).click()
  await page.getByRole('button', { name: 'Run Scenario' }).click()

  await expect(page.getByText('Scenario complete.')).toBeVisible()
  await expect(page.getByText('Final response: 200')).toBeVisible()
})

function jsonEnvelope(body) {
  return {
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data: body }),
  }
}

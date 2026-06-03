# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: devtools.spec.ts >> Test Lab loads the Dev Snapshot scenario and reports a pass
- Location: tests/devtools.spec.ts:214:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: 'Dev Snapshot' })

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - complementary [ref=e5]:
    - generic [ref=e6]:
      - generic [ref=e7]:
        - img [ref=e8]
        - generic [ref=e10]: Aras
      - generic [ref=e11]:
        - button "Hide Rail" [ref=e12]:
          - img [ref=e13]
        - button "Collapse" [ref=e14]:
          - img [ref=e15]
    - button "Developer Tools" [ref=e19]:
      - img [ref=e20]
      - generic [ref=e24]: Developer Tools
    - generic [ref=e26]:
      - button "Settings" [ref=e27]:
        - img [ref=e28]
        - generic [ref=e31]: Settings
      - button "Help" [ref=e32]:
        - img [ref=e33]
        - generic [ref=e36]: Help
      - generic [ref=e37]:
        - generic [ref=e39]: A
        - generic [ref=e40]:
          - generic [ref=e41]: Admin User
          - generic [ref=e42]: Administrator
  - generic [ref=e43]:
    - generic [ref=e44]:
      - generic [ref=e45]:
        - generic [ref=e46]: Developer Tools
        - generic [ref=e47]:
          - img [ref=e48]
          - generic [ref=e50]: SYSTEM / DEV
      - button "Find an item, command, or person… ⌘ K" [ref=e53]:
        - img [ref=e54]
        - generic [ref=e57]: Find an item, command, or person…
        - generic [ref=e58]:
          - generic [ref=e59]: ⌘
          - generic [ref=e60]: K
      - generic [ref=e61]:
        - generic [ref=e62]:
          - text: Live ·
          - generic [ref=e64]: live
        - img [ref=e66]
        - generic [ref=e71]:
          - img [ref=e72]
          - button "EN" [ref=e75]
          - button "ID" [ref=e76]
        - button "Open Template Studio for this page" [ref=e77]:
          - img [ref=e78]
        - button "Tweak layout" [ref=e82]:
          - img [ref=e83]
        - button "Notifications" [ref=e85]:
          - img [ref=e86]
        - button "Open account menu" [ref=e90] [cursor=pointer]:
          - generic [ref=e91]: A
    - main [ref=e93]:
      - generic [ref=e96]:
        - generic [ref=e97]:
          - generic [ref=e98]:
            - generic [ref=e99]:
              - generic [ref=e100]:
                - heading "DevTools" [level=1] [ref=e101]
                - generic [ref=e102]: Test Lab
              - paragraph [ref=e103]: Run API requests, scenarios, and reports
            - generic [ref=e104]:
              - generic [ref=e105]:
                - img
                - textbox "Find tool" [ref=e106]
              - button "Workbench" [ref=e107]:
                - img [ref=e108]
                - text: Workbench
              - button "Sync" [ref=e110]:
                - img [ref=e111]
                - text: Sync
          - generic [ref=e117]:
            - button "Overview" [ref=e118]
            - button "Workbench" [ref=e119]:
              - img [ref=e120]
              - text: Workbench
            - button "System" [ref=e122]:
              - img [ref=e123]
              - text: System
            - button "Schema" [ref=e126]:
              - img [ref=e127]
              - text: Schema
            - button "Timeline" [ref=e132]:
              - img [ref=e133]
              - text: Timeline
            - button "Routes" [ref=e135]:
              - img [ref=e136]
              - text: Routes
            - button "Models" [ref=e140]:
              - img [ref=e141]
              - text: Models
            - button "Cache" [ref=e151]:
              - img [ref=e152]
              - text: Cache
            - button "Commands" [ref=e155]:
              - img [ref=e156]
              - text: Commands
            - button "Test Lab" [ref=e158]:
              - img [ref=e159]
              - text: Test Lab
            - button "SQL Runner" [ref=e161]:
              - img [ref=e162]
              - text: SQL Runner
            - button "Access" [ref=e164]:
              - img [ref=e165]
              - text: Access
            - button "Handoff" [ref=e167]:
              - img [ref=e168]
              - text: Handoff
            - button "Mocks" [ref=e172]:
              - img [ref=e173]
              - text: Mocks
            - button "API Help" [ref=e176]:
              - img [ref=e177]
              - text: API Help
            - button "Scaffold" [ref=e181]:
              - img [ref=e182]
              - text: Scaffold
            - button "Logs" [ref=e186]:
              - img [ref=e187]
              - text: Logs
        - generic [ref=e190]:
          - generic [ref=e191]:
            - generic [ref=e192]:
              - img [ref=e193]
              - heading "DevTools Health" [level=2] [ref=e195]
              - generic [ref=e196]: Core developer surfaces are reachable.
            - generic [ref=e197]:
              - generic [ref=e198]:
                - generic [ref=e199]: Backend
                - generic [ref=e204]: /api/v1/dev/info
              - generic [ref=e205]:
                - generic [ref=e206]:
                  - img [ref=e207]
                  - text: App Tools
                - generic [ref=e211]: /api/v1/dev/dev/*
              - generic [ref=e212]:
                - generic [ref=e213]:
                  - img [ref=e214]
                  - text: OpenAPI
                - generic [ref=e220]: /openapi.json
              - generic [ref=e221]:
                - generic [ref=e222]:
                  - img [ref=e223]
                  - text: Expo
                - generic [ref=e227]: 127.0.0.1:8081
              - generic [ref=e228]:
                - generic [ref=e229]: Requests
                - generic [ref=e230]: "42"
              - generic [ref=e231]:
                - generic [ref=e232]: Errors
                - generic [ref=e233]: "0"
              - generic [ref=e234]:
                - generic [ref=e235]: p95
                - generic [ref=e236]: 20 ms
          - generic [ref=e237]:
            - textbox "Expo preview URL" [ref=e238]: http://127.0.0.1:8081
            - button "Check" [ref=e239]:
              - img [ref=e240]
              - text: Check
            - link "Swagger" [ref=e245] [cursor=pointer]:
              - /url: http://127.0.0.1:5173/docs
              - img [ref=e246]
              - text: Swagger
        - generic [ref=e250]:
          - generic [ref=e251]:
            - generic [ref=e252]:
              - generic [ref=e253]:
                - heading "Test Lab" [level=2] [ref=e254]
                - generic [ref=e255]: OpenAPI runner
                - generic [ref=e256]: run
              - paragraph [ref=e257]: Run endpoints, switch auth context, save repeatable cases, and replay failures with assertions.
            - generic [ref=e258]:
              - generic [ref=e259]:
                - button "Run" [ref=e260]
                - button "Explore" [ref=e261]
                - button "Debug" [ref=e262]
              - button "Refresh Spec" [ref=e263]:
                - img [ref=e264]
                - text: Refresh Spec
              - button "Copy cURL" [ref=e269]:
                - img [ref=e270]
                - text: Copy cURL
              - button "Run" [ref=e273]:
                - img [ref=e274]
                - text: Run
          - generic [ref=e276]:
            - complementary [ref=e277]:
              - generic [ref=e278]:
                - generic [ref=e279]:
                  - img [ref=e280]
                  - text: Request Context
                - generic [ref=e282]:
                  - generic [ref=e283]:
                    - generic [ref=e284]: Base URL
                    - textbox "http://127.0.0.1:5173" [ref=e285]: http://127.0.0.1:5173/api/v1
                  - generic [ref=e286]:
                    - generic [ref=e287]: Auth
                    - generic [ref=e288]:
                      - button "Current" [ref=e289]
                      - button "Anon" [ref=e290]
                      - button "Bearer" [ref=e291]
                  - generic [ref=e292]:
                    - generic [ref=e293]: Custom Headers
                    - 'textbox "{\"X-Debug\":\"1\"}" [ref=e294]': "{}"
                  - generic [ref=e295]:
                    - generic [ref=e296]: Jump to path
                    - generic [ref=e297]:
                      - textbox "/api/v1/dev/info" [ref=e298]
                      - button "Open" [ref=e299]:
                        - img [ref=e300]
                        - text: Open
              - generic [ref=e302]:
                - generic [ref=e303]:
                  - generic [ref=e304]:
                    - img [ref=e305]
                    - text: Endpoints
                  - generic [ref=e308]: "8"
                - generic [ref=e309]:
                  - img [ref=e310]
                  - textbox "Filter path, tag, summary" [ref=e313]
                - generic [ref=e314]:
                  - generic [ref=e315]:
                    - generic [ref=e316]: Developer Core
                    - button "get /api/v1/dev/dev/errors Recent errors" [ref=e318]:
                      - generic [ref=e319]:
                        - generic [ref=e320]: get
                        - generic [ref=e321]:
                          - code [ref=e322]: /api/v1/dev/dev/errors
                          - generic [ref=e323]: Recent errors
                  - generic [ref=e324]:
                    - generic [ref=e325]: Developer Metrics
                    - button "get /api/v1/dev/dev/metrics Live metrics" [ref=e327]:
                      - generic [ref=e328]:
                        - generic [ref=e329]: get
                        - generic [ref=e330]:
                          - code [ref=e331]: /api/v1/dev/dev/metrics
                          - generic [ref=e332]: Live metrics
                  - generic [ref=e333]:
                    - generic [ref=e334]: Developer Tools
                    - generic [ref=e335]:
                      - button "get /api/v1/dev/info Framework info" [ref=e336]:
                        - generic [ref=e337]:
                          - generic [ref=e338]: get
                          - generic [ref=e339]:
                            - code [ref=e340]: /api/v1/dev/info
                            - generic [ref=e341]: Framework info
                      - button "get /api/v1/dev/stats Registry stats" [ref=e342]:
                        - generic [ref=e343]:
                          - generic [ref=e344]: get
                          - generic [ref=e345]:
                            - code [ref=e346]: /api/v1/dev/stats
                            - generic [ref=e347]: Registry stats
                      - button "get /api/v1/dev/inspect/routes Inspect routes" [ref=e348]:
                        - generic [ref=e349]:
                          - generic [ref=e350]: get
                          - generic [ref=e351]:
                            - code [ref=e352]: /api/v1/dev/inspect/routes
                            - generic [ref=e353]: Inspect routes
                      - button "get /api/v1/dev/inspect/models Inspect models" [ref=e354]:
                        - generic [ref=e355]:
                          - generic [ref=e356]: get
                          - generic [ref=e357]:
                            - code [ref=e358]: /api/v1/dev/inspect/models
                            - generic [ref=e359]: Inspect models
                  - generic [ref=e360]:
                    - generic [ref=e361]: Developer UI Tools
                    - generic [ref=e362]:
                      - button "get /api/v1/dev/dev/system-info System info" [ref=e363]:
                        - generic [ref=e364]:
                          - generic [ref=e365]: get
                          - generic [ref=e366]:
                            - code [ref=e367]: /api/v1/dev/dev/system-info
                            - generic [ref=e368]: System info
                      - button "get /api/v1/dev/dev/apps-status App status" [ref=e369]:
                        - generic [ref=e370]:
                          - generic [ref=e371]: get
                          - generic [ref=e372]:
                            - code [ref=e373]: /api/v1/dev/dev/apps-status
                            - generic [ref=e374]: App status
            - main [ref=e375]:
              - generic [ref=e377]:
                - generic [ref=e378]:
                  - generic [ref=e379]:
                    - generic [ref=e380]:
                      - generic [ref=e381]: get
                      - code [ref=e382]: /api/v1/dev/info
                    - paragraph [ref=e383]: Framework info
                  - generic [ref=e384]:
                    - button "Current Path" [ref=e385]:
                      - img [ref=e386]
                      - text: Current Path
                    - button "Copy cURL" [ref=e389]:
                      - img [ref=e390]
                      - text: Copy cURL
                    - button "Run Request" [ref=e393]:
                      - img [ref=e394]
                      - text: Run Request
                - generic [ref=e396]:
                  - heading "Assertions" [level=4] [ref=e397]
                  - generic [ref=e398]:
                    - generic [ref=e399]:
                      - generic [ref=e400]:
                        - text: Expected Status
                        - generic [ref=e401]: integer
                      - spinbutton "Expected Status integer" [ref=e402]: "200"
                    - generic [ref=e403]:
                      - generic [ref=e404]:
                        - text: Response Contains
                        - generic [ref=e405]: string
                      - textbox "Response Contains string" [ref=e406]
                    - generic [ref=e407]:
                      - generic [ref=e408]:
                        - text: Max Time (ms)
                        - generic [ref=e409]: integer
                      - spinbutton "Max Time (ms) integer" [ref=e410]
              - generic [ref=e412]:
                - generic [ref=e414]:
                  - img [ref=e415]
                  - text: Latest Response
                - generic [ref=e418]: Run the request to inspect the response here.
```

# Test source

```ts
  118 |         summary: 'Live metrics',
  119 |         responses: { 200: { description: 'OK' } },
  120 |       },
  121 |     },
  122 |     '/api/v1/dev/dev/apps-status': {
  123 |       get: {
  124 |         tags: ['Developer UI Tools'],
  125 |         summary: 'App status',
  126 |         responses: { 200: { description: 'OK' } },
  127 |       },
  128 |     },
  129 |     '/api/v1/dev/dev/errors': {
  130 |       get: {
  131 |         tags: ['Developer Core'],
  132 |         summary: 'Recent errors',
  133 |         responses: { 200: { description: 'OK' } },
  134 |       },
  135 |     },
  136 |   },
  137 |   components: { schemas: {} },
  138 | }
  139 | 
  140 | test.beforeEach(async ({ page }) => {
  141 |   await page.addInitScript(() => {
  142 |     sessionStorage.setItem('aras_token', 'test-token')
  143 |     localStorage.setItem('aras_token', 'test-token')
  144 |     localStorage.setItem('org_id', '1')
  145 |     localStorage.setItem('template-builder:expo-url', 'http://127.0.0.1:8081')
  146 |   })
  147 | 
  148 |   await page.route('**/api/v1/**', route => {
  149 |     const path = new URL(route.request().url()).pathname
  150 |     if (path === '/api/v1/sidebar') {
  151 |       return route.fulfill(jsonEnvelope([
  152 |         { name: 'dev', label: 'Developer Tools', path: '/dev', type: 'framework', hide_from_sidebar: false, have_home: true },
  153 |       ]))
  154 |     }
  155 |     if (path === '/api/v1/app-menu/dev') {
  156 |       return route.fulfill(jsonEnvelope({
  157 |         app_name: 'dev',
  158 |         app_label: 'Developer Tools',
  159 |         have_home: true,
  160 |         menu: [],
  161 |         sub_apps: [],
  162 |       }))
  163 |     }
  164 |     if (path === '/api/v1/auth/me') return route.fulfill(jsonEnvelope(authMe))
  165 |     if (path === '/api/v1/admin/apps/capabilities') return route.fulfill(jsonEnvelope({ active_apps: ['dev'], optional_features: {} }))
  166 |     if (path === '/api/v1/config/organizations/1/vocabulary') return route.fulfill(jsonEnvelope({ vocabulary: { trx_in: 'Inflow', trx_out: 'Outflow', party: 'Party', pot: 'Point of Sale' } }))
  167 |     if (path === '/api/v1/settings/core') return route.fulfill(jsonEnvelope({
  168 |       general: {
  169 |         date_format: 'YYYY-MM-DD',
  170 |         number_format: '#,###.##',
  171 |         decimal_precision: '2',
  172 |         currency_symbol: 'USD',
  173 |         language_default: 'en',
  174 |       },
  175 |     }))
  176 |     if (path === '/api/v1/dev/info') return route.fulfill(jsonEnvelope(devInfo))
  177 |     if (path === '/api/v1/dev/stats') return route.fulfill(jsonEnvelope(devStats))
  178 |     if (path === '/api/v1/dev/dev/info') return route.fulfill(jsonEnvelope(devInfo))
  179 |     if (path === '/api/v1/dev/dev/metrics') return route.fulfill(jsonEnvelope(metrics))
  180 |     if (path === '/api/v1/dev/dev/system-info') return route.fulfill(jsonEnvelope(systemInfo))
  181 |     if (path === '/api/v1/dev/dev/apps-status') return route.fulfill(jsonEnvelope(appsStatus))
  182 |     if (path === '/api/v1/dev/dev/errors') return route.fulfill(jsonEnvelope([]))
  183 |     if (path === '/api/v1/dev/inspect/routes') return route.fulfill(jsonEnvelope(routes))
  184 |     if (path === '/api/v1/dev/inspect/models') return route.fulfill(jsonEnvelope([{ name: 'User', table: 'auth_users' }]))
  185 |     if (path === '/api/v1/dev/dev/style-overrides') return route.fulfill(jsonEnvelope([]))
  186 |     return route.fulfill(jsonEnvelope({}))
  187 |   })
  188 |   await page.route('**/openapi.json', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(openApi) }))
  189 |   await page.route('http://127.0.0.1:8081/**', route => route.abort())
  190 | })
  191 | 
  192 | test('DevTools renders core panels and routes', async ({ page }) => {
  193 |   await page.goto('/dev?tab=overview')
  194 | 
  195 |   await expect(page.getByRole('heading', { name: 'DevTools', exact: true })).toBeVisible()
  196 |   await expect(page.getByText('DevTools Health')).toBeVisible()
  197 |   await expect(page.getByText('/api/v1/dev/info')).toBeVisible()
  198 |   await expect(page.getByText('/api/v1/dev/dev/*')).toBeVisible()
  199 | 
  200 |   await page.getByRole('button', { name: 'System' }).click()
  201 |   await expect(page.getByRole('heading', { name: 'System' })).toBeVisible()
  202 |   await expect(page.getByRole('heading', { name: 'Live Metrics' })).toBeVisible()
  203 |   await expect(page.getByRole('heading', { name: 'Loaded Apps' })).toBeVisible()
  204 | 
  205 |   await page.getByRole('button', { name: 'Routes' }).click()
  206 |   await expect(page.getByText('Route Debugger', { exact: true }).first()).toBeVisible()
  207 |   await expect(page.getByRole('button', { name: /GET \/api\/v1\/dev\/info/ })).toBeVisible()
  208 | 
  209 |   await page.getByRole('button', { name: 'Test Lab' }).click()
  210 |   await expect(page.getByRole('heading', { name: 'Test Lab' })).toBeVisible()
  211 |   await expect(page.getByText('OpenAPI runner', { exact: true })).toBeVisible()
  212 | })
  213 | 
  214 | test('Test Lab loads the Dev Snapshot scenario and reports a pass', async ({ page }) => {
  215 |   await page.goto('/dev?tab=console')
  216 | 
  217 |   await expect(page.getByRole('heading', { name: 'Test Lab' })).toBeVisible()
> 218 |   await page.getByRole('button', { name: 'Dev Snapshot' }).click()
      |                                                            ^ Error: locator.click: Test timeout of 30000ms exceeded.
  219 |   await page.getByRole('button', { name: 'Run Scenario' }).click()
  220 | 
  221 |   await expect(page.getByText('Scenario complete.')).toBeVisible()
  222 |   await expect(page.getByText('Final response: 200')).toBeVisible()
  223 | })
  224 | 
  225 | function jsonEnvelope(body) {
  226 |   return {
  227 |     status: 200,
  228 |     contentType: 'application/json',
  229 |     body: JSON.stringify({ success: true, data: body }),
  230 |   }
  231 | }
  232 | 
```
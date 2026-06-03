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
        - button "Open menu" [ref=e46]:
          - img [ref=e47]
        - generic [ref=e48]: Developer Tools
        - generic [ref=e49]:
          - img [ref=e50]
          - generic [ref=e52]: SYSTEM / DEV
      - button "Find an item, command, or person…" [ref=e53]:
        - img [ref=e54]
        - generic: Find an item, command, or person…
      - generic [ref=e57]:
        - button "Open Template Studio for this page" [ref=e58]:
          - img [ref=e59]
        - button "Tweak layout" [ref=e63]:
          - img [ref=e64]
        - button "Notifications" [ref=e66]:
          - img [ref=e67]
        - button "Open account menu" [ref=e71] [cursor=pointer]:
          - generic [ref=e72]: A
    - main [ref=e74]:
      - generic [ref=e77]:
        - generic [ref=e78]:
          - generic [ref=e79]:
            - generic [ref=e80]:
              - generic [ref=e81]:
                - heading "DevTools" [level=1] [ref=e82]
                - generic [ref=e83]: Test Lab
              - paragraph [ref=e84]: Run API requests, scenarios, and reports
            - generic [ref=e85]:
              - generic [ref=e86]:
                - img
                - textbox "Find tool" [ref=e87]
              - button "Workbench" [ref=e88]:
                - img [ref=e89]
                - text: Workbench
              - button "Sync" [ref=e91]:
                - img [ref=e92]
                - text: Sync
          - generic [ref=e98]:
            - button "Overview" [ref=e99]
            - button "Workbench" [ref=e100]:
              - img [ref=e101]
              - text: Workbench
            - button "System" [ref=e103]:
              - img [ref=e104]
              - text: System
            - button "Schema" [ref=e107]:
              - img [ref=e108]
              - text: Schema
            - button "Timeline" [ref=e113]:
              - img [ref=e114]
              - text: Timeline
            - button "Routes" [ref=e116]:
              - img [ref=e117]
              - text: Routes
            - button "Models" [ref=e121]:
              - img [ref=e122]
              - text: Models
            - button "Cache" [ref=e132]:
              - img [ref=e133]
              - text: Cache
            - button "Commands" [ref=e136]:
              - img [ref=e137]
              - text: Commands
            - button "Test Lab" [ref=e139]:
              - img [ref=e140]
              - text: Test Lab
            - button "SQL Runner" [ref=e142]:
              - img [ref=e143]
              - text: SQL Runner
            - button "Access" [ref=e145]:
              - img [ref=e146]
              - text: Access
            - button "Handoff" [ref=e148]:
              - img [ref=e149]
              - text: Handoff
            - button "Mocks" [ref=e153]:
              - img [ref=e154]
              - text: Mocks
            - button "API Help" [ref=e157]:
              - img [ref=e158]
              - text: API Help
            - button "Scaffold" [ref=e162]:
              - img [ref=e163]
              - text: Scaffold
            - button "Logs" [ref=e167]:
              - img [ref=e168]
              - text: Logs
        - generic [ref=e171]:
          - generic [ref=e172]:
            - generic [ref=e173]:
              - img [ref=e174]
              - heading "DevTools Health" [level=2] [ref=e176]
              - generic [ref=e177]: Core developer surfaces are reachable.
            - generic [ref=e178]:
              - generic [ref=e179]:
                - generic [ref=e180]:
                  - img [ref=e181]
                  - text: Backend
                - generic [ref=e186]: /api/v1/dev/info
              - generic [ref=e187]:
                - generic [ref=e188]:
                  - img [ref=e189]
                  - text: App Tools
                - generic [ref=e193]: /api/v1/dev/dev/*
              - generic [ref=e194]:
                - generic [ref=e195]:
                  - img [ref=e196]
                  - text: OpenAPI
                - generic [ref=e202]: /openapi.json
              - generic [ref=e203]:
                - generic [ref=e204]:
                  - img [ref=e205]
                  - text: Expo
                - generic [ref=e209]: 127.0.0.1:8081
              - generic [ref=e210]:
                - generic [ref=e211]: Requests
                - generic [ref=e212]: "42"
              - generic [ref=e213]:
                - generic [ref=e214]: Errors
                - generic [ref=e215]: "0"
              - generic [ref=e216]:
                - generic [ref=e217]: p95
                - generic [ref=e218]: 20 ms
          - generic [ref=e219]:
            - textbox "Expo preview URL" [ref=e220]: http://127.0.0.1:8081
            - button "Check" [ref=e221]:
              - img [ref=e222]
              - text: Check
            - link "Swagger" [ref=e227] [cursor=pointer]:
              - /url: http://127.0.0.1:5173/docs
              - img [ref=e228]
              - text: Swagger
        - generic [ref=e232]:
          - generic [ref=e233]:
            - generic [ref=e234]:
              - generic [ref=e235]:
                - heading "Test Lab" [level=2] [ref=e236]
                - generic [ref=e237]: OpenAPI runner
                - generic [ref=e238]: run
              - paragraph [ref=e239]: Run endpoints, switch auth context, save repeatable cases, and replay failures with assertions.
            - generic [ref=e240]:
              - generic [ref=e241]:
                - button "Run" [ref=e242]
                - button "Explore" [ref=e243]
                - button "Debug" [ref=e244]
              - button "Refresh Spec" [ref=e245]:
                - img [ref=e246]
                - text: Refresh Spec
              - button "Copy cURL" [ref=e251]:
                - img [ref=e252]
                - text: Copy cURL
              - button "Run" [ref=e255]:
                - img [ref=e256]
                - text: Run
          - generic [ref=e258]:
            - complementary [ref=e259]:
              - generic [ref=e260]:
                - generic [ref=e261]:
                  - img [ref=e262]
                  - text: Request Context
                - generic [ref=e264]:
                  - generic [ref=e265]:
                    - generic [ref=e266]: Base URL
                    - textbox "http://127.0.0.1:5173" [ref=e267]: http://127.0.0.1:5173/api/v1
                  - generic [ref=e268]:
                    - generic [ref=e269]: Auth
                    - generic [ref=e270]:
                      - button "Current" [ref=e271]
                      - button "Anon" [ref=e272]
                      - button "Bearer" [ref=e273]
                  - generic [ref=e274]:
                    - generic [ref=e275]: Custom Headers
                    - 'textbox "{\"X-Debug\":\"1\"}" [ref=e276]': "{}"
                  - generic [ref=e277]:
                    - generic [ref=e278]: Jump to path
                    - generic [ref=e279]:
                      - textbox "/api/v1/dev/info" [ref=e280]
                      - button "Open" [ref=e281]:
                        - img [ref=e282]
                        - text: Open
              - generic [ref=e284]:
                - generic [ref=e285]:
                  - generic [ref=e286]:
                    - img [ref=e287]
                    - text: Endpoints
                  - generic [ref=e290]: "8"
                - generic [ref=e291]:
                  - img [ref=e292]
                  - textbox "Filter path, tag, summary" [ref=e295]
                - generic [ref=e296]:
                  - generic [ref=e297]:
                    - generic [ref=e298]: Developer Core
                    - button "get /api/v1/dev/dev/errors Recent errors" [ref=e300]:
                      - generic [ref=e301]:
                        - generic [ref=e302]: get
                        - generic [ref=e303]:
                          - code [ref=e304]: /api/v1/dev/dev/errors
                          - generic [ref=e305]: Recent errors
                  - generic [ref=e306]:
                    - generic [ref=e307]: Developer Metrics
                    - button "get /api/v1/dev/dev/metrics Live metrics" [ref=e309]:
                      - generic [ref=e310]:
                        - generic [ref=e311]: get
                        - generic [ref=e312]:
                          - code [ref=e313]: /api/v1/dev/dev/metrics
                          - generic [ref=e314]: Live metrics
                  - generic [ref=e315]:
                    - generic [ref=e316]: Developer Tools
                    - generic [ref=e317]:
                      - button "get /api/v1/dev/info Framework info" [ref=e318]:
                        - generic [ref=e319]:
                          - generic [ref=e320]: get
                          - generic [ref=e321]:
                            - code [ref=e322]: /api/v1/dev/info
                            - generic [ref=e323]: Framework info
                      - button "get /api/v1/dev/stats Registry stats" [ref=e324]:
                        - generic [ref=e325]:
                          - generic [ref=e326]: get
                          - generic [ref=e327]:
                            - code [ref=e328]: /api/v1/dev/stats
                            - generic [ref=e329]: Registry stats
                      - button "get /api/v1/dev/inspect/routes Inspect routes" [ref=e330]:
                        - generic [ref=e331]:
                          - generic [ref=e332]: get
                          - generic [ref=e333]:
                            - code [ref=e334]: /api/v1/dev/inspect/routes
                            - generic [ref=e335]: Inspect routes
                      - button "get /api/v1/dev/inspect/models Inspect models" [ref=e336]:
                        - generic [ref=e337]:
                          - generic [ref=e338]: get
                          - generic [ref=e339]:
                            - code [ref=e340]: /api/v1/dev/inspect/models
                            - generic [ref=e341]: Inspect models
                  - generic [ref=e342]:
                    - generic [ref=e343]: Developer UI Tools
                    - generic [ref=e344]:
                      - button "get /api/v1/dev/dev/system-info System info" [ref=e345]:
                        - generic [ref=e346]:
                          - generic [ref=e347]: get
                          - generic [ref=e348]:
                            - code [ref=e349]: /api/v1/dev/dev/system-info
                            - generic [ref=e350]: System info
                      - button "get /api/v1/dev/dev/apps-status App status" [ref=e351]:
                        - generic [ref=e352]:
                          - generic [ref=e353]: get
                          - generic [ref=e354]:
                            - code [ref=e355]: /api/v1/dev/dev/apps-status
                            - generic [ref=e356]: App status
            - main [ref=e357]:
              - generic [ref=e359]:
                - generic [ref=e360]:
                  - generic [ref=e361]:
                    - generic [ref=e362]:
                      - generic [ref=e363]: get
                      - code [ref=e364]: /api/v1/dev/info
                    - paragraph [ref=e365]: Framework info
                  - generic [ref=e366]:
                    - button "Current Path" [ref=e367]:
                      - img [ref=e368]
                      - text: Current Path
                    - button "Copy cURL" [ref=e371]:
                      - img [ref=e372]
                      - text: Copy cURL
                    - button "Run Request" [ref=e375]:
                      - img [ref=e376]
                      - text: Run Request
                - generic [ref=e378]:
                  - heading "Assertions" [level=4] [ref=e379]
                  - generic [ref=e380]:
                    - generic [ref=e381]:
                      - generic [ref=e382]:
                        - text: Expected Status
                        - generic [ref=e383]: integer
                      - spinbutton "Expected Status integer" [ref=e384]: "200"
                    - generic [ref=e385]:
                      - generic [ref=e386]:
                        - text: Response Contains
                        - generic [ref=e387]: string
                      - textbox "Response Contains string" [ref=e388]
                    - generic [ref=e389]:
                      - generic [ref=e390]:
                        - text: Max Time (ms)
                        - generic [ref=e391]: integer
                      - spinbutton "Max Time (ms) integer" [ref=e392]
              - generic [ref=e394]:
                - generic [ref=e396]:
                  - img [ref=e397]
                  - text: Latest Response
                - generic [ref=e400]: Run the request to inspect the response here.
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
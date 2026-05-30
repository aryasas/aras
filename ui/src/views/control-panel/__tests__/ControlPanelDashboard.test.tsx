// @ts-nocheck
import { readFileSync } from 'node:fs'

const readControlPanelView = (name: string) => readFileSync(new URL(`../${name}.tsx`, import.meta.url), 'utf8')
const readApp = () => readFileSync(new URL('../../../App.tsx', import.meta.url), 'utf8')

describe('Control Panel routing and views', () => {
  it('loads the tenant list from the control-panel API and navigates to tenant detail', () => {
    const source = readControlPanelView('ControlPanelDashboard')

    expect(source).toContain("api.get('/saas/control-panel/tenants')")
    expect(source).toContain('/control-panel/tenants/${tenant.tenant_id || tenant.id}')
    expect(source).toContain('Control Panel')
  })

  it('renders the licenses panel and calls operator license endpoints', () => {
    const source = readControlPanelView('LicensesPanel')

    expect(source).toContain("api.get('/saas/control-panel/licenses')")
    expect(source).toContain("api.post('/saas/control-panel/licenses/issue'")
    expect(source).toContain('/saas/control-panel/licenses/${tenantId}/renew')
    expect(source).toContain('/saas/control-panel/licenses/${tenantId}/revoke')
  })

  it('gates control-panel and tenant license routes by ARAS_ROLE', () => {
    const source = readApp()

    expect(source).toContain("getArasRole() !== 'control-panel'")
    expect(source).toContain("getArasRole() === 'control-panel'")
    expect(source).toContain('path="control-panel/licenses"')
    expect(source).toContain('path="admin/license"')
  })
})

import { useEffect, useState, type CSSProperties } from 'react'
import { useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../lib/api'
import type { SidebarApp } from './types'
import { Sidebar } from './components/Sidebar'
import { Header } from './components/Header'
import { Building2 } from 'lucide-react'
import { useAras } from '../aras-core/hooks/useAras'
import { useUIStore } from '../store/uiStore'
import { SidebarBrand } from './components/SidebarBrand'
import { PageHeader } from '../components/PageHeader'

export default function MainLayout() {
  const [sidebarData, setSidebarData] = useState<SidebarApp[]>([])
  const { organizations, activeOrgId, setActiveOrg, logout } = useAuthStore()
  const location = useLocation()
  const activeOrganization = organizations.find((organization) => organization.id === activeOrgId)
  const { notify } = useAras()
  const { closePanel, themeMode, cornerMode, density, accentColor, fontScale } = useUIStore()

  const themeTokens = {
    light: {
      bg: '#ffffff',
      panel: '#ffffff',
      panelSoft: '#ffffff',
      tableHead: '#f4f4f4',
      border: '#e8e8e8',
      borderStrong: '#d8d8d8',
      text: '#222226',
      muted: '#68686d',
      button: accentColor,
    },
    normal: {
      bg: '#f3f3f3',
      panel: '#ffffff',
      panelSoft: '#f8f8f8',
      tableHead: '#e6e6e6',
      border: '#e2e2e2',
      borderStrong: '#d2d2d2',
      text: '#222226',
      muted: '#68686d',
      button: '#111111',
    },
    dark: {
      bg: '#020617',
      panel: '#0f172a',
      panelSoft: '#111827',
      tableHead: '#1f2937',
      border: '#1e293b',
      borderStrong: '#334155',
      text: '#f8fafc',
      muted: '#cbd5e1',
      button: accentColor,
    },
  }[themeMode]

  const layoutStyle = {
    '--aras-accent': accentColor,
    '--aras-accent-strong': accentColor === '#ffffff' ? '#e5e7eb' : accentColor,
    '--aras-button': themeTokens.button,
    '--aras-button-text': themeTokens.button === '#ffffff' ? '#111111' : '#ffffff',
    '--aras-radius': cornerMode === 'square' ? '0px' : '5px',
    '--aras-density': density === 'compact' ? '0.82' : density === 'comfy' ? '1.16' : '1',
    '--aras-font-scale': String(fontScale / 100),
    '--aras-bg-main': themeTokens.bg,
    '--aras-panel': themeTokens.panel,
    '--aras-panel-soft': themeTokens.panelSoft,
    '--aras-table-head': themeTokens.tableHead,
    '--aras-border': themeTokens.border,
    '--aras-border-strong': themeTokens.borderStrong,
    '--aras-text': themeTokens.text,
    '--aras-muted': themeTokens.muted,
  } as CSSProperties

  useEffect(() => {
    closePanel()
  }, [location.pathname])

  useEffect(() => {
    if (activeOrgId === null && organizations.length > 0) {
      setActiveOrg(organizations[0].id)
    }
  }, [activeOrgId, organizations, setActiveOrg])

  useEffect(() => {
    const fetchSidebar = async () => {
      try {
        const res = await api.get('/sidebar')
        setSidebarData(res.data)
      } catch (err: any) {
        notify(err.message || 'Failed to fetch sidebar', 'error')
      }
    }
    fetchSidebar()
  }, [notify])

  return (
    <div className="grid h-screen grid-cols-[68px_minmax(0,1fr)] grid-rows-[64px_minmax(0,1fr)] bg-[var(--aras-bg-main)] text-[var(--aras-text)] font-sans max-sm:block max-sm:min-h-screen max-sm:overflow-auto" style={layoutStyle}>
      <SidebarBrand />
      <Sidebar
        sidebarData={sidebarData}
        currentPath={location.pathname}
        onLogout={logout}
      />

      <main className="col-start-2 row-span-2 row-start-1 flex min-w-0 flex-col overflow-hidden max-sm:block max-sm:overflow-visible">
        <Header>
          {organizations.length > 1 && (
            <div className="z-50">
              <label className="sr-only" htmlFor="organization-selector">Organization</label>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--aras-muted)] pointer-events-none" size={16} />
                  <select
                    id="organization-selector"
                    value={activeOrgId ?? ''}
                    onChange={(event) => setActiveOrg(Number(event.target.value))}
                    className="h-16 min-w-[300px] max-w-[340px] appearance-none border-0 border-l border-r border-[var(--aras-border)] bg-[var(--aras-panel-soft)] pl-12 pr-10 text-base font-semibold text-[var(--aras-text)] outline-none transition-colors hover:bg-[var(--aras-panel)] focus:border-[var(--aras-accent)] focus:ring-2 focus:ring-[color:var(--aras-accent)]/10 max-sm:h-12 max-sm:min-w-52"
                  >
                    <option value="-1">All</option>
                    {organizations.map((organization) => (
                      <option key={organization.id} value={organization.id}>{organization.name}</option>
                    ))}
                  </select>
                </div>
                {(activeOrgId === -1 || activeOrganization?.is_group) && (
                  <span className="text-xs font-semibold px-2 py-1 rounded-[var(--aras-radius)]" style={{ color: 'var(--aras-accent)', backgroundColor: 'color-mix(in srgb, var(--aras-accent) 10%, transparent)' }}>
                    {activeOrgId === -1 ? 'All Orgs' : 'Consolidated'}
                  </span>
                )}
              </div>
              <span className="sr-only">{activeOrganization?.name}</span>
            </div>
          )}
        </Header>
        {/* Content Area */}
        <div className="flex-1 overflow-auto bg-[var(--aras-bg-main)] px-8 py-7 max-sm:min-h-screen max-sm:overflow-visible max-sm:p-4">
          <div className="mx-auto max-w-none">
            <PageHeader />
            <Outlet context={{ sidebarData }} />
          </div>
        </div>
      </main>
    </div>
  )
}

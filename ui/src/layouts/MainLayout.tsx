// claude-opus-4-7
// ARC shell: full-bleed bg + dot-grid, ARC sidebar on the left, topbar, content frame.
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
import Combobox from '../aras-core/components/Combobox'
import { PageHeader } from '../components/PageHeader'

export default function MainLayout() {
  const [sidebarData, setSidebarData] = useState<SidebarApp[]>([])
  const { organizations, activeOrgId, setActiveOrg, logout } = useAuthStore()
  const location = useLocation()
  const activeOrganization = organizations.find((organization) => organization.id === activeOrgId)
  const { notify } = useAras()
  const { closePanel, themeMode, cornerMode, density, fontScale, accentColor } = useUIStore()

  const layoutStyle = {
    '--accent': accentColor,
    '--aras-accent': accentColor,
    '--aras-accent-strong': `color-mix(in srgb, ${accentColor}, black 14%)`,
    '--aras-accent-glow': `color-mix(in srgb, ${accentColor}, transparent 78%)`,
    '--aras-radius': cornerMode === 'square' ? '0px' : '8px',
    '--aras-radius-lg': cornerMode === 'square' ? '0px' : '14px',
    '--aras-density': density === 'compact' ? 0.85 : density === 'comfy' ? 1.1 : '1',
    '--aras-font-scale': String(fontScale / 100),
  } as CSSProperties

  useEffect(() => {
    const root = document.documentElement
    Object.entries(layoutStyle).forEach(([key, value]) => {
      root.style.setProperty(key, String(value))
    })
    if (themeMode === 'dark') {
      root.classList.add('dark')
      root.setAttribute('data-theme', 'dark')
    } else {
      root.classList.remove('dark')
      root.setAttribute('data-theme', 'light')
    }
  }, [layoutStyle, themeMode])

  useEffect(() => { closePanel() }, [location.pathname])

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
    <div className="arc arc-bg arc-dotgrid h-screen w-full overflow-hidden flex font-sans antialiased p-3 gap-3" style={layoutStyle}>
      <Sidebar
        sidebarData={sidebarData}
        currentPath={location.pathname}
        onLogout={logout}
      />

      <div id="content-wrapper"
           className="flex flex-col flex-1 min-w-0 h-full overflow-hidden arc-card relative z-10">
        <Header>
          <div className="z-50 flex items-center gap-2 max-sm:hidden">
            <Building2 size={13} className="text-[var(--text-3)]" />
            {organizations.length > 1 ? (
              <div className="min-w-[180px]">
                <Combobox
                  options={[
                    { label: 'All Organizations', value: -1 },
                    ...organizations.map((org) => ({ label: org.name, value: org.id })),
                  ]}
                  value={activeOrgId ?? -1}
                  onChange={(val) => setActiveOrg(Number(val))}
                  placeholder="Select Organization"
                />
              </div>
            ) : (
              <span className="arc-id"><b>{activeOrganization?.name || 'org'}</b></span>
            )}
          </div>
        </Header>

        <main id="main-content" className="flex-1 overflow-y-auto min-w-0 relative flex flex-col arc-scroll">
          <div className="px-5 sm:px-7 lg:px-10 py-[calc(20px*var(--app-density))] flex-1 flex flex-col gap-[calc(24px*var(--app-density))]">
            <div className="pt-1">
              <PageHeader />
            </div>
            <div className="flex-1 max-sm:overflow-visible relative">
              <Outlet context={{ sidebarData }} />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

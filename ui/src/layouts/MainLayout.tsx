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
import { HorizontalAppNav } from './components/HorizontalAppNav'
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
    '--aras-accent': accentColor,
    '--aras-accent-strong': `color-mix(in srgb, ${accentColor}, black 15%)`,
    '--aras-accent-glow': `color-mix(in srgb, ${accentColor}, transparent 85%)`,
    '--aras-radius': cornerMode === 'square' ? '0px' : '12px',
    '--aras-radius-lg': cornerMode === 'square' ? '0px' : '24px',
    '--aras-density': density === 'compact' ? 0.62 : density === 'comfy' ? 1.16 : '1',
    '--aras-font-scale': String(fontScale / 100),
  } as CSSProperties

  useEffect(() => {
    const root = document.documentElement
    Object.entries(layoutStyle).forEach(([key, value]) => {
      root.style.setProperty(key, String(value))
    })
    
    // Manage dark mode class on root based on themeMode
    if (themeMode === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [layoutStyle, themeMode])

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
    <div className="h-screen w-full overflow-hidden flex bg-[var(--app-bg-main)] text-[var(--app-text)] font-sans antialiased transition-colors p-4 gap-4" style={layoutStyle}>
        <Sidebar
          sidebarData={sidebarData}
          currentPath={location.pathname}
          onLogout={logout}
        />

        <div id="content-wrapper" className="flex flex-col flex-1 min-w-0 h-full overflow-hidden bg-[var(--app-panel)] relative z-10 rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-sm">
          <Header>
            <div className="z-50 flex items-center gap-3 px-4 max-sm:hidden">
              <div className="flex items-center gap-2">
                <Building2 size={16} className="text-[var(--app-muted)]" />
                {organizations.length > 1 ? (
                  <div className="min-w-[200px]">
                    <Combobox
                      options={[
                        { label: 'All Organizations', value: -1 },
                        ...organizations.map((org) => ({ label: org.name, value: org.id }))
                      ]}
                      value={activeOrgId ?? -1}
                      onChange={(val) => setActiveOrg(Number(val))}
                      placeholder="Select Organization"
                    />
                  </div>
                ) : (
                  <span className="text-sm font-bold text-[var(--app-muted)] uppercase tracking-wider">
                    {activeOrganization?.name || 'Loading...'}
                  </span>
                )}
              </div>
            </div>
          </Header>

          <main id="main-content" className="flex-1 overflow-y-auto min-w-0 relative flex flex-col">
            <div className="px-4 sm:px-8 lg:px-12 py-[calc(24px*var(--app-density))] flex-1 flex flex-col gap-[calc(32px*var(--app-density))]">
              {/* <HorizontalAppNav sidebarData={sidebarData} /> */}

              <div className="py-2 animate-in fade-in slide-in-from-left-4 duration-500">
                <PageHeader />
              </div>

              {/* Content Area */}
              <div className="flex-1 max-sm:overflow-visible relative">
                <Outlet context={{ sidebarData }} />
              </div>
            </div>
          </main>
        </div>
      
    </div>
  )
}

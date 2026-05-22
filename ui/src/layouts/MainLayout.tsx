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
import { TopbarAppMenu } from './components/TopbarAppMenu'
import Combobox from '../aras-core/components/Combobox'
import { DesignInspector } from '../aras-core/components/design/DesignInspector'

export default function MainLayout() {
  const [sidebarData, setSidebarData] = useState<SidebarApp[]>([])
  const { organizations, activeOrgId, setActiveOrg, logout } = useAuthStore()
  const location = useLocation()
  const activeOrganization = organizations.find((organization) => organization.id === activeOrgId)
  const { notify } = useAras()
  const { closePanel, themeMode, cornerMode, density, accentColor, fontScale, sidebarCollapsed, designMode } = useUIStore()

  const themeTokens = {
    light: {
      bg: '#e8ecf2',
      panel: '#ffffff',
      panelSoft: '#f4f6f9',
      tableHead: '#f4f6f9',
      border: '#e2e8f0',
      borderStrong: '#cbd5e1',
      text: '#0f172a',
      muted: '#64748b',
      button: accentColor,
    },
    normal: {
      bg: '#eaecf0',
      panel: '#ffffff',
      panelSoft: '#f5f6f8',
      tableHead: '#f5f6f8',
      border: '#e5e7eb',
      borderStrong: '#d1d5db',
      text: '#111827',
      muted: '#6b7280',
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
  }[themeMode] || {
    bg: '#e8ecf2',
    panel: '#ffffff',
    panelSoft: '#f4f6f9',
    tableHead: '#f4f6f9',
    border: '#e2e8f0',
    borderStrong: '#cbd5e1',
    text: '#0f172a',
    muted: '#64748b',
    button: '#111111',
  }

  const layoutStyle = {
    '--aras-accent': accentColor,
    '--aras-accent-strong': accentColor === '#ffffff' ? '#e5e7eb' : accentColor,
    '--aras-button': themeTokens.button,
    '--aras-button-text': themeTokens.button === '#ffffff' ? '#111111' : '#ffffff',
    '--aras-radius': cornerMode === 'square' ? '0px' : '8px',
    '--aras-radius-lg': cornerMode === 'square' ? '0px' : '24px',
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
    const root = document.documentElement
    Object.entries(layoutStyle).forEach(([key, value]) => {
      root.style.setProperty(key, String(value))
    })
  }, [layoutStyle])

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
    <div className={`h-screen overflow-hidden flex ${designMode ? 'p-0 bg-slate-100' : 'p-4 md:p-6 bg-[var(--aras-bg-main)] gap-4 md:gap-6'} text-[var(--aras-text)] font-sans antialiased transition-all`} style={layoutStyle}>
      <div className={`flex flex-1 overflow-hidden ${designMode ? 'p-4 md:p-6 gap-4 md:gap-6' : ''}`}>
        <Sidebar
          sidebarData={sidebarData}
          currentPath={location.pathname}
          onLogout={logout}
        />

        <div id="content-wrapper" className={`flex flex-col flex-1 min-w-0 h-full overflow-hidden transition-[margin,padding] duration-300 ease-in-out ${sidebarCollapsed ? 'md:ml-[8.5rem]' : 'md:ml-[18.5rem]'}`}>
          <main id="main-content" className="flex-1 overflow-y-auto flex flex-col gap-3 md:gap-4 pb-20 md:pb-4 min-w-0">

            <Header moduleMenu={<TopbarAppMenu sidebarData={sidebarData} />}>
              <div className="z-50 flex items-center gap-3 px-4 max-sm:hidden">
                <div className="flex items-center gap-2">
                  <Building2 size={16} className="text-[var(--aras-muted)]" />
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
                    <span className="text-sm font-bold text-[var(--aras-muted)] uppercase tracking-wider">
                      {activeOrganization?.name || 'Loading...'}
                    </span>
                  )}
                </div>
              </div>
            </Header>

            {/* Content Area */}
            <div className="flex-1 max-sm:overflow-visible relative">
              <Outlet context={{ sidebarData }} />
            </div>
          </main>
        </div>
      </div>
      
      {designMode && (
        <DesignInspector />
      )}
    </div>
  )
}

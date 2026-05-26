// claude-opus-4-7
// ARC shell: full-bleed bg + dot-grid, ARC sidebar on the left, topbar, content frame.
import { useEffect, useState, type CSSProperties } from 'react'
import { useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../lib/api'
import type { SidebarApp } from './types'
import { Sidebar } from './components/Sidebar'
import { Header } from './components/Header'
import { Building2, ChevronRight } from 'lucide-react'
import { useAras } from '../aras-core/hooks/useAras'
import { useUIStore } from '../store/uiStore'
import SimpleCombobox from '../aras-core/components/SimpleCombobox'
import TweaksPanel from '../aras-core/components/TweaksPanel'

export default function MainLayout() {
  const [sidebarData, setSidebarData] = useState<SidebarApp[]>([])
  const { organizations, activeOrgId, setActiveOrg } = useAuthStore()
  const location = useLocation()
const { notify } = useAras()
  const { closePanel, themeMode, cornerMode, density, fontScale, accentColor, iconRailCollapsed, toggleIconRail } = useUIStore()

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
    <div className="arc arc-bg arc-dotgrid h-screen w-full overflow-hidden flex font-sans antialiased" style={layoutStyle}>
      <Sidebar
        sidebarData={sidebarData}
        currentPath={location.pathname}
      />
      {iconRailCollapsed && (
        <button
          onClick={toggleIconRail}
          aria-label="Show sidebar"
          className="fixed left-0 top-1/2 -translate-y-1/2 flex items-center justify-center text-[var(--text-3)] hover:text-[var(--text)] transition-colors"
          style={{
            width: 14,
            height: 56,
            background: 'var(--bg-2)',
            border: '1px solid var(--line)',
            borderLeft: 'none',
            borderRadius: '0 8px 8px 0',
            zIndex: 60,
            cursor: 'pointer',
          }}
        >
          <ChevronRight size={12} />
        </button>
      )}

      <TweaksPanel />
      <div id="content-wrapper"
           className="flex flex-col flex-1 min-w-0 h-full overflow-hidden relative z-10">
        <Header>
          <div className="z-50 flex items-center gap-2 max-sm:hidden">
            <Building2 size={13} className="text-[var(--text-3)]" />
            {organizations.length > 1 ? (
              <SimpleCombobox
                width={180}
                options={[
                  { label: 'All Organizations', value: -1 },
                  ...organizations.map((org) => ({ label: org.name, value: org.id })),
                ]}
                value={activeOrgId ?? -1}
                onChange={(val) => setActiveOrg(Number(val))}
                placeholder="Select Organization"
              />
            ) : null}
          </div>
        </Header>

        <main id="main-content" className="flex-1 overflow-y-auto min-w-0 relative flex flex-col arc-scroll">
          <div className="flex-1 flex flex-col">
            <div className="flex-1 max-sm:overflow-visible relative">
              <Outlet context={{ sidebarData }} />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

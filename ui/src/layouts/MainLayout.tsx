import { useState, useEffect } from 'react'
import { useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../lib/api'
import type { SidebarApp } from './types'
import { Sidebar } from './components/Sidebar'
import { Header } from './components/Header'
import { Breadcrumbs } from './components/Breadcrumbs'
import { TopbarAppMenu } from './components/TopbarAppMenu'
import { Building2 } from 'lucide-react'
import { useAras } from '../aras-core/hooks/useAras'

export default function MainLayout() {
  const [isSidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarData, setSidebarData] = useState<SidebarApp[]>([])
  const { organizations, activeOrgId, setActiveOrg, logout } = useAuthStore()
  const location = useLocation()
  const activeOrganization = organizations.find((organization) => organization.id === activeOrgId)
  const { notify } = useAras()

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
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
      <Sidebar
        isOpen={isSidebarOpen}
        setOpen={setSidebarOpen}
        sidebarData={sidebarData}
        currentPath={location.pathname}
        onLogout={logout}
      />

      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="relative">
          <Header />
          {organizations.length > 1 && (
            <div className="absolute right-36 top-3 z-50">
              <label className="sr-only" htmlFor="organization-selector">Organization</label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" size={16} />
                <select
                  id="organization-selector"
                  value={activeOrgId ?? ''}
                  onChange={(event) => setActiveOrg(Number(event.target.value))}
                  className="h-10 min-w-48 max-w-64 appearance-none rounded-xl border border-slate-200 bg-white pl-9 pr-8 text-sm font-semibold text-slate-700 shadow-sm outline-none transition-colors hover:border-slate-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                >
                  {organizations.map((organization) => (
                    <option key={organization.id} value={organization.id}>{organization.name}</option>
                  ))}
                </select>
              </div>
              <span className="sr-only">{activeOrganization?.name}</span>
            </div>
          )}
        </div>
        <Breadcrumbs />
        <TopbarAppMenu sidebarData={sidebarData} />

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-8 bg-slate-50/50">
          <div className="max-w-7xl mx-auto">
            <Outlet context={{ sidebarData }} />
          </div>
        </div>
      </main>
    </div>
  )
}

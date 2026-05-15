import { useState, useEffect } from 'react'
import { useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../lib/api'
import type { SidebarApp } from './types'
import { Sidebar } from './components/Sidebar'
import { Header } from './components/Header'
import { Breadcrumbs } from './components/Breadcrumbs'
import { TopbarAppMenu } from './components/TopbarAppMenu'

export default function MainLayout() {
  const [isSidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarData, setSidebarData] = useState<SidebarApp[]>([])
  const logout = useAuthStore((state) => state.logout)
  const location = useLocation()

  useEffect(() => {
    const fetchSidebar = async () => {
      try {
        const res = await api.get('/sidebar')
        setSidebarData(res.data)
      } catch (err) {
        console.error("Failed to fetch sidebar", err)
      }
    }
    fetchSidebar()
  }, [])

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
        <Header />
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

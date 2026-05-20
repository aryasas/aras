import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { resolveIcon } from '../lib/iconUtils'
import { ArrowRight } from 'lucide-react'
import { DashboardView } from './DashboardView'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'
import api from '../lib/api'

interface SidebarApp {
  name: string
  label: string
  icon: string
  path: string
  app_type?: string
  sub_apps?: SidebarApp[]
}

export default function HomeView() {
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const [apps, setApps] = useState<SidebarApp[]>([])
  const setPageTitle = useUIStore(state => state.setPageTitle)

  const displayName = user?.full_name || user?.username || 'there'

  useEffect(() => {
    setPageTitle(`Welcome back, ${displayName}`, "Here's what's happening in your workspace today.", "HOME")
    return () => setPageTitle('', '', '')
  }, [displayName, setPageTitle])

  useEffect(() => {
    api.get('/sidebar').then((res) => setApps(res.data)).catch(() => {})
  }, [])

  const userApps = apps.filter(a => a.app_type !== 'framework')

  return (
    <>
      {userApps.length > 0 && (
        <div className="mb-10">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Your Apps</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {userApps.map((app) => {
              const IconComponent = resolveIcon(app.icon)
              return (
                <button
                  key={app.name}
                  onClick={() => navigate(app.path || `/apps/${app.name}`)}
                  className="group flex flex-col items-start p-5 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 hover:shadow-md hover:border-indigo-200 dark:hover:border-indigo-700 transition-all text-left"
                >
                  <div className="p-2 bg-indigo-50 dark:bg-indigo-900/30 rounded-lg mb-3">
                    <IconComponent size={20} className="text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">{app.label}</span>
                  <span className="mt-1 flex items-center gap-1 text-xs text-slate-400 group-hover:text-indigo-500 transition-colors">
                    Open <ArrowRight size={12} />
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      <DashboardView />
    </>
  )
}

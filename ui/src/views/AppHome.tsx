import { useEffect, useMemo, useState } from 'react'
import { Link, useOutletContext, useParams } from 'react-router-dom'
import * as LucideIcons from 'lucide-react'
import api from '../lib/api'
import type { SidebarItem } from '../layouts/types'

interface OutletContext {
  sidebarData: SidebarItem[]
}

interface AppMenuModel {
  name: string
  label: string
  path?: string
}

interface AppMenuData {
  app_name: string
  app_label: string
  icon: string
  have_home?: boolean
  models: AppMenuModel[]
  sub_apps?: {
    name: string
    label: string
    icon: string
    path: string
  }[]
}

export default function AppHome() {
  const { appName } = useParams()
  const { sidebarData } = useOutletContext<OutletContext>()
  const [remoteMenu, setRemoteMenu] = useState<AppMenuData | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const sidebarApp = useMemo(
    () => sidebarData.find((item) => (item.type || 'app') === 'app' && item.name === appName),
    [appName, sidebarData]
  )

  useEffect(() => {
    let cancelled = false

    if (!appName || sidebarApp?.have_home) {
      setRemoteMenu(null)
      return
    }

    setIsLoading(true)
    api.get(`/app-menu/${appName}`)
      .then((res) => {
        if (!cancelled) setRemoteMenu(res.data)
      })
      .catch(() => {
        if (!cancelled) setRemoteMenu(null)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [appName, sidebarApp?.have_home])

  const appInfo: AppMenuData | null = remoteMenu || (sidebarApp ? {
    app_name: sidebarApp.name,
    app_label: sidebarApp.label,
    icon: sidebarApp.icon,
    have_home: sidebarApp.have_home,
    models: sidebarApp.models || [],
    sub_apps: sidebarApp.sub_apps?.map(s => ({
       name: s.name,
       label: s.label,
       icon: s.icon,
       path: s.have_home ? `/${s.name}` : (s.models?.[0]?.path || `/${s.name}/${s.models?.[0]?.name}` || `/${s.name}`)
    })) || [],
  } : null)

  if (!appName || isLoading) {
    return (
      <div className="p-12 text-center text-slate-400 bg-white rounded-2xl border border-dashed border-slate-200">
        Loading application...
      </div>
    )
  }

  if (!appInfo) {
    return (
      <div className="p-12 text-center text-slate-400 bg-white rounded-2xl border border-dashed border-slate-200">
        Application not found.
      </div>
    )
  }

  const IconComponent = (LucideIcons as any)[appInfo.icon] || LucideIcons.Package

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-5">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
          <IconComponent size={34} />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-slate-900">{appInfo.app_label}</h1>
          <p className="mt-1 text-sm text-slate-500">Choose a workspace to open.</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {/* Render Sub-Apps first if any */}
        {appInfo.sub_apps?.map((sub) => {
          const SubIcon = (LucideIcons as any)[sub.icon] || LucideIcons.Package
          return (
            <Link
              key={sub.name}
              to={sub.path}
              className="group flex min-h-28 items-center gap-4 rounded-lg border border-indigo-100 bg-indigo-50/30 p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-indigo-300 hover:shadow-md"
            >
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-white text-indigo-600 shadow-sm transition-colors group-hover:bg-indigo-600 group-hover:text-white">
                <SubIcon size={22} />
              </div>
              <div className="min-w-0">
                <h2 className="truncate text-base font-bold text-slate-900">{sub.label}</h2>
                <p className="mt-1 text-sm text-slate-600 italic">Module</p>
              </div>
            </Link>
          )
        })}

        {appInfo.models.map((model) => {
          const targetPath = model.path || `/${appName}/${model.name}`

          return (
            <Link
              key={model.name}
              to={targetPath}
              className="group flex min-h-28 items-center gap-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md"
            >
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500 transition-colors group-hover:bg-indigo-50 group-hover:text-indigo-600">
                <IconComponent size={22} />
              </div>
              <div className="min-w-0">
                <h2 className="truncate text-base font-semibold text-slate-900">{model.label}</h2>
                <p className="mt-1 text-sm text-slate-500">Open records</p>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

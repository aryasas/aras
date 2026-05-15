import { useEffect, useMemo, useState } from 'react'
import { Link, useOutletContext, useParams } from 'react-router-dom'
import * as LucideIcons from 'lucide-react'
import api from '../lib/api'
import type { SidebarItem, AppMenuData, MenuItem } from '../layouts/types'

interface OutletContext {
  sidebarData: SidebarItem[]
}

export default function AppHome() {
  const params = useParams()
  const { sidebarData } = useOutletContext<OutletContext>()
  const [remoteMenu, setRemoteMenu] = useState<AppMenuData | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Combine segments to get the full app path
  const appPath = useMemo(() => {
    const splat = params['*'] || ''
    return [params.segment1, ...splat.split('/').filter(Boolean)].filter(Boolean).join('/')
  }, [params])

  const sidebarApp = useMemo(
    () => sidebarData.find((item) => {
      const itemPath = (item.path || `/${item.name}`).replace(/^\//, '')
      return itemPath === appPath
    }),
    [appPath, sidebarData]
  )

  useEffect(() => {
    let cancelled = false

    if (!appPath) {
      setRemoteMenu(null)
      return
    }

    setIsLoading(true)
    api.get(`/app-menu/${appPath}`)
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
  }, [appPath])

  if (!appPath || isLoading) {
    return (
      <div className="p-12 text-center text-slate-400 bg-white rounded-2xl border border-dashed border-slate-200">
        Loading application...
      </div>
    )
  }

  if (!remoteMenu && !sidebarApp) {
    return (
      <div className="p-12 text-center text-slate-400 bg-white rounded-2xl border border-dashed border-slate-200">
        Application not found.
      </div>
    )
  }

  const appInfo = remoteMenu || {
    app_label: sidebarApp?.label || appPath,
    icon: sidebarApp?.icon || 'Package',
    menu: [],
    sub_apps: []
  }

  const IconComponent = (LucideIcons as any)[appInfo.icon] || LucideIcons.Package

  const renderTile = (item: MenuItem, groupLabel?: string) => {
    const ItemIcon = (LucideIcons as any)[item.icon || 'FileText'] || LucideIcons.FileText
    return (
      <Link
        key={item.name}
        to={item.path}
        className="group flex min-h-28 items-center gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:-translate-y-1 hover:border-indigo-200 hover:shadow-md"
      >
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-500 transition-colors group-hover:bg-indigo-50 group-hover:text-indigo-600">
          <ItemIcon size={24} />
        </div>
        <div className="min-w-0">
          <h2 className="truncate text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">{item.label || item.name}</h2>
          <p className="mt-0.5 text-xs text-slate-500 font-medium uppercase tracking-wider">{groupLabel || 'Resource'}</p>
        </div>
      </Link>
    )
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="flex items-center gap-6">
        <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 shadow-sm">
          <IconComponent size={40} />
        </div>
        <div>
          <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">{appInfo.app_label}</h1>
          <p className="mt-1.5 text-slate-500 font-medium">Select a module or resource to continue.</p>
        </div>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
        {/* Render Sub-Apps first if any */}
        {appInfo.sub_apps?.map((sub: any) => {
          const SubIcon = (LucideIcons as any)[sub.icon] || LucideIcons.Package
          return (
            <Link
              key={sub.name}
              to={sub.path}
              className="group flex min-h-28 items-center gap-4 rounded-xl border border-indigo-100 bg-indigo-50/40 p-5 shadow-sm transition-all hover:-translate-y-1 hover:border-indigo-300 hover:shadow-md"
            >
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white text-indigo-600 shadow-sm transition-colors group-hover:bg-indigo-600 group-hover:text-white">
                <SubIcon size={24} />
              </div>
              <div className="min-w-0">
                <h2 className="truncate text-base font-bold text-slate-900">{sub.label}</h2>
                <p className="mt-0.5 text-xs text-indigo-600 font-bold uppercase tracking-wider">Module</p>
              </div>
            </Link>
          )
        })}

        {/* Render items from menu groups */}
        {appInfo.menu?.map((element: any) => {
           if (element.type === 'group') {
              return element.items.map((item: MenuItem) => renderTile(item, element.label))
           }
           return renderTile(element)
        })}
      </div>

      {(!appInfo.menu || appInfo.menu.length === 0) && (!appInfo.sub_apps || appInfo.sub_apps.length === 0) && (
         <div className="p-12 text-center text-slate-400 bg-white rounded-3xl border border-dashed border-slate-200">
            No resources available for this application.
         </div>
      )}
    </div>
  )
}

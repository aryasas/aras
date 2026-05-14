import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import api from '../../lib/api'

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
}

const hiddenTopbarRoutes = new Set(['dashboard', 'settings'])

export function TopbarAppMenu() {
  const location = useLocation()
  const [menuData, setMenuData] = useState<AppMenuData | null>(null)
  const [failedApp, setFailedApp] = useState<string | null>(null)

  const appName = useMemo(() => {
    const [firstSegment] = location.pathname.split('/').filter(Boolean)
    return firstSegment || null
  }, [location.pathname])

  useEffect(() => {
    let cancelled = false

    if (!appName || hiddenTopbarRoutes.has(appName)) {
      setMenuData(null)
      setFailedApp(null)
      return
    }

    setFailedApp(null)
    api.get(`/app-menu/${appName}`)
      .then((res) => {
        if (!cancelled) setMenuData(res.data)
      })
      .catch(() => {
        if (!cancelled) {
          setMenuData(null)
          setFailedApp(appName)
        }
      })

    return () => {
      cancelled = true
    }
  }, [appName])

  if (!appName || failedApp === appName || !menuData) {
    return null
  }

  const tabs = [
    ...(menuData.have_home ? [{ name: '__home__', label: 'Home', path: `/${appName}` }] : []),
    ...menuData.models.map((model) => ({
      name: model.name,
      label: model.label,
      path: model.path || `/${appName}/${model.name}`,
    })),
  ]

  if (tabs.length === 0) {
    return null
  }

  return (
    <nav className="bg-white border-b border-slate-200 px-8">
      <div className="flex h-11 items-end gap-1 overflow-x-auto">
        {tabs.map((tab) => {
          const isHome = tab.path === `/${appName}`
          const isActive = isHome
            ? location.pathname === tab.path
            : location.pathname === tab.path || location.pathname.startsWith(`${tab.path}/`)

          return (
            <Link
              key={tab.name}
              to={tab.path}
              className={`relative flex h-10 shrink-0 items-center px-4 text-sm font-medium transition-colors ${
                isActive
                  ? 'text-indigo-600'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              {tab.label}
              {isActive && (
                <span className="absolute inset-x-3 bottom-0 h-0.5 rounded-full bg-indigo-600" />
              )}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}

import { lazy, Suspense, type ComponentType } from 'react'
import { useParams, useOutletContext, useLocation } from 'react-router-dom'
import DynamicView from './DynamicView'
import AppHome from './AppHome'
import type { SidebarItem } from '../layouts/types'

interface OutletContext { sidebarData: SidebarItem[] }

// Custom home overrides keyed by app slug (exact single-segment match only)
const customHomeMap: Record<string, ReturnType<typeof lazy<ComponentType>>> = {
}

function normalizePath(path?: string) {
  if (!path) return ''
  return path.replace(/^\/+/, '').replace(/\/+$/, '')
}

// claude-sonnet-4-6
export default function SmartDispatcher() {
  const params = useParams()
  const location = useLocation()
  const { sidebarData } = useOutletContext<OutletContext>()

  const splat = params['*'] || ''
  const segment1 = params.segment1
  const fromParams = [segment1, ...splat.split('/').filter(Boolean)].filter(Boolean) as string[]
  const fromLocation = location.pathname.replace(/^\//, '').split('/').filter(Boolean)
  const allSegments = fromParams.length > 0 ? fromParams : fromLocation
  const currentPath = allSegments.join('/')

  if (allSegments.length === 0) return null

  // Single-segment custom home override (e.g. /dev → DevTools)
  const singleSlug = allSegments.length === 1 ? allSegments[0] : null
  const CustomHome = singleSlug ? customHomeMap[singleSlug] : null
  if (CustomHome) return <Suspense fallback={null}><CustomHome /></Suspense>

  const isAppHomePath = sidebarData.some((app) => {
    const appPath = normalizePath(app.path || `/${app.name}`)
    if (appPath === currentPath) return true
    return app.sub_apps?.some((sub) => normalizePath(sub.path || `/${sub.name}`) === currentPath)
  })

  if (isAppHomePath) return <AppHome />

  return <DynamicView />
}

import { Suspense } from 'react'
import { useParams, useOutletContext, useLocation } from 'react-router-dom'
import DynamicView from './DynamicView'
import AppHome from './AppHome'
import type { SidebarItem } from '../layouts/types'
import type { MenuElement, MenuItem } from '../layouts/types'
import { getCustomPage, hasCustomPage } from '../aras-core/customPageRegistry'
import { appRouteMatchTargets, isRouteMatch, normalizeRoutePath } from '../lib/navUtils'

interface OutletContext {
  sidebarData: SidebarItem[]
  menuData?: {
    menu?: MenuElement[]
    sub_apps?: Array<{ menu?: MenuElement[] }>
  } | null
  isLoadingMenu?: boolean
}
const warnedKeys = new Set<string>()

function findCustomMenuItem(menu: MenuElement[] | undefined, currentPath: string): MenuItem | null {
  for (const element of menu || []) {
    if (element.type === 'group') {
      const match = element.items.find((item) => item.type === 'custom' && normalizeRoutePath(item.path) === currentPath)
      if (match) return match
      continue
    }

    if (element.type === 'custom' && normalizeRoutePath(element.path) === currentPath) {
      return element
    }
  }

  return null
}

// claude-sonnet-4-6
export default function SmartDispatcher() {
  const params = useParams()
  const location = useLocation()
  const { sidebarData, menuData, isLoadingMenu } = useOutletContext<OutletContext>()

  const splat = params['*'] || ''
  const segment1 = params.segment1
  const fromParams = [segment1, ...splat.split('/').filter(Boolean)].filter(Boolean) as string[]
  const fromLocation = location.pathname.replace(/^\//, '').split('/').filter(Boolean)
  const allSegments = fromParams.length > 0 ? fromParams : fromLocation
  const currentPath = normalizeRoutePath(location.pathname || `/${allSegments.join('/')}`)

  if (allSegments.length === 0) return null

  const activeApp = sidebarData.find((app) => {
    if (appRouteMatchTargets(app).some((target) => isRouteMatch(currentPath, target))) return true
    return (app.sub_apps || []).some((subApp) => appRouteMatchTargets(subApp).some((target) => isRouteMatch(currentPath, target)))
  }) || null

  if (activeApp && isLoadingMenu && currentPath.startsWith('/admin/')) return null

  const customItem = activeApp
    ? findCustomMenuItem(menuData?.menu, currentPath)
      || (menuData?.sub_apps || []).map((subApp) => findCustomMenuItem(subApp.menu, currentPath)).find(Boolean)
      || null
    : null

  if (customItem?.component) {
    const CustomPage = getCustomPage(customItem.component)
    if (CustomPage) {
      return <Suspense fallback={null}><CustomPage /></Suspense>
    }

    if (!hasCustomPage(customItem.component) && !warnedKeys.has(customItem.component)) {
      warnedKeys.add(customItem.component)
      console.warn(`Custom page component "${customItem.component}" is not registered.`)
    }
  }

  const isAppHomePath = sidebarData.some((app) => {
    if (appRouteMatchTargets(app).some((target) => normalizeRoutePath(target) === currentPath)) return true
    return app.sub_apps?.some((sub) => appRouteMatchTargets(sub).some((target) => normalizeRoutePath(target) === currentPath))
  })

  if (isAppHomePath) return <AppHome />

  return <DynamicView />
}

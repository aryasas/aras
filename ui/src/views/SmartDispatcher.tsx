import { useParams, useOutletContext } from 'react-router-dom'
import AppHome from './AppHome'
import DynamicView from './DynamicView'
import type { SidebarItem } from '../layouts/types'

interface OutletContext {
  sidebarData: SidebarItem[]
}

export default function SmartDispatcher() {
  const params = useParams()
  const { sidebarData } = useOutletContext<OutletContext>()
  const splat = params['*'] || ''
  const segment1 = params.segment1
  const allSegments = [segment1, ...splat.split('/').filter(Boolean)].filter(Boolean) as string[]

  if (allSegments.length === 0) return null

  // 1 Segment (e.g., /erp) -> App Home
  if (allSegments.length === 1) {
    return <AppHome />
  }

  // 3+ Segments (e.g., /erp/accounting/accounts) -> Resource View
  if (allSegments.length >= 3) {
    return <DynamicView />
  }

  // 2 Segments (e.g., /erp/accounting OR /inventory/products)
  // Check if the 2-segment path exists in sidebarData (as a sub-app or root app)
  const currentPath = allSegments.join('/')
  const isApp = sidebarData.some(app => {
    const appPath = (app.path || `/${app.name}`).replace(/^\//, '')
    if (appPath === currentPath) return true
    return app.sub_apps?.some(sub => {
      const subPath = (sub.path || `/${sub.name}`).replace(/^\//, '')
      return subPath === currentPath
    })
  })

  if (isApp) {
     return <AppHome />
  }

  return <DynamicView />
}

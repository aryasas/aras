import { useParams, useOutletContext } from 'react-router-dom'
import DynamicView from './DynamicView'
import AppHome from './AppHome'
import type { SidebarItem } from '../layouts/types'

interface OutletContext { sidebarData: SidebarItem[] }

function normalizePath(path?: string) {
  if (!path) return ''
  return path.replace(/^\/+/, '').replace(/\/+$/, '')
}

export default function SmartDispatcher() {
  const params = useParams()
  const { sidebarData } = useOutletContext<OutletContext>()
  const splat = params['*'] || ''
  const segment1 = params.segment1
  const allSegments = [segment1, ...splat.split('/').filter(Boolean)].filter(Boolean) as string[]
  const currentPath = allSegments.join('/')

  const isAppHomePath = sidebarData.some((app) => {
    const appPath = normalizePath(app.path || `/${app.name}`)
    if (appPath === currentPath) return true
    return app.sub_apps?.some((sub) => normalizePath(sub.path || `/${sub.name}`) === currentPath)
  })

  if (allSegments.length === 0) return null
  if (isAppHomePath) return <AppHome />

  return <DynamicView />
}

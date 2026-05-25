// claude-opus-4-7
// Routes /app paths: for app-root and sub-app paths, redirect to first submenu item.
// 3+ segment paths render DynamicView. AppHome is bypassed by user requirement.
import { useEffect, useState } from 'react'
import { useParams, useOutletContext, Navigate } from 'react-router-dom'
import DynamicView from './DynamicView'
import { LoadingState } from '../components/LoadingState'
import type { SidebarItem } from '../layouts/types'
import { useUIStore } from '../store/uiStore'
import { filterMenuElements, filterMenuItems } from '../lib/menuUtils'
import api from '../lib/api'

interface OutletContext { sidebarData: SidebarItem[] }

export default function SmartDispatcher() {
  const params = useParams()
  const { sidebarData } = useOutletContext<OutletContext>()
  const submenuOrder = useUIStore((s) => s.submenuOrder)
  const splat = params['*'] || ''
  const segment1 = params.segment1
  const allSegments = [segment1, ...splat.split('/').filter(Boolean)].filter(Boolean) as string[]

  const [firstPath, setFirstPath] = useState<string | null | undefined>(undefined)

  const needsRedirect = (() => {
    if (allSegments.length === 0) return false
    if (allSegments.length >= 3) return false
    const currentPath = allSegments.join('/')
    if (allSegments.length === 1) return true
    return sidebarData.some((app) => {
      const appPath = (app.path || `/${app.name}`).replace(/^\//, '')
      if (appPath === currentPath) return true
      return app.sub_apps?.some((sub) => {
        const subPath = (sub.path || `/${sub.name}`).replace(/^\//, '')
        return subPath === currentPath
      })
    })
  })()

  const appName = allSegments[0]

  useEffect(() => {
    if (!needsRedirect || !appName) { setFirstPath(null); return }
    const saved = submenuOrder[appName]
    if (saved && saved[0]) { setFirstPath(saved[0]); return }
    let cancelled = false
    api.get(`/app-menu/${appName}`)
      .then((res) => {
        if (cancelled) return
        const groups = filterMenuElements(res.data?.menu || [])
        for (const g of groups) {
          const items = filterMenuItems((g as any).items || [])
          if (items.length) { setFirstPath(items[0].path); return }
        }
        setFirstPath(null)
      })
      .catch(() => { if (!cancelled) setFirstPath(null) })
    return () => { cancelled = true }
  }, [needsRedirect, appName, submenuOrder])

  if (allSegments.length === 0) return null
  if (allSegments.length >= 3) return <DynamicView />

  if (needsRedirect) {
    if (firstPath === undefined) return <LoadingState label="Loading application..." />
    if (firstPath) return <Navigate to={firstPath} replace />
    // No menu items at all — fall through to DynamicView, which will likely 404 gracefully.
  }

  return <DynamicView />
}

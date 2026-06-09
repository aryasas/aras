import { useEffect, useMemo, useState } from 'react'
import api from '../../lib/api'
import { appRouteMatchTargets, applySubmenuOrder, flattenAppMenu, isRouteMatch, normalizeRoutePath, type FlatMenuItem } from '../../lib/navUtils'
import { useUIStore } from '../../store/uiStore'
import type { SidebarApp } from '../types'

export function useAppMenu(apps: SidebarApp[], currentPath: string) {
  const submenuOrder = useUIStore((state) => state.submenuOrder)
  const [menuData, setMenuData] = useState<any>(null)
  const [isLoadingMenu, setIsLoadingMenu] = useState(false)

  const activeApp = useMemo(() => {
    const current = normalizeRoutePath(currentPath)
    return apps
      .map((app) => ({ app, targets: appRouteMatchTargets(app) }))
      .filter(({ targets }) => targets.some((target) => isRouteMatch(current, target)))
      .sort((a, b) => Math.max(...b.targets.map((target) => target.length)) - Math.max(...a.targets.map((target) => target.length)))[0]?.app || null
  }, [apps, currentPath])

  useEffect(() => {
    if (!activeApp || activeApp.type === 'link') {
      setMenuData(null)
      setIsLoadingMenu(false)
      return
    }

    let cancelled = false
    setIsLoadingMenu(true)
    const menuPath = normalizeRoutePath(activeApp.path || `/${activeApp.name}`).replace(/^\//, '')

    api.get(`/app-menu/${menuPath}`)
      .then((res) => {
        if (!cancelled) setMenuData(res.data)
      })
      .catch(() => {
        if (!cancelled) setMenuData(null)
      })
      .finally(() => {
        if (!cancelled) setIsLoadingMenu(false)
      })

    return () => { cancelled = true }
  }, [activeApp?.name, activeApp?.path, activeApp?.type])

  const flatItems = useMemo<FlatMenuItem[]>(() => flattenAppMenu(menuData), [menuData])
  const orderedItems = useMemo<FlatMenuItem[]>(() => (
    activeApp ? applySubmenuOrder(flatItems, submenuOrder[activeApp.name]) : []
  ), [activeApp, flatItems, submenuOrder])

  return { activeApp, menuData, isLoadingMenu, flatItems, orderedItems }
}

export default useAppMenu

import type { MenuItem, SidebarApp } from '../layouts/types'
import { filterMenuElements, filterMenuItems } from './menuUtils'

export interface FlatMenuItem extends MenuItem {
  id: string
  groupLabel?: string
}

// claude-opus-4-8
export function normalizeRoutePath(path?: string): string {
  if (!path) return '/'
  const normalized = path.startsWith('/') ? path : `/${path}`
  return normalized.length > 1 ? normalized.replace(/\/+$/, '') : normalized
}

// claude-opus-4-8
export function appRoutePath(item?: Pick<SidebarApp, 'name' | 'path'> | null): string {
  if (!item) return '/'
  if (item.name === 'settings' || item.path === '/settings') return '/admin/settings'
  return normalizeRoutePath(item.path || `/${item.name}`)
}

// claude-opus-4-8
export function isRouteMatch(currentPath: string, targetPath?: string): boolean {
  const current = normalizeRoutePath(currentPath)
  const target = normalizeRoutePath(targetPath)
  return current === target || current.startsWith(`${target}/`)
}

function isAdminSettingsLabel(value?: string) {
  const normalized = String(value || '').toLowerCase()
  return normalized.includes('setting') || normalized.includes('admin')
}

function buildMenuElements(menuData: any) {
  const elements = filterMenuElements(menuData?.menu || [])
  const existingPaths = new Set(elements.map((element: any) => element?.path).filter(Boolean))
  const subApps = (menuData?.sub_apps || []).filter((subApp: any) => !existingPaths.has(subApp.path))
  return [...elements, ...subApps.map((subApp: any) => ({ ...subApp, type: 'app_link' }))]
}

// claude-opus-4-8
export function flattenAppMenu(menuData: any): FlatMenuItem[] {
  const items: FlatMenuItem[] = []

  buildMenuElements(menuData).forEach((element: any) => {
    if (isAdminSettingsLabel(element.label) || isAdminSettingsLabel(element.name)) return

    if (element.type === 'group') {
      filterMenuItems(element.items || []).forEach((item: MenuItem) => {
        if (isAdminSettingsLabel(item.label) || isAdminSettingsLabel(item.name)) return
        items.push({ ...item, id: item.path || item.name, groupLabel: element.label })
      })
      return
    }

    items.push({ ...element, id: element.path || element.name, groupLabel: 'General' })
  })

  return items
}

// claude-opus-4-8
export function firstPathFromMenuData(data: any): string | null {
  for (const element of buildMenuElements(data)) {
    if (isAdminSettingsLabel(element.label) || isAdminSettingsLabel(element.name)) continue

    if (element.type === 'group') {
      const firstItem = filterMenuItems(element.items || []).find((item: MenuItem) => (
        !isAdminSettingsLabel(item.label) && !isAdminSettingsLabel(item.name)
      ))
      if (firstItem?.path) return normalizeRoutePath(firstItem.path)
      continue
    }

    if (element.path) return normalizeRoutePath(element.path)
  }

  return null
}

// claude-opus-4-8
export function applySubmenuOrder(flatItems: FlatMenuItem[], saved?: string[]): FlatMenuItem[] {
  if (!saved?.length) return flatItems
  const byId = new Map(flatItems.map((item) => [item.id, item]))
  const reordered: FlatMenuItem[] = []

  saved.forEach((id) => {
    const item = byId.get(id)
    if (!item) return
    reordered.push(item)
    byId.delete(id)
  })

  byId.forEach((item) => reordered.push(item))
  return reordered
}

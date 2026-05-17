import type { MenuElement, MenuItem } from '../layouts/types'

function isSupplierLabel(value?: string | null) {
  return /supplier/i.test(value || '')
}

export function isVisibleMenuItem(item: { name?: string; label?: string | null }) {
  return !isSupplierLabel(item.name) && !isSupplierLabel(item.label)
}

export function filterMenuItems<T extends MenuItem>(items: T[]): T[] {
  return items.filter(isVisibleMenuItem)
}

export function filterMenuElements<T extends MenuElement>(items: T[]): T[] {
  return items
    .filter((item) => item.type === 'group' ? !isSupplierLabel(item.label) : !isSupplierLabel(item.name) && !isSupplierLabel(item.label))
    .map((item) => {
      if (item.type !== 'group') return item
      return { ...item, items: filterMenuItems(item.items) }
    }) as T[]
}

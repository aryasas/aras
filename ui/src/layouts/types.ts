export interface SidebarItem {
  type?: 'app' | 'link'
  name: string
  label: string
  icon: string
  have_home?: boolean
  path?: string
  models?: { name: string, label: string, path?: string }[]
}

// For backward compatibility until fully refactored
export type SidebarApp = SidebarItem

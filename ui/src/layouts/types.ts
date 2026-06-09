export interface SidebarItem {
  type?: 'app' | 'link'
  name: string
  label: string
  icon: string
  have_home?: boolean
  path?: string
  hide_from_sidebar?: boolean
  sub_apps?: SidebarItem[]
  models?: {
    name: string
    label: string
    path?: string
  }[]
}

export type SidebarApp = SidebarItem

export interface MenuItem {
  type: 'model' | 'app_link' | 'link' | 'custom'
  name: string
  label?: string
  path: string
  icon?: string
  component?: string
}

export interface MenuGroup {
  type: 'group'
  label: string
  icon: string
  items: MenuItem[]
}

export type MenuElement = MenuItem | MenuGroup

export interface AppMenuData {
  app_name: string
  app_label: string
  icon: string
  have_home?: boolean
  menu: MenuElement[]
  sub_apps: { name: string, label: string, icon: string, path: string, menu?: MenuElement[] }[]
}

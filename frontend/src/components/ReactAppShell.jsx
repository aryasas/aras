import React, { useEffect, useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import ArasListView from './ArasListView'
import ArasFormView from './ArasFormView'
import ArasAppHome from './ArasAppHome'
import CustomerPage from './CustomerPage'
import SettingsPage from './SettingsPage'
import AppSettingsPage from './AppSettingsPage'
import TrashPage from './TrashPage'
import { TweakPanel } from './TweakPanel'
import { useThemeStore } from '../lib/themeStore'
import { api } from '../lib/api'
import ArasSidebar from './ArasSidebar'
import ArasTopMenu from './ArasTopMenu'

/**
 * Parses the current pathname into a config object.
 * Logic matches Aras URL conventions:
 * /admin/ -> dashboard
 * /admin/settings -> settings
 * /admin/trash -> trash
 * /admin/:appSlug/:resource/list -> list view
 * /admin/:appSlug/:resource/form/:id -> form view
 */
function parsePath(path, currentMenu = []) {
  const parts = path.split('/').filter(Boolean)
  // parts[0] is 'admin'
  if (parts.length <= 1) return { viewType: 'dashboard' }
  
  const slug = parts[1]
  if (slug === 'settings') return { viewType: 'settings' }
  if (slug === 'trash') return { viewType: 'trash' }
  if (slug === 'dashboard') return { viewType: 'dashboard' }

  // Check for app home: /admin/:app/
  if (parts.length === 2) return { viewType: 'appHome', appSlug: slug }

  const last = parts[parts.length - 1]
  
  // 1. ADD Form
  if (last === 'add') {
    const resource = parts.slice(2, -1).join('/')
    return { appSlug: slug, resource, viewType: 'form', action: 'add' }
  }

  // 2. EDIT Form
  let id = null
  let isEdit = false
  if (last === 'edit') {
    id = parts[parts.length - 2]
    isEdit = true
  } else if (!isNaN(last) && !isNaN(parseFloat(last))) {
    id = last
    isEdit = true
  }

  if (isEdit && id) {
    const resource = parts.slice(2, last === 'edit' ? -2 : -1).join('/')
    return { appSlug: slug, resource, viewType: 'form', id, action: 'edit' }
  }

  // 3. LIST or GROUP View
  if (last === 'list' || parts.length > 2) {
    const resource = parts.slice(2, last === 'list' ? -1 : undefined).join('/')
    
    // Check menu for group type
    const findInMenu = (items) => {
      if (!items) return null
      for (const item of items) {
        if (item.url === path || item.url === (path + '/')) return item
        if (item.children) {
          const found = findInMenu(item.children)
          if (found) return found
        }
      }
      return null
    }

    const menuItem = findInMenu(currentMenu)
    if (menuItem && menuItem.type === 'group') {
      return { appSlug: slug, resource, viewType: 'appHome', title: menuItem.title }
    }

    return { appSlug: slug, resource, viewType: 'list' }
  }

  return { viewType: 'appHome', appSlug: slug }
}

export default function ReactAppShell(initialConfig) {
  const location = useLocation()
  const theme = useThemeStore()
  
  const { data: ui, isLoading: uiLoading } = useQuery({
    queryKey: ['ui-init'],
    queryFn: () => api.uiInit(),
  })

  const [config, setConfig] = useState(() => ({
    ...initialConfig,
    ...parsePath(window.location.pathname, initialConfig.menu || [])
  }))

  useEffect(() => {
    const pathConfig = parsePath(location.pathname, ui?.menu || initialConfig.menu || [])
    setConfig(prev => {
      const isNewResource = pathConfig.resource !== prev.resource || pathConfig.appSlug !== prev.appSlug;
      const next = { ...prev, ...pathConfig };
      
      // If we moved to a new resource/module home, drop old tiles/widgets
      // so we don't show stale data (e.g. POS tiles when clicking Accounting)
      if (isNewResource) {
        if (!pathConfig.tiles) delete next.tiles;
        if (!pathConfig.widgets) delete next.widgets;
      }
      return next;
    })
  }, [location.pathname, ui?.menu])

  // Fetch resource metadata dynamically if we have a resource but no columns/fields
  const { data: resourceMeta, isLoading: metaLoading } = useQuery({
    queryKey: ['resource-config', config.appSlug, config.resource],
    queryFn: () => api.resourceConfig(`${config.appSlug}/${config.resource}`),
    enabled: !!config.resource && (!config.columns || !config.fields),
  })

  // Merge dynamic metadata into config
  const activeConfig = useMemo(() => {
    if (resourceMeta) {
      return { ...config, ...resourceMeta }
    }
    return config
  }, [config, resourceMeta])

  useEffect(() => {
    theme.applyToDOM()
  }, [theme])

  if (uiLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-aras-bg">
        <div className="w-8 h-8 border-2 border-aras-accent border-t-transparent rounded-none animate-spin"></div>
      </div>
    )
  }

  const menu = ui?.menu || []
  const user = ui?.user || {}
  const { viewType, appSlug, resource, title } = activeConfig

  return (
    <div className="flex h-screen bg-aras-bg text-aras-primary antialiased overflow-hidden">
      <ArasSidebar 
        menu={menu} 
        currentApp={appSlug} 
        currentResource={resource} 
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-aras-bg">
        {/* PRIMARY TOPBAR (System-wide) */}
        <header className="h-14 bg-white border-b border-[#dde3e7] flex items-center justify-between px-6 flex-shrink-0 z-20">
            <div className="flex items-center gap-4 flex-1">
                <div className="relative w-full max-w-md group">
                    <i className="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-[#9aacb8] text-xs group-focus-within:text-aras-accent transition-colors"></i>
                    <input 
                        type="text" 
                        placeholder="Search resources, records, or commands..." 
                        className="w-full bg-[#f8fafb] border border-[#dde3e7] rounded-md py-1.5 pl-9 pr-4 text-xs focus:outline-none focus:ring-1 focus:ring-aras-accent/20 focus:border-aras-accent transition-all"
                    />
                </div>
            </div>

            <div className="flex items-center gap-3">
                <button className="w-8 h-8 flex items-center justify-center text-[#9aacb8] hover:text-aras-accent hover:bg-aras-accent/5 rounded-full transition-all">
                    <i className="fa fa-bell-o text-sm"></i>
                </button>
                <button className="w-8 h-8 flex items-center justify-center text-[#9aacb8] hover:text-aras-accent hover:bg-aras-accent/5 rounded-full transition-all">
                    <i className="fa fa-cog text-sm"></i>
                </button>
                <div className="h-6 w-px bg-[#dde3e7] mx-1"></div>
                <div className="flex items-center gap-3 pl-2">
                    <div className="text-right hidden sm:block">
                        <p className="text-[10px] font-bold text-aras-primary uppercase tracking-wider leading-none mb-1">{user.email || 'Admin User'}</p>
                        <p className="text-[9px] text-[#9aacb8] font-studio-serif italic leading-none">System Administrator</p>
                    </div>
                    <div className="w-8 h-8 rounded-full bg-aras-accent text-white flex items-center justify-center text-[10px] font-bold shadow-sm">
                        {user.email ? user.email.substring(0,2).toUpperCase() : 'AD'}
                    </div>
                </div>
            </div>
        </header>

        {/* SECONDARY TOPBAR (Module-specific) */}
        <ArasTopMenu 
          menu={menu} 
          currentApp={appSlug}
          currentResource={resource}
        />
        
        <main className="flex-1 overflow-auto p-8 relative">
          <div className="max-w-[1600px] mx-auto space-y-2">
            {viewType !== 'appHome' && viewType !== 'dashboard' && viewType !== 'posHome' && (
              <div className="mb-6">
                <h1 className="text-4xl font-studio-serif font-bold text-aras-primary tracking-tight">
                  {activeConfig.title || title}
                </h1>
              </div>
            )}

            <div className="animate-fade-in" key={location.pathname}>
              {resource === 'crm/customer' ? (
                <CustomerPage initialView={viewType} initialId={activeConfig.id} />
              ) : (
                <>
                  {viewType === 'list' && (
                    <ArasListView app={appSlug} resource={resource} columns={activeConfig.columns} title={activeConfig.title} />
                  )}
                  {viewType === 'form' && (
                    <ArasFormView app={appSlug} resource={resource} id={activeConfig.id} fields={activeConfig.fields} childTables={activeConfig.child_tables} redirectOnSave={activeConfig.listUrl} />
                  )}
                  {viewType === 'settings' && (
                    <SettingsPage server_info={activeConfig.server_info} config={activeConfig.config} />
                  )}
                  {viewType === 'appSettings' && (
                    <AppSettingsPage {...activeConfig} />
                  )}
                  {viewType === 'trash' && (
                    <TrashPage />
                  )}
                  {(viewType === 'appHome' || viewType === 'dashboard') && (
                    <ArasAppHome config={activeConfig} />
                  )}
                </>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

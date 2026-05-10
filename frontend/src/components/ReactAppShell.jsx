import React, { useEffect, useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import ArasFullListView from './ArasFullListView'
import ArasFormView from './ArasFormView'
import ArasAppHome from './ArasAppHome'
import CustomerPage from './CustomerPage'
import SettingsPage from './SettingsPage'
...
import TrashPage from './TrashPage'
import { TweakPanel } from './TweakPanel'
import { useThemeStore } from '../lib/themeStore'
import { api } from '../lib/api'

/**
 * Parses the current pathname into a config object.
 * Logic matches Aras URL conventions:
 * /admin/ -> dashboard
 * /admin/settings -> settings
 * /admin/trash -> trash
 * /admin/:appSlug/:resource/list -> list view
 * /admin/:appSlug/:resource/form/:id -> form view
 */
function parsePath(path) {
  const parts = path.split('/').filter(Boolean)
  // parts[0] is 'admin'
  if (parts.length <= 1) return { viewType: 'dashboard' }
  
  const slug = parts[1]
  if (slug === 'settings') return { viewType: 'settings' }
  if (slug === 'trash') return { viewType: 'trash' }
  if (slug === 'dashboard') return { viewType: 'dashboard' }

  // Check for app home: /admin/:app/
  if (parts.length === 2) return { viewType: 'appHome', appSlug: slug }

  // Resource views: /admin/:app/:resource/.../viewType
  // Resource can be multiple parts, e.g. erp/crm/customer
  // We look for 'list' or 'form' as keywords
  const viewIdx = parts.findIndex(p => p === 'list' || p === 'form' || p === 'report')
  if (viewIdx > 2) {
    const resource = parts.slice(2, viewIdx).join('/')
    const viewType = parts[viewIdx]
    const id = viewType === 'form' ? parts[viewIdx + 1] : null
    return { appSlug: slug, resource, viewType, id }
  }

  return { viewType: 'appHome', appSlug: slug }
}

export default function ReactAppShell(initialConfig) {
  const location = useLocation()
  const theme = useThemeStore()
  
  // Local state for the current view configuration
  const [config, setConfig] = useState(initialConfig)

  // Sync config with URL changes
  useEffect(() => {
    const pathConfig = parsePath(location.pathname)
    // Only update if it's a "real" change to avoid flickering
    if (pathConfig.resource !== config.resource || pathConfig.viewType !== config.viewType || pathConfig.id !== config.id) {
      console.log('[shell] route change detected:', pathConfig)
      setConfig(prev => ({ ...prev, ...pathConfig }))
    }
  }, [location.pathname])

  const { data: ui, isLoading: uiLoading } = useQuery({
    queryKey: ['ui-init'],
    queryFn: () => api.uiInit(),
  })

  // Fetch resource metadata dynamically if we have a resource but no columns/fields
  const { data: resourceMeta, isLoading: metaLoading } = useQuery({
    queryKey: ['resource-config', config.resource],
    queryFn: () => api.resourceConfig(config.resource),
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
        <ArasTopMenu 
          menu={menu} 
          currentApp={appSlug}
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
                    <ArasFullListView app={appSlug} resource={resource} columns={activeConfig.columns} title={activeConfig.title} />
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
                  {viewType === 'posHome' && (
                    <PosHomePage terminals={activeConfig.terminals} open_sessions={activeConfig.open_sessions} />
                  )}
                  {viewType === 'report' && (
                    <ReportsPage initialReportId={activeConfig.id} />
                  )}
                  {viewType === 'posAction' && (
                    <PosActionPage 
                      action={activeConfig.action} 
                      terminal={activeConfig.terminal} 
                      session={activeConfig.session} 
                      order_count={activeConfig.order_count}
                      current_user={user}
                    />
                  )}
                  {viewType === 'posShiftReport' && (
                    <PosShiftReportPage data={activeConfig.data} />
                  )}
                  {viewType === 'posSession' && (
                    <PosSessionPage config={activeConfig} />
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

// claude-sonnet-4-6
// TopMenuLayout: full Sidebar (toggle/hide intact) + horizontal submenu strip below topbar.
// Section panel suppressed via hideSection prop — no code deleted from Sidebar.tsx.
import { useEffect, useState, useMemo, type CSSProperties } from 'react'
import { useLocation, Outlet, useNavigate } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'
import { useAras } from '../aras-core/hooks/useAras'
import { useVocabulary } from '../context/VocabularyContext'
import api from '../lib/api'
import type { SidebarApp, MenuItem } from './types'
import { Header } from './components/Header'
import { Sidebar } from './components/Sidebar'
import { Building2 } from 'lucide-react'
import SimpleCombobox from '../aras-core/components/SimpleCombobox'
import { isVisibleMenuItem, filterMenuItems, filterMenuElements } from '../lib/menuUtils'

function normalizeRoutePath(path?: string) {
  if (!path) return '/'
  const normalized = path.startsWith('/') ? path : `/${path}`
  return normalized.length > 1 ? normalized.replace(/\/+$/, '') : normalized
}
function appRoutePath(item?: Pick<SidebarApp, 'name' | 'path'> | null) {
  if (!item) return '/'
  if (item.name === 'settings' || item.path === '/settings') return '/admin/settings'
  return normalizeRoutePath(item.path || `/${item.name}`)
}
function isRouteMatch(currentPath: string, targetPath?: string) {
  const current = normalizeRoutePath(currentPath)
  const target = normalizeRoutePath(targetPath)
  return current === target || current.startsWith(`${target}/`)
}

interface FlatMenuItem extends MenuItem { id: string; groupLabel?: string }

// ── horizontal submenu strip ──────────────────────────────────────────────────
function TopMenuBar({ items, currentPath, isLoading, hasActiveApp }: {
  items: FlatMenuItem[]
  currentPath: string
  isLoading: boolean
  hasActiveApp: boolean
}) {
  const navigate = useNavigate()
  const vocabulary = useVocabulary()

  if (!hasActiveApp) return null

  return (
    <div
      className="flex items-center shrink-0 gap-0.5 px-3 overflow-x-auto arc-scroll"
      style={{ height: 38, borderBottom: '1px solid var(--line)', background: 'var(--bg-2)' }}
    >
      {isLoading ? (
        [80, 100, 70, 90].map((w, i) => (
          <div key={i} style={{
            height: 22, width: w, borderRadius: 'var(--radius)',
            background: 'var(--surface-2)', opacity: 0.5, flexShrink: 0,
          }} />
        ))
      ) : items.map((item) => {
        const target = normalizeRoutePath(item.path)
        const isActive = isRouteMatch(currentPath, target)
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => navigate(target)}
            className="relative flex items-center shrink-0 transition-colors"
            style={{
              height: 28, padding: '0 10px', borderRadius: 'var(--radius)',
              background: isActive ? 'var(--surface-2)' : 'transparent',
              border: isActive ? '1px solid var(--line)' : '1px solid transparent',
              color: isActive ? 'var(--text)' : 'var(--text-3)',
              fontSize: 12.5, fontWeight: isActive ? 600 : 500,
              whiteSpace: 'nowrap',
            }}
          >
            {isActive && (
              <span style={{
                position: 'absolute', left: 6, bottom: -1, right: 6, height: 2,
                background: 'var(--accent)', borderRadius: '2px 2px 0 0',
              }} />
            )}
            {vocabulary.get(item.label || item.name)}
          </button>
        )
      })}
    </div>
  )
}

// ── main layout ───────────────────────────────────────────────────────────────
export default function TopMenuLayout() {
  const [sidebarData, setSidebarData] = useState<SidebarApp[]>([])
  const [menuData, setMenuData] = useState<any>(null)
  const [isLoadingMenu, setIsLoadingMenu] = useState(false)
  const { organizations, activeOrgId, setActiveOrg } = useAuthStore()
  const location = useLocation()
  const { notify } = useAras()
  const { closePanel, cornerMode, density, fontScale, accentColor, iconRailCollapsed, toggleIconRail, dirtyForms, fullWidth } = useUIStore()

  const layoutStyle = {
    '--accent': accentColor,
    '--aras-accent': accentColor,
    '--aras-accent-strong': `color-mix(in srgb, ${accentColor}, black 14%)`,
    '--aras-accent-glow': `color-mix(in srgb, ${accentColor}, transparent 78%)`,
    '--aras-radius': cornerMode === 'square' ? '0px' : '8px',
    '--aras-radius-lg': cornerMode === 'square' ? '0px' : '14px',
    '--aras-density': density === 'compact' ? 0.85 : density === 'comfy' ? 1.1 : '1',
    '--aras-font-scale': String(fontScale / 100),
  } as CSSProperties

  useEffect(() => {
    if (dirtyForms.size === 0) return
    const onBeforeUnload = (e: BeforeUnloadEvent) => { e.preventDefault(); e.returnValue = '' }
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => window.removeEventListener('beforeunload', onBeforeUnload)
  }, [dirtyForms])

  useEffect(() => { closePanel() }, [location.pathname])

  useEffect(() => {
    if (activeOrgId === null && organizations.length > 0) setActiveOrg(organizations[0].id)
  }, [activeOrgId, organizations, setActiveOrg])

  useEffect(() => {
    const fetchSidebar = async () => {
      try {
        const res = await api.get('/sidebar')
        setSidebarData(res.data)
      } catch (err: any) {
        notify(err.message || 'Failed to fetch sidebar', 'error')
      }
    }
    fetchSidebar()
  }, [notify])

  const apps = useMemo(() =>
    sidebarData.filter((item) =>
      isVisibleMenuItem(item) && !item.hide_from_sidebar &&
      item.name !== 'settings' && item.name !== 'help'
    ), [sidebarData])

  const activeApp = useMemo(() => {
    const current = normalizeRoutePath(location.pathname)
    return apps
      .map((app) => ({ app, path: appRoutePath(app) }))
      .filter(({ path }) => isRouteMatch(current, path))
      .sort((a, b) => b.path.length - a.path.length)[0]?.app || null
  }, [location.pathname, apps])

  useEffect(() => {
    if (!activeApp || activeApp.type === 'link') { setMenuData(null); return }
    let cancelled = false
    setIsLoadingMenu(true)
    const menuPath = normalizeRoutePath(activeApp.path || `/${activeApp.name}`).replace(/^\//, '')
    api.get(`/app-menu/${menuPath}`)
      .then((res) => { if (!cancelled) setMenuData(res.data) })
      .catch(() => { if (!cancelled) setMenuData(null) })
      .finally(() => { if (!cancelled) setIsLoadingMenu(false) })
    return () => { cancelled = true }
  }, [activeApp?.name, activeApp?.path, activeApp?.type])

  const flatItems = useMemo<FlatMenuItem[]>(() => {
    if (!menuData) return []
    const elements = filterMenuElements(menuData.menu || [])
    const existingPaths = new Set(elements.map((e: any) => (e as any).path).filter(Boolean))
    const subApps = (menuData.sub_apps || []).filter((sa: any) => !existingPaths.has(sa.path))
    const allElements = [...elements, ...subApps.map((sa: any) => ({ ...sa, type: 'app_link' }))]
    const items: FlatMenuItem[] = []
    allElements.forEach((el: any) => {
      const label = (el.label || '').toLowerCase()
      const name = (el.name || '').toLowerCase()
      if (label.includes('setting') || name.includes('setting') || label.includes('admin') || name.includes('admin')) return
      if (el.type === 'group') {
        filterMenuItems(el.items || []).forEach((i: MenuItem) => {
          const il = (i.label || '').toLowerCase()
          const inm = (i.name || '').toLowerCase()
          if (il.includes('setting') || inm.includes('setting') || il.includes('admin') || inm.includes('admin')) return
          items.push({ ...i, id: i.path || i.name, groupLabel: el.label })
        })
      } else {
        items.push({ ...el, id: el.path || el.name, groupLabel: 'General' })
      }
    })
    return items
  }, [menuData])

  return (
    <div className="arc arc-bg arc-dotgrid h-screen w-full overflow-hidden flex font-sans antialiased" style={layoutStyle}>
      <Sidebar
        sidebarData={sidebarData}
        currentPath={location.pathname}
        hideSection
      />
      {iconRailCollapsed && (
        <button
          onClick={toggleIconRail}
          aria-label="Show sidebar"
          className="fixed left-0 top-1/2 -translate-y-1/2 flex items-center justify-center text-[var(--text-3)] hover:text-[var(--text)] transition-colors"
          style={{
            width: 14, height: 56,
            background: 'var(--bg-2)',
            border: '1px solid var(--line)',
            borderLeft: 'none',
            borderRadius: '0 8px 8px 0',
            zIndex: 60, cursor: 'pointer',
          }}
        >
          <ChevronRight size={12} />
        </button>
      )}

      <div id="content-wrapper" className="flex flex-col flex-1 min-w-0 h-full overflow-hidden relative z-10">
        <Header>
          <div className="z-50 flex items-center gap-2 max-sm:hidden">
            <Building2 size={13} className="text-[var(--text-3)]" />
            {organizations.length > 1 ? (
              <SimpleCombobox
                width={180}
                options={[
                  { label: 'All Organizations', value: -1 },
                  ...organizations.map((org) => ({ label: org.name, value: org.id })),
                ]}
                value={activeOrgId ?? -1}
                onChange={(val) => setActiveOrg(Number(val))}
                placeholder="Select Organization"
              />
            ) : null}
          </div>
        </Header>

        <TopMenuBar
          items={flatItems}
          currentPath={location.pathname}
          isLoading={isLoadingMenu}
          hasActiveApp={!!activeApp && activeApp.type !== 'link'}
        />

        <main id="main-content" className={`flex-1 min-w-0 relative flex flex-col arc-scroll ${fullWidth ? 'overflow-hidden' : 'overflow-y-auto'}`}>
          <div className="flex-1 flex flex-col min-h-0">
            <div className={fullWidth
              ? 'flex-1 min-h-0 relative w-full flex flex-col'
              : 'flex-1 max-sm:overflow-visible relative w-full max-w-[1280px] mx-auto px-4 md:px-6 lg:px-8 py-5'}>
              <Outlet context={{ sidebarData }} />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

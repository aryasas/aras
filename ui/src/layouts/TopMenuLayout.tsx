import { useEffect, useState, useMemo, type CSSProperties } from 'react'
import { useLocation, Outlet, useNavigate } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'
import { useAras } from '../aras-core/hooks/useAras'
import { useVocabulary } from '../context/VocabularyContext'
import api from '../lib/api'
import type { SidebarApp } from './types'
import { Header } from './components/Header'
import { Sidebar } from './components/Sidebar'
import { isVisibleMenuItem } from '../lib/menuUtils'
import { SortableList, DragHandle } from '../aras-core/components/SortableList'
import { isRouteMatch, normalizeRoutePath, type FlatMenuItem } from '../lib/navUtils'
import { useAppMenu } from './hooks/useAppMenu'
import WorkspaceSwitcher from './components/WorkspaceSwitcher'

// ── horizontal submenu strip ──────────────────────────────────────────────────
function TopMenuBar({ items, currentPath, isLoading, hasActiveApp, activeAppName }: {
  items: FlatMenuItem[]
  currentPath: string
  isLoading: boolean
  hasActiveApp: boolean
  activeAppName: string | null
}) {
  const navigate = useNavigate()
  const vocabulary = useVocabulary()
  const setSubmenuOrder = useUIStore((state) => state.setSubmenuOrder)

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
      ) : (
        <SortableList
          items={items}
          onReorder={(next) => {
            if (!activeAppName) return
            setSubmenuOrder(activeAppName, next.map((item) => item.id))
          }}
          className="flex-row gap-0.5"
          itemClassName="shrink-0"
          overlayClassName="shrink-0"
          renderItem={(item) => {
            const target = normalizeRoutePath(item.path)
            const isActive = isRouteMatch(currentPath, target)
            return (
              <div className="group relative flex items-center shrink-0">
                <button
                  type="button"
                  onClick={() => navigate(target)}
                  className="relative flex items-center shrink-0 transition-colors"
                  style={{
                    height: 28, padding: '0 28px 0 10px', borderRadius: 'var(--radius)',
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
                <span className="absolute right-1.5 top-1/2 -translate-y-1/2 opacity-0 transition-opacity group-hover:opacity-100">
                  <DragHandle className="h-5 w-5 rounded text-[var(--text-3)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]" />
                </span>
              </div>
            )
          }}
        />
      )}
    </div>
  )
}

// ── main layout ───────────────────────────────────────────────────────────────
export default function TopMenuLayout() {
  const [sidebarData, setSidebarData] = useState<SidebarApp[]>([])
  const organizations = useAuthStore((state) => state.organizations)
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

  // Template Builder runtime for the layout that is actually mounted by App.tsx.
  // Applies saved overrides on normal pages and installs pick/drag tools inside builder previews.
  useEffect(() => {
    let cancelled = false
    const path = location.pathname || '/'
    api.get(`/dev/dev/style-overrides?path=${encodeURIComponent(path)}`)
      .then((res) => {
        if (cancelled) return
        const rows: Array<{ selector: string; css_json: Record<string, any>; hidden: boolean; text_override: string | null }> = Array.isArray(res.data) ? res.data : []
        const cssParts: string[] = []
        for (const row of rows) {
          const decls: string[] = []
          if (row.hidden) decls.push('display: none !important')
          for (const [key, value] of Object.entries(row.css_json || {})) {
            if (value == null || value === '') continue
            if (key.startsWith('@media') && typeof value === 'object' && !Array.isArray(value)) {
              const mediaDecls = Object.entries(value)
                .filter(([, nestedValue]) => nestedValue != null && nestedValue !== '')
                .map(([nestedKey, nestedValue]) => `${nestedKey}: ${nestedValue}`)
              if (mediaDecls.length) cssParts.push(`${key} { ${row.selector} { ${mediaDecls.join('; ')} } }`)
              continue
            }
            decls.push(`${key}: ${value}`)
          }
          if (decls.length) cssParts.push(`${row.selector} { ${decls.join('; ')} }`)
        }
        let tag = document.getElementById('aras-style-overrides') as HTMLStyleElement | null
        if (!tag) {
          tag = document.createElement('style')
          tag.id = 'aras-style-overrides'
          document.head.appendChild(tag)
        }
        tag.textContent = cssParts.join('\n')

        const applyText = () => {
          for (const row of rows) {
            if (!row.text_override) continue
            try {
              document.querySelectorAll(row.selector).forEach((el) => {
                const target = el as HTMLElement
                const overrideText = row.text_override || ''
                if (target.dataset.arasTextApplied === overrideText) return
                target.textContent = overrideText
                target.dataset.arasTextApplied = overrideText
              })
            } catch { /* ignore invalid selector */ }
          }
        }
        applyText()
        window.setTimeout(applyText, 250)
      })
      .catch(() => { /* overrides are non-critical */ })
    return () => { cancelled = true }
  }, [location.pathname])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const params = new URLSearchParams(window.location.search)
    if (params.get('__builder_preview') !== '1') return
    if (window.top === window.self) return

    const computeSelector = (el: Element): string => {
      if (el.id) return `#${CSS.escape(el.id)}`
      const arasId = (el as HTMLElement).dataset?.arasId
      if (arasId) return `[data-aras-id="${arasId}"]`
      const testId = (el as HTMLElement).dataset?.testid
      if (testId) return `[data-testid="${testId}"]`
      const path: string[] = []
      let node: Element | null = el
      let depth = 0
      while (node && node.nodeType === 1 && depth < 7) {
        let segment = node.tagName.toLowerCase()
        const parent = node.parentElement
        if (parent) {
          const siblings = Array.from(parent.children).filter((child) => child.tagName === node!.tagName)
          if (siblings.length > 1) segment += `:nth-of-type(${siblings.indexOf(node) + 1})`
        }
        path.unshift(segment)
        node = node.parentElement
        depth++
      }
      return path.join(' > ')
    }

    const outline = document.createElement('div')
    outline.style.cssText = 'position:fixed;pointer-events:none;border:2px solid #2563eb;background:rgba(37,99,235,0.08);z-index:2147483647;transition:all 0.05s;border-radius:4px;'
    outline.style.display = 'none'
    document.body.appendChild(outline)

    let editMode = params.get('__builder_edit') === '1'
    let toolMode = 'select'
    let dragSource: Element | null = null

    const enableDrag = () => {
      if (!editMode) return
      document.body.setAttribute('data-aras-edit-mode', '1')
      document.body.setAttribute('data-aras-builder-tool', toolMode)
      document.querySelectorAll('*').forEach((el) => {
        const target = el as HTMLElement
        if (!target.hasAttribute('draggable')) target.draggable = true
      })
    }

    const disableDrag = () => {
      document.body.removeAttribute('data-aras-edit-mode')
      document.body.removeAttribute('data-aras-builder-tool')
    }

    const move = (event: MouseEvent) => {
      if (!editMode) { outline.style.display = 'none'; return }
      const target = event.target as Element | null
      if (!target || target === outline) return
      const rect = target.getBoundingClientRect()
      outline.style.display = 'block'
      outline.style.left = `${rect.left}px`
      outline.style.top = `${rect.top}px`
      outline.style.width = `${rect.width}px`
      outline.style.height = `${rect.height}px`
    }

    const click = (event: MouseEvent) => {
      if (!editMode || toolMode !== 'select') return
      event.preventDefault()
      event.stopPropagation()
      const target = event.target as Element | null
      if (!target) return
      const computed = window.getComputedStyle(target)
      window.parent.postMessage({
        type: 'aras-builder-pick',
        payload: {
          selector: computeSelector(target),
          tag: target.tagName.toLowerCase(),
          text: (target.textContent || '').slice(0, 200),
          styles: {
            color: computed.color,
            backgroundColor: computed.backgroundColor,
            fontSize: computed.fontSize,
            fontWeight: computed.fontWeight,
            padding: computed.padding,
            margin: computed.margin,
            borderRadius: computed.borderRadius,
            border: computed.border,
            display: computed.display,
            textAlign: computed.textAlign,
          },
        },
      }, '*')
    }

    const blockNav = (event: Event) => {
      if (!editMode) return
      const target = event.target as Element | null
      if (target?.closest('a,button,[role="button"]')) {
        event.preventDefault()
        event.stopPropagation()
      }
    }

    const onDragStart = (event: DragEvent) => {
      if (!editMode || (toolMode !== 'reorder' && !event.altKey)) return
      dragSource = event.target as Element
      try { event.dataTransfer?.setData('text/plain', 'aras-reorder') } catch {}
    }

    const onDragOver = (event: DragEvent) => {
      if (editMode && dragSource) event.preventDefault()
    }

    const onDrop = (event: DragEvent) => {
      if (!editMode || !dragSource) return
      event.preventDefault()
      const target = event.target as Element | null
      if (!target || target === dragSource) { dragSource = null; return }
      const parent = dragSource.parentElement
      if (!parent || !parent.contains(target)) { dragSource = null; return }
      const targetChild = Array.from(parent.children).find((child) => child === target || child.contains(target))
      if (!targetChild) { dragSource = null; return }
      const siblings = Array.from(parent.children)
      const fromIndex = siblings.indexOf(dragSource)
      const toIndex = siblings.indexOf(targetChild)
      if (fromIndex < 0 || toIndex < 0) { dragSource = null; return }
      const next = siblings.slice()
      next.splice(toIndex, 0, next.splice(fromIndex, 1)[0])
      window.parent.postMessage({
        type: 'aras-builder-reorder',
        patches: next.map((el, index) => ({
          selector: computeSelector(el),
          css_json: { order: String(index) },
          label: `Reorder ${index + 1}`,
        })),
      }, '*')
      dragSource = null
    }

    const onParentMessage = (event: MessageEvent) => {
      if (!event.data || typeof event.data !== 'object') return
      if (event.data.type === 'aras-builder-set-mode') {
        editMode = Boolean(event.data.edit)
        toolMode = event.data.tool === 'reorder' ? 'reorder' : 'select'
        if (editMode) enableDrag()
        else { disableDrag(); outline.style.display = 'none' }
      }
      if (event.data.type === 'aras-builder-reload') window.location.reload()
    }

    document.addEventListener('mousemove', move, true)
    document.addEventListener('click', click, true)
    document.addEventListener('click', blockNav, true)
    document.addEventListener('dragstart', onDragStart, true)
    document.addEventListener('dragover', onDragOver, true)
    document.addEventListener('drop', onDrop, true)
    window.addEventListener('message', onParentMessage)

    if (editMode) enableDrag()
    window.parent.postMessage({ type: 'aras-builder-ready', path: window.location.pathname }, '*')

    return () => {
      document.removeEventListener('mousemove', move, true)
      document.removeEventListener('click', click, true)
      document.removeEventListener('click', blockNav, true)
      document.removeEventListener('dragstart', onDragStart, true)
      document.removeEventListener('dragover', onDragOver, true)
      document.removeEventListener('drop', onDrop, true)
      window.removeEventListener('message', onParentMessage)
      outline.remove()
      disableDrag()
    }
  }, [])

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
  const { activeApp, isLoadingMenu, orderedItems } = useAppMenu(apps, location.pathname)

  return (
    <div className="arc arc-bg arc-dotgrid h-screen w-full overflow-hidden flex font-sans antialiased" style={layoutStyle}>
      <Sidebar sidebarData={sidebarData} currentPath={location.pathname} />
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
          {organizations.length > 0 ? <WorkspaceSwitcher /> : null}
        </Header>

        <TopMenuBar
          items={orderedItems}
          currentPath={location.pathname}
          isLoading={isLoadingMenu}
          hasActiveApp={!!activeApp && activeApp.type !== 'link'}
          activeAppName={activeApp?.name || null}
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

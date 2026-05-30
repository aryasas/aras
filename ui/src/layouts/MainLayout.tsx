// claude-opus-4-7
// ARC shell: full-bleed bg + dot-grid, ARC sidebar on the left, topbar, content frame.
import { useEffect, useState, type CSSProperties } from 'react'
import { useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../lib/api'
import type { SidebarApp } from './types'
import { Sidebar } from './components/Sidebar'
import { Header } from './components/Header'
import { Building2, ChevronRight } from 'lucide-react'
import { useAras } from '../aras-core/hooks/useAras'
import { useUIStore } from '../store/uiStore'
import SimpleCombobox from '../aras-core/components/SimpleCombobox'

export default function MainLayout() {
  const [sidebarData, setSidebarData] = useState<SidebarApp[]>([])
  const { organizations, activeOrgId, setActiveOrg } = useAuthStore()
  const location = useLocation()
const { notify } = useAras()
  const { closePanel, cornerMode, density, fontScale, accentColor, iconRailCollapsed, toggleIconRail, dirtyForms } = useUIStore()

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

  // Tab close / refresh guard. In-app navigation guard requires a data router (createBrowserRouter);
  // current app uses BrowserRouter, so useBlocker is unavailable. Re-enable when router is migrated.
  useEffect(() => {
    if (dirtyForms.size === 0) return
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => window.removeEventListener('beforeunload', onBeforeUnload)
  }, [dirtyForms])

  useEffect(() => { closePanel() }, [location.pathname])

  // claude-opus-4-7
  // Universal style-override layer: fetch overrides matching the current route,
  // inject as a single <style> tag, apply hidden/text overrides via attribute selectors.
  useEffect(() => {
    let cancelled = false
    const path = location.pathname || '/'
    api.get(`/style-overrides?path=${encodeURIComponent(path)}`)
      .then((res) => {
        if (cancelled) return
        const rows: Array<{ selector: string; css_json: Record<string, string>; hidden: boolean; text_override: string | null }> = Array.isArray(res.data) ? res.data : []
        const cssParts: string[] = []
        for (const row of rows) {
          const decls: string[] = []
          if (row.hidden) decls.push('display: none !important')
          for (const [k, v] of Object.entries(row.css_json || {})) {
            if (v == null || v === '') continue
            decls.push(`${k}: ${v}`)
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
        // Text overrides applied after paint
        const applyText = () => {
          for (const row of rows) {
            if (!row.text_override) continue
            try {
              document.querySelectorAll(row.selector).forEach((el) => {
                if ((el as HTMLElement).dataset.arasTextApplied === row.text_override) return
                ;(el as HTMLElement).textContent = row.text_override
                ;(el as HTMLElement).dataset.arasTextApplied = row.text_override ?? ''
              })
            } catch { /* ignore invalid selector */ }
          }
        }
        applyText()
        const t = window.setTimeout(applyText, 250)
        return () => window.clearTimeout(t)
      })
      .catch(() => { /* silent — overrides are non-critical */ })
    return () => { cancelled = true }
  }, [location.pathname])

  // Builder preview mode — when shown inside an iframe with __builder_preview=1,
  // install a hover/click picker that posts the chosen selector to the parent.
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
      while (node && node.nodeType === 1 && depth < 6) {
        let seg = node.tagName.toLowerCase()
        const parent = node.parentElement
        if (parent) {
          const sibs = Array.from(parent.children).filter((c) => c.tagName === node!.tagName)
          if (sibs.length > 1) {
            const idx = sibs.indexOf(node) + 1
            seg += `:nth-of-type(${idx})`
          }
        }
        path.unshift(seg)
        node = node.parentElement
        depth++
      }
      return path.join(' > ')
    }

    const outline = document.createElement('div')
    outline.style.cssText = 'position:fixed;pointer-events:none;border:2px solid #6366f1;background:rgba(99,102,241,0.08);z-index:2147483647;transition:all 0.05s;border-radius:3px;'
    outline.style.display = 'none'
    document.body.appendChild(outline)

    let editMode = params.get('__builder_edit') === '1'
    let lastTarget: Element | null = null

    // claude-opus-4-7
    // CSS-order DnD for arbitrary elements: drag any element to reorder among its siblings inside a flex/grid parent.
    // Writes `order: N` per sibling selector into the override layer via the parent window.
    let dragSrc: Element | null = null

    const move = (e: MouseEvent) => {
      if (!editMode) { outline.style.display = 'none'; return }
      const t = e.target as Element | null
      if (!t || t === outline) return
      lastTarget = t
      const r = t.getBoundingClientRect()
      outline.style.display = 'block'
      outline.style.left = `${r.left}px`
      outline.style.top = `${r.top}px`
      outline.style.width = `${r.width}px`
      outline.style.height = `${r.height}px`
    }
    const click = (e: MouseEvent) => {
      if (!editMode) return
      e.preventDefault()
      e.stopPropagation()
      const t = e.target as Element | null
      if (!t) return
      const sel = computeSelector(t)
      const cs = window.getComputedStyle(t as Element)
      const summary = {
        selector: sel,
        tag: t.tagName.toLowerCase(),
        text: (t.textContent || '').slice(0, 200),
        styles: {
          color: cs.color,
          backgroundColor: cs.backgroundColor,
          fontSize: cs.fontSize,
          fontWeight: cs.fontWeight,
          padding: cs.padding,
          margin: cs.margin,
          borderRadius: cs.borderRadius,
          border: cs.border,
          display: cs.display,
          textAlign: cs.textAlign,
        },
      }
      window.parent.postMessage({ type: 'aras-builder-pick', payload: summary }, '*')
    }

    // Intercept link/button navigation in edit mode so picks don't trigger app navigation.
    const blockNav = (e: Event) => {
      if (!editMode) return
      const t = e.target as Element | null
      if (!t) return
      const a = t.closest('a,button,[role="button"]')
      if (a) { e.preventDefault(); e.stopPropagation() }
    }

    // CSS-order DnD — handled via native HTML5 drag, but only on container children when alt-key drag is used.
    const onDragStart = (e: DragEvent) => {
      if (!editMode || !e.altKey) return
      dragSrc = e.target as Element
      try { e.dataTransfer?.setData('text/plain', 'aras-reorder') } catch {}
    }
    const onDragOver = (e: DragEvent) => { if (editMode && dragSrc) e.preventDefault() }
    const onDrop = (e: DragEvent) => {
      if (!editMode || !dragSrc) return
      e.preventDefault()
      const target = e.target as Element | null
      if (!target || target === dragSrc) { dragSrc = null; return }
      const parent = dragSrc.parentElement
      if (!parent || !parent.contains(target)) { dragSrc = null; return }
      const targetChild = Array.from(parent.children).find((c) => c === target || c.contains(target))
      if (!targetChild) { dragSrc = null; return }
      const siblings = Array.from(parent.children)
      const fromIdx = siblings.indexOf(dragSrc)
      const toIdx = siblings.indexOf(targetChild)
      if (fromIdx < 0 || toIdx < 0) { dragSrc = null; return }
      const newOrder = siblings.slice()
      newOrder.splice(toIdx, 0, newOrder.splice(fromIdx, 1)[0])
      const patches = newOrder.map((el, i) => ({
        selector: computeSelector(el),
        css_json: { order: String(i) },
        label: `Reorder ${i + 1}`,
      }))
      window.parent.postMessage({ type: 'aras-builder-reorder', patches }, '*')
      dragSrc = null
    }

    // Make all elements draggable in edit mode (alt+drag to reorder)
    const enableDrag = () => {
      if (!editMode) return
      document.body.setAttribute('data-aras-edit-mode', '1')
      document.querySelectorAll('*').forEach((el) => {
        if (!(el as HTMLElement).hasAttribute('draggable')) (el as HTMLElement).draggable = true
      })
    }
    const disableDrag = () => {
      document.body.removeAttribute('data-aras-edit-mode')
    }

    document.addEventListener('mousemove', move, true)
    document.addEventListener('click', click, true)
    document.addEventListener('click', blockNav, true)
    document.addEventListener('dragstart', onDragStart, true)
    document.addEventListener('dragover', onDragOver, true)
    document.addEventListener('drop', onDrop, true)

    if (editMode) enableDrag()

    // Listen for mode changes from parent
    const onParentMsg = (e: MessageEvent) => {
      if (!e.data || typeof e.data !== 'object') return
      if (e.data.type === 'aras-builder-set-mode') {
        editMode = !!e.data.edit
        if (editMode) enableDrag()
        else { disableDrag(); outline.style.display = 'none' }
      }
      if (e.data.type === 'aras-builder-reload') window.location.reload()
    }
    window.addEventListener('message', onParentMsg)

    window.parent.postMessage({ type: 'aras-builder-ready', path: window.location.pathname }, '*')
    return () => {
      document.removeEventListener('mousemove', move, true)
      document.removeEventListener('click', click, true)
      document.removeEventListener('click', blockNav, true)
      document.removeEventListener('dragstart', onDragStart, true)
      document.removeEventListener('dragover', onDragOver, true)
      document.removeEventListener('drop', onDrop, true)
      window.removeEventListener('message', onParentMsg)
      outline.remove()
      disableDrag()
      void lastTarget
    }
  }, [])

  useEffect(() => {
    if (activeOrgId === null && organizations.length > 0) {
      setActiveOrg(organizations[0].id)
    }
  }, [activeOrgId, organizations, setActiveOrg])

  useEffect(() => {
    const fetchSidebar = async () => {
      try {
        const res = await api.get('/menu').catch(() => api.get('/sidebar'))
        setSidebarData(res.data)
      } catch (err: any) {
        notify(err.message || 'Failed to fetch sidebar', 'error')
      }
    }
    fetchSidebar()
  }, [notify])

  return (
    <div className="arc arc-bg arc-dotgrid h-screen w-full overflow-hidden flex font-sans antialiased" style={layoutStyle}>
      <Sidebar
        sidebarData={sidebarData}
        currentPath={location.pathname}
      />
      {iconRailCollapsed && (
        <button
          onClick={toggleIconRail}
          aria-label="Show sidebar"
          className="fixed left-0 top-1/2 -translate-y-1/2 flex items-center justify-center text-[var(--text-3)] hover:text-[var(--text)] transition-colors"
          style={{
            width: 14,
            height: 56,
            background: 'var(--bg-2)',
            border: '1px solid var(--line)',
            borderLeft: 'none',
            borderRadius: '0 8px 8px 0',
            zIndex: 60,
            cursor: 'pointer',
          }}
        >
          <ChevronRight size={12} />
        </button>
      )}

      <div id="content-wrapper"
           className="flex flex-col flex-1 min-w-0 h-full overflow-hidden relative z-10">
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

        <main id="main-content" className="flex-1 overflow-y-auto min-w-0 relative flex flex-col arc-scroll">
          <div className="flex-1 flex flex-col">
            <div className="flex-1 max-sm:overflow-visible relative w-full max-w-[1280px] mx-auto px-4 md:px-6 lg:px-8 py-5">
              <Outlet context={{ sidebarData }} />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

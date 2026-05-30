// claude-opus-4-7
// Universal template editor — Claude-style edit mode.
// Six features in one screen:
//   1. Field DnD on metadata-driven routes (DynamicForm reads __builder_edit=1, drag fields, POST /field-reorder)
//   2. Edit Mode toggle — when off, iframe is a normal preview; when on, picker + DnD activate
//   3. Element-aware inspector — controls switch based on picked.tag (img / button / heading / container)
//   4. AI edit box — natural-language prompt → CSS patch via /style-overrides/ai
//   5. Undo history — list recent overrides, click to delete-revert
//   6. CSS-order DnD — alt+drag any element inside the iframe to reorder siblings via order: N
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAras } from '../aras-core/hooks/useAras'
import api from '../lib/api'

type Picked = {
  selector: string
  tag: string
  text: string
  styles: Record<string, string>
}

type Override = {
  id?: number
  scope: string
  selector: string
  label?: string | null
  css_json: Record<string, string>
  text_override?: string | null
  hidden?: boolean
  updated_at?: string | null
}

const BREAKPOINTS: Record<string, number> = { desktop: 1280, tablet: 820, mobile: 390 }

type StyleField = { key: string; label: string; type: 'color' | 'text' | 'select'; options?: string[] }

// Element-aware control sets
const CONTROLS_BY_TAG: Record<string, StyleField[]> = {
  img: [
    { key: 'object-fit', label: 'Fit', type: 'select', options: ['', 'cover', 'contain', 'fill', 'none', 'scale-down'] },
    { key: 'opacity', label: 'Opacity', type: 'text' },
    { key: 'border-radius', label: 'Radius', type: 'text' },
    { key: 'width', label: 'Width', type: 'text' },
    { key: 'height', label: 'Height', type: 'text' },
  ],
  button: [
    { key: 'color', label: 'Text color', type: 'color' },
    { key: 'background-color', label: 'Background', type: 'color' },
    { key: 'padding', label: 'Padding', type: 'text' },
    { key: 'border-radius', label: 'Radius', type: 'text' },
    { key: 'border', label: 'Border', type: 'text' },
    { key: 'font-weight', label: 'Weight', type: 'text' },
  ],
  heading: [
    { key: 'color', label: 'Color', type: 'color' },
    { key: 'font-size', label: 'Size', type: 'text' },
    { key: 'font-weight', label: 'Weight', type: 'text' },
    { key: 'letter-spacing', label: 'Tracking', type: 'text' },
    { key: 'text-align', label: 'Align', type: 'select', options: ['', 'left', 'center', 'right'] },
  ],
  text: [
    { key: 'color', label: 'Color', type: 'color' },
    { key: 'font-size', label: 'Size', type: 'text' },
    { key: 'font-weight', label: 'Weight', type: 'text' },
    { key: 'line-height', label: 'Line height', type: 'text' },
    { key: 'text-align', label: 'Align', type: 'select', options: ['', 'left', 'center', 'right'] },
  ],
  container: [
    { key: 'background-color', label: 'Background', type: 'color' },
    { key: 'padding', label: 'Padding', type: 'text' },
    { key: 'margin', label: 'Margin', type: 'text' },
    { key: 'border', label: 'Border', type: 'text' },
    { key: 'border-radius', label: 'Radius', type: 'text' },
    { key: 'display', label: 'Display', type: 'select', options: ['', 'block', 'flex', 'grid', 'inline-block', 'none'] },
    { key: 'gap', label: 'Gap', type: 'text' },
  ],
}

function controlsFor(tag: string): StyleField[] {
  if (tag === 'img') return CONTROLS_BY_TAG.img
  if (tag === 'button' || tag === 'a') return CONTROLS_BY_TAG.button
  if (/^h[1-6]$/.test(tag)) return CONTROLS_BY_TAG.heading
  if (['p', 'span', 'label', 'li'].includes(tag)) return CONTROLS_BY_TAG.text
  return CONTROLS_BY_TAG.container
}

function toRgbHex(rgb: string): string {
  const m = rgb.match(/rgba?\(([^)]+)\)/)
  if (!m) return rgb.startsWith('#') ? rgb : '#000000'
  const parts = m[1].split(',').map((s) => parseInt(s.trim(), 10))
  const [r, g, b] = parts
  return '#' + [r, g, b].map((n) => (isNaN(n) ? 0 : n).toString(16).padStart(2, '0')).join('')
}

function camelToKebab(s: string) {
  return s.replace(/([A-Z])/g, '-$1').toLowerCase()
}

export default function TemplateBuilder() {
  const { notify } = useAras()
  const [searchParams, setSearchParams] = useSearchParams()
  const iframeRef = useRef<HTMLIFrameElement | null>(null)

  const rawFrom = searchParams.get('from') || '/'
  const fromPath = rawFrom.startsWith('/') ? rawFrom : `/${rawFrom}`
  const [editMode, setEditMode] = useState(true)
  const previewSrc = useMemo(() => {
    const sep = fromPath.includes('?') ? '&' : '?'
    return `${fromPath}${sep}__builder_preview=1${editMode ? '&__builder_edit=1' : ''}`
  }, [fromPath, editMode])

  const [picked, setPicked] = useState<Picked | null>(null)
  const [draft, setDraft] = useState<Record<string, string>>({})
  const [hidden, setHidden] = useState(false)
  const [textOverride, setTextOverride] = useState<string>('')
  const [textEnabled, setTextEnabled] = useState(false)
  const [scope, setScope] = useState<string>('global')
  const [breakpoint, setBreakpoint] = useState<'desktop' | 'tablet' | 'mobile'>('desktop')
  const [overrides, setOverrides] = useState<Override[]>([])
  const [history, setHistory] = useState<Override[]>([])
  const [saving, setSaving] = useState(false)
  const [routeInput, setRouteInput] = useState(rawFrom)
  const [aiPrompt, setAiPrompt] = useState('')
  const [aiBusy, setAiBusy] = useState(false)

  const loadOverrides = useCallback(async () => {
    try {
      const res = await api.get(`/style-overrides?path=${encodeURIComponent(fromPath)}`)
      setOverrides(Array.isArray(res.data) ? res.data : [])
    } catch {
      setOverrides([])
    }
    try {
      const h = await api.get(`/style-overrides/history?path=${encodeURIComponent(fromPath)}&limit=15`)
      setHistory(Array.isArray(h.data) ? h.data : [])
    } catch {
      setHistory([])
    }
  }, [fromPath])

  useEffect(() => { loadOverrides() }, [loadOverrides])

  // Tell iframe whenever editMode flips
  useEffect(() => {
    const ifr = iframeRef.current
    if (!ifr || !ifr.contentWindow) return
    ifr.contentWindow.postMessage({ type: 'aras-builder-set-mode', edit: editMode }, '*')
  }, [editMode])

  // Receive picks, field-reorder events, and CSS-order DnD patches
  useEffect(() => {
    const onMessage = async (e: MessageEvent) => {
      if (!e.data || typeof e.data !== 'object') return
      if (e.data.type === 'aras-builder-pick') {
        const p = e.data.payload as Picked
        setPicked(p)
        const existing = overrides.find((o) => o.selector === p.selector)
        if (existing) {
          setDraft({ ...existing.css_json })
          setHidden(Boolean(existing.hidden))
          setTextOverride(existing.text_override || '')
          setTextEnabled(Boolean(existing.text_override))
        } else {
          setDraft({})
          setHidden(false)
          setTextOverride(p.text)
          setTextEnabled(false)
        }
      }
      if (e.data.type === 'aras-builder-reordered') {
        await loadOverrides()
        notify('Fields reordered', 'success')
        reloadIframe()
      }
      if (e.data.type === 'aras-builder-reorder') {
        const patches = e.data.patches as Array<{ selector: string; css_json: Record<string, string>; label: string }>
        try {
          await Promise.all(patches.map((p) =>
            api.post('/style-overrides', { scope, selector: p.selector, css_json: p.css_json, label: p.label })
          ))
          notify(`Reordered ${patches.length} elements`, 'success')
          await loadOverrides()
          reloadIframe()
        } catch (err: any) {
          notify(err?.message || 'Reorder save failed', 'error')
        }
      }
    }
    window.addEventListener('message', onMessage)
    return () => window.removeEventListener('message', onMessage)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [overrides, scope])

  const reloadIframe = useCallback(() => {
    if (iframeRef.current) iframeRef.current.src = previewSrc
  }, [previewSrc])

  const handleSave = useCallback(async () => {
    if (!picked) return
    setSaving(true)
    try {
      await api.post('/style-overrides', {
        scope,
        selector: picked.selector,
        label: picked.text?.slice(0, 80) || picked.tag,
        css_json: draft,
        hidden,
        text_override: textEnabled ? textOverride : null,
      })
      notify('Override saved', 'success')
      await loadOverrides()
      reloadIframe()
    } catch (err: any) {
      notify(err?.message || 'Failed to save', 'error')
    } finally {
      setSaving(false)
    }
  }, [draft, hidden, loadOverrides, notify, picked, reloadIframe, scope, textEnabled, textOverride])

  const handleAiEdit = useCallback(async () => {
    if (!picked || !aiPrompt.trim()) return
    setAiBusy(true)
    try {
      const computed = Object.fromEntries(
        Object.entries(picked.styles).map(([k, v]) => [camelToKebab(k), v])
      )
      const res = await api.post('/style-overrides/ai', {
        selector: picked.selector,
        tag: picked.tag,
        computed,
        instruction: aiPrompt,
      })
      const patch = res.data?.css_json || {}
      setDraft((prev) => ({ ...prev, ...patch }))
      notify(`AI suggested ${Object.keys(patch).length} properties — review then Save`, 'success')
    } catch (err: any) {
      notify(err?.response?.data?.detail || err?.message || 'AI edit failed', 'error')
    } finally {
      setAiBusy(false)
    }
  }, [aiPrompt, notify, picked])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await api.delete(`/style-overrides/${id}`)
      notify('Reverted', 'success')
      await loadOverrides()
      reloadIframe()
    } catch (err: any) {
      notify(err?.message || 'Failed to revert', 'error')
    }
  }, [loadOverrides, notify, reloadIframe])

  const updateDraft = (k: string, v: string) => {
    setDraft((prev) => {
      const next = { ...prev }
      if (!v) delete next[k]
      else next[k] = v
      return next
    })
  }

  const canvasWidth = BREAKPOINTS[breakpoint]
  const styleFields = picked ? controlsFor(picked.tag) : []

  const goToRoute = (path: string) => {
    setSearchParams({ from: path })
    setPicked(null)
    setDraft({})
  }

  return (
    <div className="flex h-full min-h-[calc(100vh-120px)] flex-col gap-3 p-3">
      {/* Topbar */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-[var(--line)] bg-[var(--bg-2)] px-4 py-2.5">
        <span className="text-xs font-semibold uppercase tracking-wide text-[var(--text-3)]">Editing</span>
        <form
          onSubmit={(e) => { e.preventDefault(); goToRoute(routeInput) }}
          className="flex items-center gap-2"
        >
          <input
            value={routeInput}
            onChange={(e) => setRouteInput(e.target.value)}
            placeholder="/notes/note"
            className="w-72 rounded-md border border-[var(--line)] bg-[var(--bg)] px-2.5 py-1 text-sm"
          />
          <button type="submit" className="rounded-md border border-[var(--line)] bg-[var(--bg)] px-3 py-1 text-sm hover:bg-[var(--bg-3)]">
            Open
          </button>
        </form>

        {/* Edit Mode toggle */}
        <label className={`flex cursor-pointer items-center gap-2 rounded-md border px-2.5 py-1 text-sm ${editMode ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-[var(--line)]'}`}>
          <input type="checkbox" checked={editMode} onChange={(e) => setEditMode(e.target.checked)} className="accent-indigo-600" />
          <span className="font-semibold">{editMode ? 'Edit mode' : 'Preview'}</span>
        </label>

        <div className="ml-auto flex items-center gap-1 rounded-md border border-[var(--line)] p-0.5">
          {(['desktop', 'tablet', 'mobile'] as const).map((bp) => (
            <button
              key={bp}
              onClick={() => setBreakpoint(bp)}
              className={`rounded px-2.5 py-1 text-xs capitalize ${breakpoint === bp ? 'bg-[var(--bg-3)] font-semibold' : 'hover:bg-[var(--bg-3)]'}`}
            >
              {bp}
            </button>
          ))}
        </div>
        <button onClick={reloadIframe} className="rounded-md border border-[var(--line)] bg-[var(--bg)] px-3 py-1 text-sm hover:bg-[var(--bg-3)]">
          Reload
        </button>
      </div>

      {editMode && (
        <div className="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs text-indigo-800">
          <strong>Edit mode:</strong> click any element to edit • <strong>Alt+drag</strong> to reorder siblings • on form pages, drag fields to reorder.
        </div>
      )}

      <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_380px] gap-3">
        {/* Canvas */}
        <section className="flex min-h-0 items-start justify-center overflow-auto rounded-xl border border-[var(--line)] bg-[var(--bg-2)] p-4">
          <div
            className="shrink-0 bg-white shadow-sm transition-all"
            style={{ width: canvasWidth, maxWidth: '100%' }}
          >
            <iframe
              ref={iframeRef}
              title="Live preview"
              src={previewSrc}
              style={{ width: '100%', height: 'calc(100vh - 240px)', border: 0, display: 'block' }}
            />
          </div>
        </section>

        {/* Inspector */}
        <section className="flex min-h-0 flex-col overflow-y-auto rounded-xl border border-[var(--line)] bg-[var(--bg-2)] p-4">
          {!picked ? (
            <div className="flex h-40 flex-col items-center justify-center gap-2 text-center text-sm text-[var(--text-3)]">
              <div className="text-base font-semibold text-[var(--text)]">Click any element</div>
              <div>Hover the live page, then click to edit.</div>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wide text-[var(--text-3)]">
                  &lt;{picked.tag}&gt; selector
                </div>
                <code className="mt-1 block break-all rounded-md bg-[var(--bg)] px-2 py-1.5 text-xs">{picked.selector}</code>
              </div>

              {/* AI edit */}
              <div className="rounded-md border border-indigo-200 bg-gradient-to-br from-indigo-50 to-white p-2.5">
                <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-indigo-700">Ask AI</div>
                <textarea
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  rows={2}
                  placeholder="make this look like a hero card with soft shadow"
                  className="w-full rounded border border-indigo-200 bg-white px-2 py-1 text-sm"
                />
                <button
                  onClick={handleAiEdit}
                  disabled={aiBusy || !aiPrompt.trim()}
                  className="mt-1.5 w-full rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                >
                  {aiBusy ? 'Thinking…' : 'Generate styles'}
                </button>
              </div>

              <label className="flex flex-col gap-1">
                <span className="text-xs font-semibold uppercase tracking-wide text-[var(--text-3)]">Scope</span>
                <select
                  value={scope}
                  onChange={(e) => setScope(e.target.value)}
                  className="rounded-md border border-[var(--line)] bg-[var(--bg)] px-2 py-1 text-sm"
                >
                  <option value="global">Global (all routes)</option>
                  <option value={fromPath}>This route only ({fromPath})</option>
                  <option value={fromPath.split('/').slice(0, 2).join('/') + '/'}>
                    This app ({fromPath.split('/').slice(0, 2).join('/')}/*)
                  </option>
                </select>
              </label>

              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={hidden} onChange={(e) => setHidden(e.target.checked)} />
                <span>Hide this element</span>
              </label>

              <div>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={textEnabled} onChange={(e) => setTextEnabled(e.target.checked)} />
                  <span>Override text</span>
                </label>
                {textEnabled && (
                  <textarea
                    value={textOverride}
                    onChange={(e) => setTextOverride(e.target.value)}
                    rows={2}
                    className="mt-1 w-full rounded-md border border-[var(--line)] bg-[var(--bg)] px-2 py-1 text-sm"
                  />
                )}
              </div>

              <div className="border-t border-[var(--line)] pt-3">
                <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-3)]">
                  Styles ({picked.tag})
                </div>
                <div className="flex flex-col gap-2">
                  {styleFields.map((field) => {
                    const cur = draft[field.key] ?? ''
                    const camel = field.key.replace(/-([a-z])/g, (_, c) => c.toUpperCase())
                    const computed = picked.styles[camel] || ''
                    return (
                      <div key={field.key} className="grid grid-cols-[100px_1fr] items-center gap-2 text-sm">
                        <label className="text-xs text-[var(--text-3)]">{field.label}</label>
                        {field.type === 'color' ? (
                          <div className="flex items-center gap-2">
                            <input
                              type="color"
                              value={cur ? (cur.startsWith('#') ? cur : toRgbHex(cur)) : toRgbHex(computed)}
                              onChange={(e) => updateDraft(field.key, e.target.value)}
                              className="h-7 w-10 cursor-pointer rounded border border-[var(--line)]"
                            />
                            <input
                              type="text"
                              value={cur}
                              onChange={(e) => updateDraft(field.key, e.target.value)}
                              placeholder={computed}
                              className="flex-1 rounded-md border border-[var(--line)] bg-[var(--bg)] px-2 py-1 text-xs"
                            />
                          </div>
                        ) : field.type === 'select' ? (
                          <select
                            value={cur}
                            onChange={(e) => updateDraft(field.key, e.target.value)}
                            className="rounded-md border border-[var(--line)] bg-[var(--bg)] px-2 py-1 text-xs"
                          >
                            {(field.options || []).map((opt) => (
                              <option key={opt} value={opt}>{opt || `(computed: ${computed})`}</option>
                            ))}
                          </select>
                        ) : (
                          <input
                            type="text"
                            value={cur}
                            onChange={(e) => updateDraft(field.key, e.target.value)}
                            placeholder={computed}
                            className="rounded-md border border-[var(--line)] bg-[var(--bg)] px-2 py-1 text-xs"
                          />
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>

              <button
                onClick={handleSave}
                disabled={saving}
                className="mt-2 rounded-md bg-[var(--aras-accent,#6366f1)] px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {saving ? 'Saving…' : 'Save override'}
              </button>
            </div>
          )}

          {/* Active overrides */}
          {overrides.length > 0 && (
            <div className="mt-4 border-t border-[var(--line)] pt-3">
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-3)]">
                Active on this route ({overrides.length})
              </div>
              <div className="flex flex-col gap-1.5">
                {overrides.map((o) => (
                  <div key={o.id} className="flex items-center gap-2 rounded-md bg-[var(--bg)] px-2 py-1.5 text-xs">
                    <span className="flex-1 truncate" title={o.selector}>
                      <span className="font-mono">{o.selector}</span>
                      {o.label && <span className="ml-2 text-[var(--text-3)]">{o.label}</span>}
                    </span>
                    <span className="rounded bg-[var(--bg-3)] px-1.5 py-0.5 text-[10px] uppercase">{o.scope === 'global' ? 'global' : 'route'}</span>
                    {o.id && (
                      <button onClick={() => handleDelete(o.id!)} className="text-[var(--text-3)] hover:text-red-500">×</button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* History / undo */}
          {history.length > 0 && (
            <div className="mt-4 border-t border-[var(--line)] pt-3">
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-3)]">
                Recent changes ({history.length})
              </div>
              <div className="flex flex-col gap-1">
                {history.map((h) => (
                  <div key={h.id} className="flex items-center gap-2 rounded bg-[var(--bg)] px-2 py-1 text-[11px]">
                    <span className="flex-1 truncate font-mono" title={h.selector}>{h.selector}</span>
                    {h.updated_at && (
                      <span className="text-[var(--text-3)]">{new Date(h.updated_at).toLocaleTimeString()}</span>
                    )}
                    {h.id && (
                      <button
                        onClick={() => handleDelete(h.id!)}
                        title="Revert this change"
                        className="rounded border border-[var(--line)] px-1.5 py-0.5 text-[10px] hover:bg-[var(--bg-3)]"
                      >
                        Undo
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

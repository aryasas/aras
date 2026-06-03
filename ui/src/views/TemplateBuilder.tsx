import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Eye,
  Laptop,
  MousePointer2,
  Move,
  Paintbrush,
  PanelRight,
  RefreshCw,
  Save,
  Smartphone,
  Sparkles,
  Tablet,
  Trash2,
  Type,
  Wand2,
} from 'lucide-react'
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
  css_json: Record<string, any>
  text_override?: string | null
  hidden?: boolean
  updated_at?: string | null
}

type ToolMode = 'select' | 'reorder'
type Viewport = 'desktop' | 'tablet' | 'mobile'

const DEV_UI = '/dev/dev'
const VIEWPORTS: Record<Viewport, { label: string; width: number; icon: typeof Laptop }> = {
  desktop: { label: 'Desktop', width: 1280, icon: Laptop },
  tablet: { label: 'Tablet', width: 820, icon: Tablet },
  mobile: { label: 'Mobile', width: 390, icon: Smartphone },
}

const RESPONSIVE_MEDIA: Record<Exclude<Viewport, 'desktop'>, string> = {
  tablet: '@media (max-width: 1024px)',
  mobile: '@media (max-width: 640px)',
}

const PRESETS: Array<{ label: string; patch: Record<string, string> }> = [
  { label: 'Panel', patch: { 'background-color': '#ffffff', border: '1px solid #e5e7eb', 'border-radius': '8px', padding: '18px', 'box-shadow': '0 10px 24px rgba(15,23,42,0.08)' } },
  { label: 'Quiet', patch: { 'background-color': '#f8fafc', border: '1px solid #e2e8f0', 'border-radius': '8px', padding: '14px' } },
  { label: 'Primary', patch: { color: '#ffffff', 'background-color': '#2563eb', border: '1px solid #2563eb', 'border-radius': '6px', padding: '10px 14px', 'font-weight': '700' } },
  { label: 'Heading', patch: { color: '#0f172a', 'font-size': '28px', 'font-weight': '800', 'line-height': '1.15', 'letter-spacing': '0' } },
  { label: 'Muted', patch: { color: '#64748b', 'font-size': '13px', 'line-height': '1.55' } },
]

const QUICK_FIELDS = [
  ['background-color', 'Background'],
  ['color', 'Text'],
  ['font-size', 'Font size'],
  ['font-weight', 'Weight'],
  ['padding', 'Padding'],
  ['margin', 'Margin'],
  ['border', 'Border'],
  ['border-radius', 'Radius'],
  ['width', 'Width'],
  ['height', 'Height'],
  ['display', 'Display'],
  ['gap', 'Gap'],
] as const

function normalizeFrom(raw: string) {
  if (!raw || raw === 'landing') return '/welcome'
  return raw.startsWith('/') ? raw : `/${raw}`
}

function toRgbHex(rgb: string): string {
  const m = rgb.match(/rgba?\(([^)]+)\)/)
  if (!m) return rgb?.startsWith('#') ? rgb : '#000000'
  const parts = m[1].split(',').map((s) => parseInt(s.trim(), 10))
  return `#${parts.slice(0, 3).map((n) => (Number.isFinite(n) ? n : 0).toString(16).padStart(2, '0')).join('')}`
}

function camelToKebab(value: string) {
  return value.replace(/([A-Z])/g, '-$1').toLowerCase()
}

function baseCss(cssJson?: Record<string, any>) {
  const out: Record<string, string> = {}
  for (const [key, value] of Object.entries(cssJson || {})) {
    if (key.startsWith('@media')) continue
    if (typeof value === 'string') out[key] = value
  }
  return out
}

function viewportCss(cssJson: Record<string, any> | undefined, viewport: Viewport) {
  if (viewport === 'desktop') return baseCss(cssJson)
  const media = RESPONSIVE_MEDIA[viewport]
  const nested = cssJson?.[media]
  return nested && typeof nested === 'object' && !Array.isArray(nested) ? { ...nested } as Record<string, string> : {}
}

function mergeViewportCss(cssJson: Record<string, any> | undefined, viewport: Viewport, draft: Record<string, string>) {
  if (viewport === 'desktop') {
    const next: Record<string, any> = {}
    for (const [key, value] of Object.entries(cssJson || {})) {
      if (key.startsWith('@media')) next[key] = value
    }
    return { ...next, ...draft }
  }
  const media = RESPONSIVE_MEDIA[viewport]
  return { ...(cssJson || {}), [media]: draft }
}

function FieldRow({
  label,
  value,
  placeholder,
  onChange,
  color = false,
}: {
  label: string
  value: string
  placeholder?: string
  onChange: (value: string) => void
  color?: boolean
}) {
  return (
    <label className="grid grid-cols-[88px_minmax(0,1fr)] items-center gap-2 text-xs">
      <span className="font-bold text-slate-500">{label}</span>
      {color ? (
        <div className="flex min-w-0 items-center gap-2">
          <input
            type="color"
            value={value ? (value.startsWith('#') ? value : toRgbHex(value)) : toRgbHex(placeholder || '#000000')}
            onChange={(event) => onChange(event.target.value)}
            className="h-8 w-10 shrink-0 rounded border border-slate-200"
          />
          <input
            value={value}
            placeholder={placeholder}
            onChange={(event) => onChange(event.target.value)}
            className="min-w-0 flex-1 rounded-md border border-slate-200 bg-white px-2 py-1.5 outline-none focus:border-blue-400"
          />
        </div>
      ) : (
        <input
          value={value}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
          className="min-w-0 rounded-md border border-slate-200 bg-white px-2 py-1.5 outline-none focus:border-blue-400"
        />
      )}
    </label>
  )
}

export default function TemplateBuilder() {
  const { notify } = useAras()
  const [searchParams, setSearchParams] = useSearchParams()
  const iframeRef = useRef<HTMLIFrameElement | null>(null)

  const fromPath = normalizeFrom(searchParams.get('from') || localStorage.getItem('template-studio:last') || '/')
  const [routeInput, setRouteInput] = useState(fromPath)
  const [toolMode, setToolMode] = useState<ToolMode>('select')
  const [previewOnly, setPreviewOnly] = useState(false)
  const [viewport, setViewport] = useState<Viewport>('desktop')
  const [picked, setPicked] = useState<Picked | null>(null)
  const [draft, setDraft] = useState<Record<string, string>>({})
  const [pickedOverrideCss, setPickedOverrideCss] = useState<Record<string, any>>({})
  const [hidden, setHidden] = useState(false)
  const [textOverride, setTextOverride] = useState('')
  const [textEnabled, setTextEnabled] = useState(false)
  const [scope, setScope] = useState<string>(fromPath)
  const [overrides, setOverrides] = useState<Override[]>([])
  const [aiPrompt, setAiPrompt] = useState('')
  const [aiBusy, setAiBusy] = useState(false)
  const [saving, setSaving] = useState(false)
  const [expoSelector, setExpoSelector] = useState('')
  const [expoPreviewUrl, setExpoPreviewUrl] = useState(() =>
    localStorage.getItem('template-builder:expo-url')
    || import.meta.env.VITE_EXPO_PREVIEW_URL
    || 'http://localhost:8081',
  )

  const nativePreview = viewport === 'tablet' || viewport === 'mobile'

  const inferExpoSelector = (pickedNode: Picked | null) => {
    if (!pickedNode) return ''
    if (pickedNode.tag === 'button' || pickedNode.tag === 'a') return 'mobile:button'
    if (['input', 'select', 'textarea', 'label'].includes(pickedNode.tag)) return 'mobile:input'
    if (/^h[1-6]$/.test(pickedNode.tag) || ['p', 'span', 'strong', 'small'].includes(pickedNode.tag)) return 'mobile:button-text'
    return 'mobile:card'
  }

  const editMode = !previewOnly
  const previewSrc = useMemo(() => {
    const sep = fromPath.includes('?') ? '&' : '?'
    return `${fromPath}${sep}__builder_preview=1${editMode ? '&__builder_edit=1' : ''}`
  }, [editMode, fromPath])
  const canvasSrc = nativePreview ? expoPreviewUrl : previewSrc

  const loadOverrides = useCallback(async () => {
    try {
      const res = await api.get(`${DEV_UI}/style-overrides?path=${encodeURIComponent(nativePreview ? 'mobile' : fromPath)}`)
      setOverrides(Array.isArray(res.data) ? res.data : [])
    } catch {
      setOverrides([])
    }
  }, [fromPath, nativePreview])

  useEffect(() => {
    localStorage.setItem('template-studio:last', fromPath)
    setRouteInput(fromPath)
    setScope(fromPath)
    setPicked(null)
    setDraft({})
    if (!nativePreview) setExpoSelector('')
  }, [fromPath, nativePreview])

  useEffect(() => { loadOverrides() }, [loadOverrides])

  useEffect(() => {
    iframeRef.current?.contentWindow?.postMessage({
      type: 'aras-builder-set-mode',
      edit: editMode,
      tool: toolMode,
    }, '*')
  }, [editMode, nativePreview, toolMode, canvasSrc])

  const reloadIframe = useCallback(() => {
    if (iframeRef.current) iframeRef.current.src = canvasSrc
  }, [canvasSrc])

  useEffect(() => {
    const onMessage = async (event: MessageEvent) => {
      if (!event.data || typeof event.data !== 'object') return
      if (event.data.type === 'aras-builder-ready') {
        iframeRef.current?.contentWindow?.postMessage({ type: 'aras-builder-set-mode', edit: editMode, tool: toolMode }, '*')
      }
      if (event.data.type === 'aras-builder-pick') {
        const nextPicked = event.data.payload as Picked
        const existing = overrides.find((row) => row.selector === nextPicked.selector)
        setPicked(nextPicked)
        setPickedOverrideCss(existing?.css_json ? { ...existing.css_json } : {})
        setDraft(viewportCss(existing?.css_json, viewport))
        setHidden(Boolean(existing?.hidden))
        setTextOverride(existing?.text_override || nextPicked.text || '')
        setTextEnabled(Boolean(existing?.text_override))
        setExpoSelector(inferExpoSelector(nextPicked))
      }
      if (event.data.type === 'aras-builder-reordered') {
        notify('Field order saved', 'success')
        await loadOverrides()
        reloadIframe()
      }
      if (event.data.type === 'aras-builder-reorder') {
        const patches = event.data.patches as Array<{ selector: string; css_json: Record<string, string>; label: string }>
        try {
          await Promise.all(patches.map((patch) =>
            api.post(`${DEV_UI}/style-overrides`, { scope, selector: patch.selector, css_json: patch.css_json, label: patch.label }),
          ))
          notify('Order saved', 'success')
          await loadOverrides()
          reloadIframe()
        } catch (error: any) {
          notify(error?.message || 'Reorder failed', 'error')
        }
      }
    }
    window.addEventListener('message', onMessage)
    return () => window.removeEventListener('message', onMessage)
  }, [editMode, loadOverrides, notify, overrides, reloadIframe, scope, toolMode, viewport])

  useEffect(() => {
    if (!picked) return
    const existing = overrides.find((row) => row.selector === picked.selector)
    if (!existing) {
      setDraft(viewportCss(pickedOverrideCss, viewport))
      return
    }
    setPickedOverrideCss({ ...existing.css_json })
    setDraft(viewportCss(existing.css_json, viewport))
    // pickedOverrideCss is intentionally omitted; this effect syncs when the selected element,
    // viewport, or loaded override rows change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [overrides, picked?.selector, viewport])

  useEffect(() => {
    if (!nativePreview || picked || !expoSelector.trim()) return
    const existing = overrides.find((row) => row.selector === expoSelector.trim())
    setDraft(existing?.css_json ? baseCss(existing.css_json) : {})
    setHidden(Boolean(existing?.hidden))
    setTextOverride(existing?.text_override || '')
    setTextEnabled(Boolean(existing?.text_override))
  }, [expoSelector, nativePreview, overrides, picked])

  const setStyle = (key: string, value: string) => {
    setDraft((current) => {
      const next = { ...current }
      if (!value) delete next[key]
      else next[key] = value
      return next
    })
  }

  const applyPreset = (patch: Record<string, string>) => {
    setDraft((current) => ({ ...current, ...patch }))
  }

  const save = useCallback(async () => {
    if (!picked && !(nativePreview && expoSelector.trim())) return
    setSaving(true)
    try {
      if (picked && !nativePreview) {
        await api.post(`${DEV_UI}/style-overrides`, {
          scope,
          selector: picked.selector,
          label: picked.text?.slice(0, 80) || picked.tag,
          css_json: mergeViewportCss(pickedOverrideCss, viewport, draft),
          hidden,
          text_override: textEnabled ? textOverride : null,
        })
      }
      if (nativePreview && expoSelector.trim()) {
        await api.post(`${DEV_UI}/style-overrides`, {
          scope: 'mobile',
          selector: expoSelector.trim(),
          label: `Expo ${expoSelector.trim()}`,
          css_json: draft,
          hidden,
          text_override: textEnabled ? textOverride : null,
        })
      }
      notify(`${VIEWPORTS[viewport].label} change applied`, 'success')
      await loadOverrides()
      reloadIframe()
    } catch (error: any) {
      notify(error?.message || 'Save failed', 'error')
    } finally {
      setSaving(false)
    }
  }, [draft, expoSelector, hidden, loadOverrides, nativePreview, notify, picked, pickedOverrideCss, reloadIframe, scope, textEnabled, textOverride, viewport])

  const deleteOverride = useCallback(async (id: number) => {
    try {
      await api.delete(`${DEV_UI}/style-overrides/${id}`)
      notify('Change removed', 'success')
      await loadOverrides()
      reloadIframe()
    } catch (error: any) {
      notify(error?.message || 'Delete failed', 'error')
    }
  }, [loadOverrides, notify, reloadIframe])

  const aiEdit = useCallback(async () => {
    if (!picked || !aiPrompt.trim()) return
    setAiBusy(true)
    try {
      const computed = Object.fromEntries(Object.entries(picked.styles).map(([key, value]) => [camelToKebab(key), value]))
      const res = await api.post(`${DEV_UI}/style-overrides/ai`, {
        selector: picked.selector,
        tag: picked.tag,
        computed,
        instruction: aiPrompt,
      })
      const patch = res.data?.css_json || {}
      setDraft((current) => ({ ...current, ...patch }))
      notify('AI style ready to apply', 'success')
    } catch (error: any) {
      notify(error?.response?.data?.detail || error?.message || 'AI edit failed', 'error')
    } finally {
      setAiBusy(false)
    }
  }, [aiPrompt, notify, picked])

  const goToRoute = (path: string) => {
    const next = normalizeFrom(path)
    localStorage.setItem('template-studio:last', next)
    setSearchParams({ from: next })
  }

  const currentViewport = VIEWPORTS[viewport]

  return (
    <div className="flex h-[calc(100vh-88px)] min-h-[720px] flex-col bg-slate-100 text-slate-950">
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 bg-white px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-slate-950 text-white">
            <Wand2 size={18} />
          </div>
          <div>
            <div className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-500">Template Builder</div>
            {nativePreview ? (
              <form
                className="mt-1 flex items-center gap-2"
                onSubmit={(event) => {
                  event.preventDefault()
                  localStorage.setItem('template-builder:expo-url', expoPreviewUrl)
                  reloadIframe()
                }}
              >
                <input
                  value={expoPreviewUrl}
                  onChange={(event) => setExpoPreviewUrl(event.target.value)}
                  className="w-72 rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm font-bold outline-none focus:border-blue-400"
                />
                <button className="rounded-md bg-slate-950 px-3 py-1.5 text-xs font-bold text-white">Open Expo</button>
              </form>
            ) : (
              <form className="mt-1 flex items-center gap-2" onSubmit={(event) => { event.preventDefault(); goToRoute(routeInput) }}>
                <input
                  value={routeInput}
                  onChange={(event) => setRouteInput(event.target.value)}
                  className="w-72 rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm font-bold outline-none focus:border-blue-400"
                />
                <button className="rounded-md bg-slate-950 px-3 py-1.5 text-xs font-bold text-white">Open Web</button>
              </form>
            )}
          </div>
        </div>

        <div className="ml-auto flex flex-wrap items-center gap-2">
          <div className="flex rounded-md border border-slate-200 bg-slate-50 p-1">
            <button onClick={() => setToolMode('select')} className={`flex items-center gap-2 rounded px-3 py-1.5 text-xs font-bold ${toolMode === 'select' ? 'bg-slate-950 text-white' : 'text-slate-600 hover:bg-white'}`}>
              <MousePointer2 size={14} />
              Select
            </button>
            <button onClick={() => setToolMode('reorder')} className={`flex items-center gap-2 rounded px-3 py-1.5 text-xs font-bold ${toolMode === 'reorder' ? 'bg-slate-950 text-white' : 'text-slate-600 hover:bg-white'}`}>
              <Move size={14} />
              Drag
            </button>
          </div>
          <div className="flex rounded-md border border-slate-200 bg-slate-50 p-1">
            {(Object.keys(VIEWPORTS) as Viewport[]).map((key) => {
              const Icon = VIEWPORTS[key].icon
              return (
                <button key={key} onClick={() => setViewport(key)} className={`flex items-center gap-2 rounded px-3 py-1.5 text-xs font-bold ${viewport === key ? 'bg-slate-950 text-white' : 'text-slate-600 hover:bg-white'}`}>
                  <Icon size={14} />
                  {VIEWPORTS[key].label}
                </button>
              )
            })}
          </div>
          <button onClick={() => setPreviewOnly((value) => !value)} className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs font-bold hover:bg-slate-50">
            {previewOnly ? <Paintbrush size={14} /> : <Eye size={14} />}
            {previewOnly ? 'Edit' : 'Preview'}
          </button>
          <button onClick={reloadIframe} className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs font-bold hover:bg-slate-50">
            <RefreshCw size={14} />
            Reload
          </button>
          <button onClick={save} disabled={(!picked && !(nativePreview && expoSelector.trim())) || saving} className="flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-xs font-bold text-white disabled:opacity-50">
            <Save size={14} />
            {saving ? 'Applying' : 'Apply'}
          </button>
        </div>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-[260px_minmax(0,1fr)_390px]">
        <aside className="min-h-0 overflow-y-auto border-r border-slate-200 bg-white">
          <div className="border-b border-slate-200 p-4">
            <div className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-500">Presets</div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {PRESETS.map((preset) => (
                <button key={preset.label} disabled={!picked} onClick={() => applyPreset(preset.patch)} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-left text-xs font-black text-slate-700 hover:border-blue-300 hover:bg-blue-50 disabled:opacity-40">
                  {preset.label}
                </button>
              ))}
            </div>
          </div>
          <div className="border-b border-slate-200 p-4">
            <div className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-500">Scope</div>
            <select value={scope} onChange={(event) => setScope(event.target.value)} className="mt-3 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold outline-none">
              <option value={fromPath}>This page</option>
              <option value={fromPath.split('/').slice(0, 2).join('/') || '/'}>This area</option>
              <option value="global">Global</option>
            </select>
          </div>
          <div className="p-4">
            <div className="mb-3 flex items-center justify-between">
              <div className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-500">Active Changes</div>
              <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-black text-slate-500">{overrides.length}</span>
            </div>
            <div className="space-y-2">
              {overrides.map((row) => (
                <button key={row.id} onClick={() => row.id && deleteOverride(row.id)} className="group flex w-full items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-left hover:border-red-200 hover:bg-red-50">
                  <span className="min-w-0 flex-1 truncate font-mono text-[11px] text-slate-600">{row.label || row.selector}</span>
                  <Trash2 size={13} className="text-slate-400 group-hover:text-red-500" />
                </button>
              ))}
              {overrides.length === 0 ? <div className="rounded-md border border-dashed border-slate-200 p-3 text-xs font-medium text-slate-400">No saved changes on this page.</div> : null}
            </div>
          </div>
        </aside>

        <main className="min-h-0 overflow-auto bg-slate-200 p-5">
          <div className="mx-auto min-h-full bg-white shadow-sm transition-all" style={{ width: currentViewport.width, maxWidth: '100%' }}>
            <iframe ref={iframeRef} title={nativePreview ? 'Expo mobile preview' : 'Live page editor'} src={canvasSrc} className="block h-[calc(100vh-190px)] min-h-[620px] w-full border-0" />
          </div>
        </main>

        <aside className="min-h-0 overflow-y-auto border-l border-slate-200 bg-white">
          <div className="border-b border-slate-200 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-500">Inspector</div>
                <div className="mt-1 truncate text-sm font-black">{picked ? `<${picked.tag}>` : 'No selection'}</div>
              </div>
              <PanelRight size={18} className="text-slate-400" />
            </div>
            <div className="mt-3 rounded-md border border-blue-100 bg-blue-50 px-3 py-2 text-xs font-bold text-blue-700">
              Editing {currentViewport.label}: {viewport === 'desktop' ? 'base styles' : `${RESPONSIVE_MEDIA[viewport]} styles`}
            </div>
            {picked ? <code className="mt-3 block break-all rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-slate-500">{picked.selector}</code> : null}
          </div>

          {!picked ? (
            <div className="p-5">
              <div className="rounded-md border border-dashed border-slate-300 bg-slate-50 p-5 text-sm font-medium text-slate-500">
                {nativePreview
                  ? 'Expo preview is native/web-rendered, so edit by Expo target selector. Use mobile:button, mobile:input, or mobile:card, then apply.'
                  : 'Open a page, keep Select active, then click an element in the canvas.'}
              </div>
              {nativePreview ? (
                <div className="mt-4 space-y-4">
                  <section className="space-y-3 rounded-md border border-slate-200 bg-white p-3">
                    <div className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">
                      Expo target
                    </div>
                    <input
                      value={expoSelector}
                      onChange={(event) => setExpoSelector(event.target.value)}
                      placeholder="mobile:button"
                      className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold outline-none focus:border-blue-400"
                    />
                    <div className="text-[11px] font-medium leading-4 text-slate-500">
                      Selectors available now: mobile:button, mobile:button-text, mobile:input, mobile:input-label, mobile:input-field, mobile:card.
                    </div>
                  </section>
                  <section className="space-y-3 rounded-md border border-slate-200 bg-white p-3">
                    <div className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">Native style</div>
                    {QUICK_FIELDS.map(([key, label]) => (
                      <FieldRow key={key} label={label} value={draft[key] || ''} onChange={(value) => setStyle(key, value)} color={key.includes('color')} />
                    ))}
                    <button onClick={save} disabled={!expoSelector.trim() || saving} className="flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-xs font-black text-white disabled:opacity-50">
                      <Save size={14} />
                      Apply to Expo
                    </button>
                  </section>
                </div>
              ) : null}
            </div>
          ) : (
            <div className="space-y-5 p-4">
              <section className="space-y-3 rounded-md border border-blue-100 bg-blue-50 p-3">
                <div className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.14em] text-blue-700">
                  <Sparkles size={14} />
                  Claude-style edit
                </div>
                <textarea value={aiPrompt} onChange={(event) => setAiPrompt(event.target.value)} rows={3} placeholder="Make this card cleaner, tighter, and easier to scan" className="w-full rounded-md border border-blue-200 bg-white px-3 py-2 text-sm outline-none" />
                <button onClick={aiEdit} disabled={aiBusy || !aiPrompt.trim()} className="flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-xs font-black text-white disabled:opacity-50">
                  <Wand2 size={14} />
                  {aiBusy ? 'Thinking' : 'Generate draft'}
                </button>
              </section>

              {viewport === 'mobile' ? (
                <section className="space-y-3 rounded-md border border-slate-200 bg-slate-50 p-3">
                  <div className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">
                    Expo target
                  </div>
                  <input
                    value={expoSelector}
                    onChange={(event) => setExpoSelector(event.target.value)}
                    placeholder="mobile:button"
                    className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold outline-none focus:border-blue-400"
                  />
                  <div className="text-[11px] font-medium leading-4 text-slate-500">
                    Mobile applies to React Native selectors: mobile:button, mobile:button-text, mobile:input, mobile:input-label, mobile:input-field, mobile:card.
                  </div>
                </section>
              ) : null}

              <section className="space-y-3">
                <div className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.14em] text-slate-500">
                  <Type size={14} />
                  Content
                </div>
                <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                  <input type="checkbox" checked={textEnabled} onChange={(event) => setTextEnabled(event.target.checked)} />
                  Override text
                </label>
                {textEnabled ? <textarea value={textOverride} onChange={(event) => setTextOverride(event.target.value)} rows={3} className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400" /> : null}
                <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                  <input type="checkbox" checked={hidden} onChange={(event) => setHidden(event.target.checked)} />
                  Hide element
                </label>
              </section>

              <section className="space-y-3">
                <div className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.14em] text-slate-500">
                  <Paintbrush size={14} />
                  Style
                </div>
                {QUICK_FIELDS.map(([key, label]) => {
                  const camel = key.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())
                  const placeholder = picked.styles[camel] || ''
                  const isColor = key.includes('color')
                  return <FieldRow key={key} label={label} value={draft[key] || ''} placeholder={placeholder} color={isColor} onChange={(value) => setStyle(key, value)} />
                })}
                <div className="grid grid-cols-3 gap-2">
                  {[
                    ['left', AlignLeft],
                    ['center', AlignCenter],
                    ['right', AlignRight],
                  ].map(([align, Icon]) => (
                    <button key={String(align)} onClick={() => setStyle('text-align', String(align))} className="flex items-center justify-center rounded-md border border-slate-200 py-2 hover:bg-slate-50">
                      <Icon size={15} />
                    </button>
                  ))}
                </div>
              </section>

              <div className="sticky bottom-0 -mx-4 -mb-4 border-t border-slate-200 bg-white p-4">
                <button onClick={save} disabled={saving} className="flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-2.5 text-sm font-black text-white disabled:opacity-50">
                  <Save size={15} />
                  {saving ? 'Applying' : 'Apply to page'}
                </button>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}

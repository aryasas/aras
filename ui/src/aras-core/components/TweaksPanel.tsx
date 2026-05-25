// claude-opus-4-7
// ArasStudio Tweaks panel ported into aras UI. Live theme inspector bound to uiStore.
// Floating coral toggle (bottom-right) opens a draggable glassmorphism panel.
import React, { useEffect, useRef, useState, useCallback } from 'react'
import { Settings2 } from 'lucide-react'
import { useUIStore } from '../../store/uiStore'

const TWEAKS_STYLE = String.raw`
  .twk-panel{position:fixed;right:16px;bottom:64px;z-index:2147483646;width:280px;
    max-height:calc(100vh - 96px);display:flex;flex-direction:column;
    background:rgba(250,249,247,.78);color:#29261b;
    -webkit-backdrop-filter:blur(24px) saturate(160%);backdrop-filter:blur(24px) saturate(160%);
    border:.5px solid rgba(255,255,255,.6);border-radius:14px;
    box-shadow:0 1px 0 rgba(255,255,255,.5) inset,0 12px 40px rgba(0,0,0,.18);
    font:11.5px/1.4 ui-sans-serif,system-ui,-apple-system,sans-serif;overflow:hidden}
  [data-theme="dark"] .twk-panel{background:rgba(22,27,35,.82);color:#e7e9ee;border-color:rgba(255,255,255,.08)}
  .twk-hd{display:flex;align-items:center;justify-content:space-between;
    padding:10px 8px 10px 14px;cursor:move;user-select:none}
  .twk-hd b{font-size:12px;font-weight:600;letter-spacing:.01em}
  .twk-x{appearance:none;border:0;background:transparent;color:rgba(41,38,27,.55);
    width:22px;height:22px;border-radius:6px;cursor:pointer;font-size:13px;line-height:1}
  [data-theme="dark"] .twk-x{color:rgba(231,233,238,.5)}
  .twk-x:hover{background:rgba(0,0,0,.06);color:#29261b}
  [data-theme="dark"] .twk-x:hover{background:rgba(255,255,255,.08);color:#e7e9ee}
  .twk-body{padding:2px 14px 14px;display:flex;flex-direction:column;gap:10px;
    overflow-y:auto;overflow-x:hidden;min-height:0;scrollbar-width:thin;
    scrollbar-color:rgba(0,0,0,.15) transparent}
  .twk-body::-webkit-scrollbar{width:8px}
  .twk-body::-webkit-scrollbar-thumb{background:rgba(0,0,0,.15);border-radius:4px;
    border:2px solid transparent;background-clip:content-box}
  .twk-row{display:flex;flex-direction:column;gap:5px}
  .twk-row-h{flex-direction:row;align-items:center;justify-content:space-between;gap:10px}
  .twk-lbl{display:flex;justify-content:space-between;align-items:baseline;
    color:rgba(41,38,27,.72)}
  [data-theme="dark"] .twk-lbl{color:rgba(231,233,238,.7)}
  .twk-lbl>span:first-child{font-weight:500}
  .twk-val{color:rgba(41,38,27,.5);font-variant-numeric:tabular-nums}
  [data-theme="dark"] .twk-val{color:rgba(231,233,238,.5)}
  .twk-sect{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
    color:rgba(41,38,27,.45);padding:10px 0 0}
  [data-theme="dark"] .twk-sect{color:rgba(231,233,238,.45)}
  .twk-sect:first-child{padding-top:0}
  .twk-field{appearance:none;box-sizing:border-box;width:100%;min-width:0;height:26px;padding:0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;
    background:rgba(255,255,255,.6);color:inherit;font:inherit;outline:none}
  [data-theme="dark"] .twk-field{border-color:rgba(255,255,255,.12);background:rgba(255,255,255,.04)}
  .twk-slider{appearance:none;-webkit-appearance:none;width:100%;height:4px;margin:6px 0;
    border-radius:999px;background:rgba(0,0,0,.12);outline:none}
  [data-theme="dark"] .twk-slider{background:rgba(255,255,255,.12)}
  .twk-slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;
    width:14px;height:14px;border-radius:50%;background:#fff;
    border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:pointer}
  .twk-seg{position:relative;display:flex;padding:2px;border-radius:8px;
    background:rgba(0,0,0,.06);user-select:none}
  [data-theme="dark"] .twk-seg{background:rgba(255,255,255,.06)}
  .twk-seg-thumb{position:absolute;top:2px;bottom:2px;border-radius:6px;
    background:rgba(255,255,255,.9);box-shadow:0 1px 2px rgba(0,0,0,.12);
    transition:left .15s cubic-bezier(.3,.7,.4,1),width .15s}
  [data-theme="dark"] .twk-seg-thumb{background:rgba(255,255,255,.14)}
  .twk-seg button{appearance:none;position:relative;z-index:1;flex:1;border:0;
    background:transparent;color:inherit;font:inherit;font-weight:500;min-height:22px;
    border-radius:6px;cursor:pointer;padding:4px 6px;line-height:1.2;overflow-wrap:anywhere}
  .twk-toggle{position:relative;width:32px;height:18px;border:0;border-radius:999px;
    background:rgba(0,0,0,.15);transition:background .15s;cursor:pointer;padding:0}
  [data-theme="dark"] .twk-toggle{background:rgba(255,255,255,.15)}
  .twk-toggle[data-on="1"]{background:#E89B6C}
  .twk-toggle i{position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;
    background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.25);transition:transform .15s}
  .twk-toggle[data-on="1"] i{transform:translateX(14px)}
  .twk-swatch{appearance:none;-webkit-appearance:none;width:56px;height:22px;
    border:.5px solid rgba(0,0,0,.1);border-radius:6px;padding:0;cursor:pointer;
    background:transparent;flex-shrink:0}
  .twk-swatch::-webkit-color-swatch-wrapper{padding:0}
  .twk-swatch::-webkit-color-swatch{border:0;border-radius:5.5px}
  .twk-fab{position:fixed;right:16px;bottom:16px;z-index:2147483645;width:38px;height:38px;
    border-radius:999px;border:0;cursor:pointer;background:#E89B6C;color:#fff;
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 4px 14px rgba(232,155,108,.45),0 1px 3px rgba(0,0,0,.15)}
  .twk-fab:hover{transform:translateY(-1px);box-shadow:0 6px 18px rgba(232,155,108,.55)}
`

function useTweaksDragger(open: boolean) {
  const dragRef = useRef<HTMLDivElement>(null)
  const offsetRef = useRef({ x: 16, y: 64 })
  const PAD = 16

  const clamp = useCallback(() => {
    const p = dragRef.current
    if (!p) return
    const w = p.offsetWidth, h = p.offsetHeight
    const mr = Math.max(PAD, window.innerWidth - w - PAD)
    const mb = Math.max(PAD, window.innerHeight - h - PAD)
    offsetRef.current = {
      x: Math.min(mr, Math.max(PAD, offsetRef.current.x)),
      y: Math.min(mb, Math.max(PAD, offsetRef.current.y)),
    }
    p.style.right = offsetRef.current.x + 'px'
    p.style.bottom = offsetRef.current.y + 'px'
  }, [])

  useEffect(() => {
    if (!open) return
    clamp()
    window.addEventListener('resize', clamp)
    return () => window.removeEventListener('resize', clamp)
  }, [open, clamp])

  const onDragStart = (e: React.MouseEvent) => {
    const p = dragRef.current
    if (!p) return
    const r = p.getBoundingClientRect()
    const sx = e.clientX, sy = e.clientY
    const sr = window.innerWidth - r.right
    const sb = window.innerHeight - r.bottom
    const move = (ev: MouseEvent) => {
      offsetRef.current = { x: sr - (ev.clientX - sx), y: sb - (ev.clientY - sy) }
      clamp()
    }
    const up = () => {
      window.removeEventListener('mousemove', move)
      window.removeEventListener('mouseup', up)
    }
    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', up)
  }

  return { dragRef, onDragStart, offsetRef }
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (<><div className="twk-sect">{label}</div>{children}</>)
}

function Row({ label, value, children, inline = false }: { label: string; value?: React.ReactNode; children: React.ReactNode; inline?: boolean }) {
  return (
    <div className={inline ? 'twk-row twk-row-h' : 'twk-row'}>
      <div className="twk-lbl">
        <span>{label}</span>
        {value != null && <span className="twk-val">{value}</span>}
      </div>
      {children}
    </div>
  )
}

function Slider({ label, value, min = 0, max = 100, step = 1, unit = '', onChange }: { label: string; value: number; min?: number; max?: number; step?: number; unit?: string; onChange: (v: number) => void }) {
  return (
    <Row label={label} value={value + unit}>
      <input type="range" className="twk-slider" min={min} max={max} step={step}
             value={value} onChange={(e) => onChange(Number(e.target.value))} />
    </Row>
  )
}

function Toggle({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="twk-row twk-row-h">
      <div className="twk-lbl"><span>{label}</span></div>
      <button type="button" className="twk-toggle" data-on={value ? '1' : '0'}
              role="switch" aria-checked={value} onClick={() => onChange(!value)}><i /></button>
    </div>
  )
}

interface Opt<V> { value: V; label: string }
function Seg<V extends string | number>({ label, value, options, onChange }: { label: string; value: V; options: Opt<V>[]; onChange: (v: V) => void }) {
  const idx = Math.max(0, options.findIndex((o) => o.value === value))
  const n = options.length
  return (
    <Row label={label}>
      <div role="radiogroup" className="twk-seg">
        <div className="twk-seg-thumb"
             style={{ left: 'calc(2px + ' + idx + ' * (100% - 4px) / ' + n + ')', width: 'calc((100% - 4px) / ' + n + ')' }} />
        {options.map((o) => (
          <button key={String(o.value)} type="button" role="radio" aria-checked={o.value === value}
                  onClick={() => onChange(o.value)}>{o.label}</button>
        ))}
      </div>
    </Row>
  )
}

function ColorRow({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div className="twk-row twk-row-h">
      <div className="twk-lbl"><span>{label}</span><span className="twk-val">{value}</span></div>
      <input type="color" className="twk-swatch" value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  )
}

export function TweaksPanel() {
  const [open, setOpen] = useState(false)
  const { dragRef, onDragStart, offsetRef } = useTweaksDragger(open)
  const {
    themeMode, setThemeMode,
    accentColor, setAccentColor,
    density, setDensity,
    cornerMode, setCornerMode,
    fontScale, setFontScale,
    sidebarCollapsed, toggleSidebar,
  } = useUIStore()

  return (
    <>
      <style>{TWEAKS_STYLE}</style>
      {!open && (
        <button className="twk-fab" aria-label="Open theme tweaks" onClick={() => setOpen(true)}>
          <Settings2 size={16} />
        </button>
      )}
      {open && (
        <div ref={dragRef} className="twk-panel"
             style={{ right: offsetRef.current.x, bottom: offsetRef.current.y }}>
          <div className="twk-hd" onMouseDown={onDragStart}>
            <b>Tweaks</b>
            <button className="twk-x" aria-label="Close"
                    onMouseDown={(e) => e.stopPropagation()}
                    onClick={() => setOpen(false)}>X</button>
          </div>
          <div className="twk-body">
            <Section label="Theme">
              <Seg label="Mode" value={themeMode}
                   options={[{ value: 'normal', label: 'Light' }, { value: 'dark', label: 'Dark' }]}
                   onChange={(v) => setThemeMode(v as any)} />
              <ColorRow label="Accent" value={accentColor} onChange={setAccentColor} />
            </Section>

            <Section label="Density">
              <Seg label="Spacing" value={density}
                   options={[{ value: 'compact', label: 'Compact' }, { value: 'regular', label: 'Regular' }, { value: 'comfy', label: 'Comfy' }]}
                   onChange={(v) => setDensity(v as any)} />
              <Seg label="Corners" value={cornerMode}
                   options={[{ value: 'rounded', label: 'Rounded' }, { value: 'square', label: 'Square' }]}
                   onChange={(v) => setCornerMode(v as any)} />
              <Slider label="Font scale" value={fontScale} min={85} max={120} step={5} unit="%"
                      onChange={setFontScale} />
            </Section>

            <Section label="Layout">
              <Toggle label="Collapse sidebar" value={sidebarCollapsed} onChange={toggleSidebar} />
            </Section>
          </div>
        </div>
      )}
    </>
  )
}

export default TweaksPanel

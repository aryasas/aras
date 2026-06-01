import { useState, useRef, useEffect } from 'react'
import { SlidersHorizontal } from 'lucide-react'
import { useUIStore } from '../../store/uiStore'
import SimpleCombobox from '../../aras-core/components/SimpleCombobox'

// claude-sonnet-4-6
function ToggleSwitch({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs font-bold text-[var(--aras-muted)]">{label}</span>
      <button
        type="button"
        role="switch"
        aria-checked={value}
        onClick={() => onChange(!value)}
        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${value ? 'bg-[var(--aras-accent)]' : 'bg-[var(--aras-border)]'}`}
      >
        <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${value ? 'translate-x-4' : 'translate-x-0.5'}`} />
      </button>
    </div>
  )
}

const accentOptions = [
  { label: 'Indigo (Default)', value: '#4F46E5' },
  { label: 'Deep Red', value: '#7a2e2e' },
  { label: 'Pine', value: '#34785f' },
  { label: 'Violet', value: '#6f5bd8' },
  { label: 'Blue', value: '#448cf4' },
  { label: 'Black', value: '#111111' },
  { label: 'White', value: '#ffffff' },
]

export function ThemeTweakPanel() {
  const [open, setOpen] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)
  const {
    themeMode,
    cornerMode,
    density,
    accentColor,
    fontScale,
    setThemeMode,
    setCornerMode,
    setDensity,
    setAccentColor,
    setFontScale,
    topbarNavStyle,
    setTopbarNavStyle,
    inlineEdit,
    setInlineEdit,
  } = useUIStore()

  useEffect(() => {
    if (!open) return

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      if (panelRef.current && !panelRef.current.contains(target)) {
          if ((target as Element).closest?.('[role="listbox"]')) return
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open])

  return (
    <div className="relative" ref={panelRef}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex items-center justify-center w-8 h-8 bg-transparent rounded-lg border border-[var(--line)] text-[var(--text-3)] hover:text-[var(--accent)] hover:border-[var(--accent)] transition-all"
        title="Tweak layout"
      >
        <SlidersHorizontal size={18} />
      </button>

      {open && (
        <div className="absolute right-0 top-full z-[100] mt-2 w-[320px] max-w-[calc(100vw-24px)] rounded-[var(--aras-radius)] border border-[var(--line)] bg-[var(--bg-2)] p-4 shadow-xl">
          <div className="mb-4">
            <h3 className="text-sm font-bold text-[var(--aras-text)]">Layout Tweaks</h3>
          </div>

          <div className="space-y-4">
            <label className="block">
              <span className="mb-1.5 block text-xs font-bold text-[var(--aras-muted)]">Theme</span>
              <SimpleCombobox
                options={[
                  { label: 'Light', value: 'light' },
                  { label: 'Normal', value: 'normal' },
                  { label: 'Dark', value: 'dark' }
                ]}
                value={themeMode}
                onChange={(val) => setThemeMode(val as any)}
                width="100%"
              />
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="mb-1.5 block text-xs font-bold text-[var(--aras-muted)]">Corners</span>
                <SimpleCombobox
                  options={[
                    { label: 'Rounded', value: 'rounded' },
                    { label: 'Square', value: 'square' }
                  ]}
                  value={cornerMode}
                  onChange={(val) => setCornerMode(val as any)}
                  width="100%"
                />
              </label>

              <label className="block">
                <span className="mb-1.5 block text-xs font-bold text-[var(--aras-muted)]">Layout</span>
                <SimpleCombobox
                  options={[
                    { label: 'Compact', value: 'compact' },
                    { label: 'Regular', value: 'regular' },
                    { label: 'Comfy', value: 'comfy' }
                  ]}
                  value={density}
                  onChange={(val) => setDensity(val as any)}
                  width="100%"
                />
              </label>
            </div>

            <label className="block">
              <span className="mb-1.5 block text-xs font-bold text-[var(--aras-muted)]">Font Size</span>
              <input
                type="range"
                min="88"
                max="116"
                value={fontScale}
                onChange={(event) => setFontScale(Number(event.target.value))}
                className="w-full accent-[var(--aras-accent)]"
              />
            </label>

            <div>
              <span className="mb-2 block text-xs font-bold text-[var(--aras-muted)]">Accent</span>
              <div className="flex flex-wrap gap-2">
                {accentOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setAccentColor(option.value)}
                    className="h-8 w-8 rounded-[var(--aras-radius)] border border-[var(--aras-border)] ring-offset-2 ring-offset-[var(--aras-panel)]"
                    style={{
                      backgroundColor: option.value,
                      boxShadow: accentColor.toLowerCase() === option.value ? '0 0 0 2px var(--aras-accent)' : undefined,
                    }}
                    title={option.label}
                  />
                ))}
              </div>
            </div>

            <label className="block">
              <span className="mb-1.5 block text-xs font-bold text-[var(--aras-muted)]">Nav Labels</span>
              <SimpleCombobox
                options={[
                  { label: 'Icon + Label', value: 'icon-text' },
                  { label: 'Icon Only', value: 'icon-only' },
                ]}
                value={topbarNavStyle}
                onChange={(val) => setTopbarNavStyle(val as any)}
                width="100%"
              />
            </label>

            <div className="border-t border-[var(--aras-border)] pt-3 space-y-2.5">
              <span className="block text-xs font-bold text-[var(--aras-muted)] uppercase tracking-wider mb-2">Behavior</span>
              <ToggleSwitch label="Inline cell edit in list" value={inlineEdit} onChange={setInlineEdit} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

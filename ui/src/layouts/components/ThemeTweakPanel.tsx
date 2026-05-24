import { useState, useRef, useEffect } from 'react'
import { SlidersHorizontal } from 'lucide-react'
import { useUIStore } from '../../store/uiStore'
import Combobox from '../../aras-core/components/Combobox'

const accentOptions = [
  { label: 'Aras red', value: '#7a2e2e' },
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
  } = useUIStore()

  useEffect(() => {
    if (!open) return

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      if (panelRef.current && !panelRef.current.contains(target)) {
        // Don't close when interacting with Combobox portal dropdowns
        if ((target as Element).closest?.('[data-combobox-dropdown]')) return
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
        className="flex items-center justify-center w-10 h-10 bg-[var(--aras-panel)] rounded-[var(--aras-radius)] shadow-sm border border-[var(--aras-border)] text-[var(--aras-muted)] hover:text-[var(--aras-accent)] hover:border-[var(--aras-accent)] transition-all"
        title="Tweak layout"
      >
        <SlidersHorizontal size={18} />
      </button>

      {open && (
        <div className="absolute right-0 top-full z-[100] mt-2 w-[320px] max-w-[calc(100vw-24px)] rounded-[var(--aras-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel)] p-4 shadow-2xl ring-1 ring-black/5">
          <div className="mb-4">
            <h3 className="text-sm font-bold text-[var(--aras-text)]">Layout Tweaks</h3>
          </div>

          <div className="space-y-4">
            <label className="block">
              <span className="mb-1.5 block text-xs font-bold text-[var(--aras-muted)]">Theme</span>
              <Combobox
                variant="simple"
                options={[
                  { label: 'Light', value: 'light' },
                  { label: 'Normal', value: 'normal' },
                  { label: 'Dark', value: 'dark' }
                ]}
                value={themeMode}
                onChange={(val) => setThemeMode(val as any)}
              />
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="mb-1.5 block text-xs font-bold text-[var(--aras-muted)]">Corners</span>
                <Combobox
                  variant="simple"
                  options={[
                    { label: 'Rounded', value: 'rounded' },
                    { label: 'Square', value: 'square' }
                  ]}
                  value={cornerMode}
                  onChange={(val) => setCornerMode(val as any)}
                />
              </label>

              <label className="block">
                <span className="mb-1.5 block text-xs font-bold text-[var(--aras-muted)]">Layout</span>
                <Combobox
                  variant="simple"
                  options={[
                    { label: 'Compact', value: 'compact' },
                    { label: 'Regular', value: 'regular' },
                    { label: 'Comfy', value: 'comfy' }
                  ]}
                  value={density}
                  onChange={(val) => setDensity(val as any)}
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
              <Combobox
                variant="simple"
                options={[
                  { label: 'Icon + Label', value: 'icon-text' },
                  { label: 'Icon Only', value: 'icon-only' },
                ]}
                value={topbarNavStyle}
                onChange={(val) => setTopbarNavStyle(val as any)}
              />
            </label>
          </div>
        </div>
      )}
    </div>
  )
}

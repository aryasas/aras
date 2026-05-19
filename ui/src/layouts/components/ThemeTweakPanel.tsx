import { useState } from 'react'
import { SlidersHorizontal } from 'lucide-react'
import { useUIStore } from '../../store/uiStore'

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
  } = useUIStore()

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="grid h-14 w-14 place-items-center text-[var(--aras-text)] transition-colors hover:bg-[var(--aras-panel-soft)] max-sm:h-12 max-sm:w-12"
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
              <select
                value={themeMode}
                onChange={(event) => setThemeMode(event.target.value as typeof themeMode)}
                className="h-9 w-full rounded-[var(--aras-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel)] px-3 text-sm text-[var(--aras-text)] outline-none"
              >
                <option value="light">Light</option>
                <option value="normal">Normal</option>
                <option value="dark">Dark</option>
              </select>
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="mb-1.5 block text-xs font-bold text-[var(--aras-muted)]">Corners</span>
                <select
                  value={cornerMode}
                  onChange={(event) => setCornerMode(event.target.value as typeof cornerMode)}
                  className="h-9 w-full rounded-[var(--aras-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel)] px-3 text-sm text-[var(--aras-text)] outline-none"
                >
                  <option value="rounded">Rounded</option>
                  <option value="square">Square</option>
                </select>
              </label>

              <label className="block">
                <span className="mb-1.5 block text-xs font-bold text-[var(--aras-muted)]">Layout</span>
                <select
                  value={density}
                  onChange={(event) => setDensity(event.target.value as typeof density)}
                  className="h-9 w-full rounded-[var(--aras-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel)] px-3 text-sm text-[var(--aras-text)] outline-none"
                >
                  <option value="compact">Compact</option>
                  <option value="regular">Regular</option>
                  <option value="comfy">Comfy</option>
                </select>
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
          </div>
        </div>
      )}
    </div>
  )
}

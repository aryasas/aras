import { useEditor } from '@craftjs/core'
import { Laptop, Smartphone, Tablet, Undo2, Redo2, Wand2, Eye, Pencil, Save } from 'lucide-react'
import { BREAKPOINT_LABELS, BREAKPOINT_ORDER, useBreakpoint } from '../lib/breakpoints'

interface TopbarProps {
  templateName: string
  onTemplateNameChange: (value: string) => void
  zoom: number
  onZoomChange: (value: number) => void
  onSave: () => void
  saving: boolean
}

const viewportIcons = {
  desktop: Laptop,
  tablet: Tablet,
  mobile: Smartphone,
} as const

export function Topbar({
  templateName,
  onTemplateNameChange,
  zoom,
  onZoomChange,
  onSave,
  saving,
}: TopbarProps) {
  const { activeBreakpoint, setActiveBreakpoint } = useBreakpoint()
  const { actions, enabled } = useEditor((state) => ({
    enabled: state.options.enabled,
  }))

  return (
    <div className="template-studio-panel flex items-center justify-between gap-4 rounded-[26px] px-4 py-3">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-[var(--app-radius-lg)] bg-[var(--ts-surface-900)] shadow-md">
          <Wand2 className="h-5 w-5 text-[var(--ts-brand-400)]" />
        </div>
        <div className="min-w-0">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-[var(--ts-surface-500)]">
            Template Studio
          </p>
          <input
            value={templateName}
            onChange={(event) => onTemplateNameChange(event.target.value)}
            className="w-52 border-none bg-transparent p-0 text-base font-bold tracking-tight text-[var(--ts-surface-900)] outline-none"
          />
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-end gap-2">
        <div className="flex items-center gap-1 rounded-[var(--app-radius-lg)] border border-[var(--ts-surface-200)] bg-[var(--app-panel)] p-1">
          {BREAKPOINT_ORDER.map((breakpoint) => {
            const Icon = viewportIcons[breakpoint]
            const active = activeBreakpoint === breakpoint
            return (
              <button
                key={breakpoint}
                type="button"
                onClick={() => setActiveBreakpoint(breakpoint)}
                className={[
                  'inline-flex items-center gap-2 rounded-[var(--app-radius)] px-3 py-2 text-xs font-bold transition-colors',
                  active
                    ? 'bg-[var(--ts-surface-900)] text-[var(--ts-brand-300)]'
                    : 'text-[var(--ts-surface-600)] hover:bg-[var(--ts-surface-50)]',
                ].join(' ')}
              >
                <Icon className="h-4 w-4" />
                <span>{BREAKPOINT_LABELS[breakpoint]}</span>
              </button>
            )
          })}
        </div>

        <div className="flex items-center gap-1 rounded-[var(--app-radius-lg)] border border-[var(--ts-surface-200)] bg-[var(--app-panel)] p-1">
          <button type="button" onClick={() => actions.history.undo()} className="rounded-[var(--app-radius)] p-2 text-[var(--ts-surface-600)] hover:bg-[var(--ts-surface-50)]">
            <Undo2 className="h-4 w-4" />
          </button>
          <button type="button" onClick={() => actions.history.redo()} className="rounded-[var(--app-radius)] p-2 text-[var(--ts-surface-600)] hover:bg-[var(--ts-surface-50)]">
            <Redo2 className="h-4 w-4" />
          </button>
        </div>

        <div className="flex items-center gap-2 rounded-[var(--app-radius-lg)] border border-[var(--ts-surface-200)] bg-[var(--app-panel)] px-3 py-2">
          <span className="text-xs font-bold uppercase tracking-[0.18em] text-[var(--ts-surface-500)]">
            Zoom
          </span>
          <input
            type="range"
            min={50}
            max={150}
            step={5}
            value={zoom}
            onChange={(event) => onZoomChange(Number(event.target.value))}
            className="w-24"
          />
          <span className="w-12 text-right font-mono text-xs font-bold text-[var(--ts-surface-700)]">
            {zoom}%
          </span>
        </div>

        <button
          type="button"
          onClick={() => actions.setOptions((options) => {
            options.enabled = !enabled
          })}
          className="inline-flex items-center gap-2 rounded-[var(--app-radius-lg)] border border-[var(--ts-surface-200)] bg-[var(--app-panel)] px-4 py-2.5 text-sm font-bold text-[var(--ts-surface-700)]"
        >
          {enabled ? <Eye className="h-4 w-4" /> : <Pencil className="h-4 w-4" />}
          <span>{enabled ? 'Preview' : 'Edit'}</span>
        </button>

        <button
          type="button"
          onClick={onSave}
          className="inline-flex items-center gap-2 rounded-[var(--app-radius-lg)] border border-[var(--ts-brand-600)] bg-[var(--ts-brand-500)] px-4 py-2.5 text-sm font-bold text-white shadow-md transition-colors hover:bg-[var(--ts-brand-600)]"
        >
          <Save className="h-4 w-4" />
          <span>{saving ? 'Saving…' : 'Save'}</span>
        </button>
      </div>
    </div>
  )
}

export default Topbar

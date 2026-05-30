import type { CSSProperties, ElementType, ReactNode } from 'react'
import { useRef, useState } from 'react'
import { useEditor, useNode } from '@craftjs/core'
import { DndContext, useDraggable, type DragEndEvent, type DragMoveEvent, type DragStartEvent } from '@dnd-kit/core'
import { GripVertical } from 'lucide-react'
import {
  createResponsiveBoxSettings,
  type BoxSettings,
  type Breakpoint,
  type FlexAlign,
  type FlexJustify,
  type ResponsiveBoxSettings,
  type SpacingSide,
  useBreakpoint,
} from '../lib/breakpoints'

export interface BoxProps {
  label: string
  settings: ResponsiveBoxSettings
  className?: string
  children?: ReactNode
  as?: 'div' | 'section' | 'main' | 'aside' | 'nav'
  fill?: boolean
  minHeight?: number | null
  hiddenOverflow?: boolean
}

type SpacingKind = 'margin' | 'padding'
type DragHandleState = { kind: SpacingKind; side: SpacingSide } | null

const alignMap: Record<FlexAlign, CSSProperties['alignItems']> = {
  start: 'flex-start',
  center: 'center',
  end: 'flex-end',
  stretch: 'stretch',
}

const justifyMap: Record<FlexJustify, CSSProperties['justifyContent']> = {
  start: 'flex-start',
  center: 'center',
  end: 'flex-end',
  between: 'space-between',
}

const handleMeta: Array<{
  kind: SpacingKind
  side: SpacingSide
  label: string
  className: string
}> = [
  { kind: 'margin', side: 'top', label: 'mt', className: 'top-[-12px] left-1/2 -translate-x-1/2' },
  { kind: 'margin', side: 'right', label: 'mr', className: 'right-[-12px] top-1/2 -translate-y-1/2' },
  { kind: 'margin', side: 'bottom', label: 'mb', className: 'bottom-[-12px] left-1/2 -translate-x-1/2' },
  { kind: 'margin', side: 'left', label: 'ml', className: 'left-[-12px] top-1/2 -translate-y-1/2' },
  { kind: 'padding', side: 'top', label: 'pt', className: 'top-[10px] left-1/2 -translate-x-1/2' },
  { kind: 'padding', side: 'right', label: 'pr', className: 'right-[10px] top-1/2 -translate-y-1/2' },
  { kind: 'padding', side: 'bottom', label: 'pb', className: 'bottom-[10px] left-1/2 -translate-x-1/2' },
  { kind: 'padding', side: 'left', label: 'pl', className: 'left-[10px] top-1/2 -translate-y-1/2' },
]

export function useStudioNodeState() {
  const node = useNode((current) => ({
    id: current.id,
    selected: current.events.selected,
    hovered: current.events.hovered,
    note: String(current.data.custom?.note ?? ''),
    locked: Boolean(current.data.custom?.locked),
    hidden: current.data.hidden,
  }))
  const { enabled } = useEditor((state) => ({
    enabled: state.options.enabled,
  }))

  return {
    ...node,
    enabled,
  }
}

export function getBoxSettings(
  settings: ResponsiveBoxSettings,
  breakpoint: Breakpoint,
) {
  return settings[breakpoint]
}

export function boxSettingsToStyle(settings: BoxSettings): CSSProperties {
  return {
    display: 'flex',
    flexDirection: settings.direction === 'row' ? 'row' : 'column',
    alignItems: alignMap[settings.align],
    justifyContent: justifyMap[settings.justify],
    gap: `${settings.gap}px`,
    width: settings.width == null ? undefined : `${settings.width}px`,
    height: settings.height == null ? undefined : `${settings.height}px`,
    marginTop: `${settings.margin?.top ?? 0}px`,
    marginRight: `${settings.margin?.right ?? 0}px`,
    marginBottom: `${settings.margin?.bottom ?? 0}px`,
    marginLeft: `${settings.margin?.left ?? 0}px`,
    paddingTop: `${settings.padding?.top ?? 0}px`,
    paddingRight: `${settings.padding?.right ?? 0}px`,
    paddingBottom: `${settings.padding?.bottom ?? 0}px`,
    paddingLeft: `${settings.padding?.left ?? 0}px`,
    background: settings.bg || undefined,
    borderRadius: settings.radius ? `${settings.radius}px` : undefined,
    minWidth: 0,
  }
}

export function StudioNoteDot({ visible }: { visible: boolean }) {
  if (!visible) return null
  return (
    <span className="template-studio-note-dot absolute right-3 top-3 z-30 h-3 w-3 rounded-full bg-emerald-500" />
  )
}

function SpacingHandle({
  id,
  label,
  className,
  active,
  currentValue,
}: {
  id: string
  label: string
  className: string
  active: boolean
  currentValue: number
}) {
  const { attributes, listeners, setNodeRef } = useDraggable({ id })

  return (
    <button
      ref={setNodeRef}
      type="button"
      className={[
        'absolute z-40 flex h-6 w-6 items-center justify-center rounded-full border text-[9px] font-black uppercase tracking-widest shadow-md',
        className,
        label.startsWith('m')
          ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
          : 'border-sky-300 bg-sky-50 text-sky-700',
      ].join(' ')}
      onPointerDownCapture={(event) => event.stopPropagation()}
      style={{ touchAction: 'none' }}
      {...listeners}
      {...attributes}
    >
      {label}
      {active ? (
        <span className="absolute -top-9 rounded-full bg-[var(--ts-surface-950)] px-2 py-1 font-mono text-[10px] text-white shadow-lg">
          {currentValue}px
        </span>
      ) : null}
    </button>
  )
}

export function StudioSpacingHandles({
  settings,
}: {
  settings: ResponsiveBoxSettings
}) {
  const { activeBreakpoint } = useBreakpoint()
  const { id, setProp } = useNode()
  const [activeHandle, setActiveHandle] = useState<DragHandleState>(null)
  const dragStartValueRef = useRef(0)
  const draggingRef = useRef<DragHandleState>(null)

  const currentSettings = settings[activeBreakpoint]

  const setSpacingValue = (
    kind: SpacingKind,
    side: SpacingSide,
    delta: number,
  ) => {
    const nextValue = Math.max(0, Math.round(dragStartValueRef.current + delta))
    setProp((props: Record<string, any>) => {
      props.settings[activeBreakpoint][kind][side] = nextValue
    })
  }

  const handleDragStart = (event: DragStartEvent) => {
    const [, kind, side] = String(event.active.id).split(':') as [string, SpacingKind, SpacingSide]
    draggingRef.current = { kind, side }
    setActiveHandle({ kind, side })
    dragStartValueRef.current = currentSettings[kind][side]
  }

  const handleDragMove = (event: DragMoveEvent) => {
    if (!draggingRef.current) return
    const delta = draggingRef.current.side === 'left' || draggingRef.current.side === 'right'
      ? event.delta.x
      : event.delta.y
    setSpacingValue(draggingRef.current.kind, draggingRef.current.side, delta)
  }

  const handleDragEnd = (_event: DragEndEvent) => {
    draggingRef.current = null
    setActiveHandle(null)
  }

  return (
    <DndContext onDragStart={handleDragStart} onDragMove={handleDragMove} onDragEnd={handleDragEnd}>
      <div className="pointer-events-none absolute inset-0 z-30 rounded-[inherit]">
        {handleMeta.map((handle) => {
          const isActive = activeHandle?.kind === handle.kind && activeHandle?.side === handle.side
          const currentValue = currentSettings[handle.kind][handle.side]
          return (
            <div key={`${handle.kind}-${handle.side}`} className="pointer-events-none absolute inset-0">
              <div className="pointer-events-auto">
                <SpacingHandle
                  id={`${id}:${handle.kind}:${handle.side}`}
                  label={handle.label}
                  className={handle.className}
                  active={isActive}
                  currentValue={currentValue}
                />
              </div>
            </div>
          )
        })}
      </div>
    </DndContext>
  )
}

export function StudioSelectionChrome({
  label,
  selected,
  hovered,
  enabled,
  noteVisible,
  locked,
  settings,
}: {
  label: string
  selected: boolean
  hovered: boolean
  enabled: boolean
  noteVisible: boolean
  locked: boolean
  settings?: ResponsiveBoxSettings
}) {
  if (!enabled) return null

  return (
    <>
      <StudioNoteDot visible={noteVisible} />
      {(selected || hovered) ? (
        <div
          className={[
            'pointer-events-none absolute inset-0 z-20 rounded-[inherit] border-2 transition-colors',
            selected ? 'border-emerald-400' : 'border-[rgba(20,184,166,0.35)]',
          ].join(' ')}
        />
      ) : null}
      {selected ? (
        <>
          <div className="pointer-events-none absolute left-3 top-3 z-30 flex items-center gap-2 rounded-full bg-[var(--app-panel)]/95 px-2.5 py-1 shadow-md ring-1 ring-[rgba(203,213,225,0.95)]">
            <GripVertical className="h-3 w-3 text-[var(--ts-surface-500)]" />
            <span className="text-[10px] font-black uppercase tracking-[0.18em] text-[var(--ts-surface-700)]">
              {label}
            </span>
            {locked ? (
              <span className="rounded-full bg-amber-100 px-1.5 py-0.5 text-[9px] font-black uppercase tracking-[0.16em] text-amber-700">
                locked
              </span>
            ) : null}
          </div>
          {settings ? <StudioSpacingHandles settings={settings} /> : null}
        </>
      ) : null}
    </>
  )
}

export function Box({
  label,
  settings,
  className,
  children,
  as = 'div',
  fill = false,
  minHeight = null,
  hiddenOverflow = false,
}: BoxProps) {
  const { activeBreakpoint } = useBreakpoint()
  const { connectors: { connect, drag } } = useNode()
  const { selected, hovered, note, locked, enabled } = useStudioNodeState()
  const currentSettings = getBoxSettings(settings, activeBreakpoint)
  const Component = as as ElementType

  return (
    <Component
      ref={(ref: HTMLElement | null) => {
        if (!ref) return
        connect(drag(ref))
      }}
      className={[
        'relative',
        fill ? 'flex-1' : '',
        hiddenOverflow ? 'overflow-hidden' : '',
        className ?? '',
      ].join(' ').trim()}
      style={{
        ...boxSettingsToStyle(currentSettings),
        minHeight: minHeight == null ? undefined : `${minHeight}px`,
      }}
    >
      <StudioSelectionChrome
        label={label}
        selected={selected}
        hovered={hovered}
        enabled={enabled}
        noteVisible={Boolean(note.trim())}
        locked={locked}
        settings={settings}
      />
      {children}
    </Component>
  )
}

Box.craft = {
  displayName: 'Box',
  props: {
    label: 'Box',
    settings: createResponsiveBoxSettings(),
    className: '',
    as: 'div',
    fill: false,
    minHeight: null,
    hiddenOverflow: false,
  },
  custom: {
    note: '',
    locked: false,
    noteStatus: 'pending',
  },
  isCanvas: true,
  rules: {
    canDrag(node: { data: { custom?: { locked?: boolean } } }) {
      return !node.data.custom?.locked
    },
  },
}

export default Box

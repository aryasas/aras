import type { ReactNode } from 'react'
import { useNode } from '@craftjs/core'
import {
  boxSettingsToStyle,
  StudioSelectionChrome,
  useStudioNodeState,
} from './Box'
import {
  createResponsiveBoxSettings,
  createResponsiveColumns,
  type ResponsiveBoxSettings,
  type ResponsiveColumns,
  useBreakpoint,
} from '../lib/breakpoints'

export interface FieldGridProps {
  label: string
  settings: ResponsiveBoxSettings
  cols: ResponsiveColumns
  className?: string
  children?: ReactNode
}

export function FieldGrid({
  label,
  settings,
  cols,
  className,
  children,
}: FieldGridProps) {
  const { activeBreakpoint } = useBreakpoint()
  const { connectors: { connect, drag } } = useNode()
  const { selected, hovered, note, locked, enabled } = useStudioNodeState()
  const currentSettings = settings[activeBreakpoint]

  return (
    <div
      ref={(ref: HTMLDivElement | null) => {
        if (!ref) return
        connect(drag(ref))
      }}
      className={['relative min-w-0', className ?? ''].join(' ').trim()}
      style={{
        ...boxSettingsToStyle(currentSettings),
        display: 'grid',
        gridTemplateColumns: `repeat(${cols[activeBreakpoint]}, minmax(0, 1fr))`,
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
    </div>
  )
}

FieldGrid.craft = {
  displayName: 'FieldGrid',
  props: {
    label: 'Field Grid',
    settings: createResponsiveBoxSettings({
      desktop: { gap: 16 },
      tablet: { gap: 16 },
      mobile: { gap: 12 },
    }),
    cols: createResponsiveColumns(2, 2, 1),
    className: '',
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

export default FieldGrid

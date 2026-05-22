import { useNode } from '@craftjs/core'
import { StudioSelectionChrome, useStudioNodeState } from './Box'

export interface SummaryRowProps {
  label: string
  value: string
  accent: boolean
}

export function SummaryRow({
  label,
  value,
  accent,
}: SummaryRowProps) {
  const { connectors: { connect, drag } } = useNode()
  const { selected, hovered, note, locked, enabled } = useStudioNodeState()

  return (
    <div
      ref={(ref: HTMLDivElement | null) => {
        if (!ref) return
        connect(drag(ref))
      }}
      className={[
        'relative flex items-center justify-between',
        accent
          ? 'mt-1 border-t border-white/10 pt-3 text-base text-white'
          : 'text-sm text-[var(--ts-surface-300)]',
      ].join(' ')}
    >
      <StudioSelectionChrome
        label={label || 'Summary'}
        selected={selected}
        hovered={hovered}
        enabled={enabled}
        noteVisible={Boolean(note.trim())}
        locked={locked}
      />
      <span className={accent ? 'font-bold' : 'font-medium'}>{label}</span>
      <span
        className={[
          'font-mono',
          accent ? 'font-bold text-[var(--ts-brand-300)]' : 'text-white',
        ].join(' ')}
      >
        {value}
      </span>
    </div>
  )
}

SummaryRow.craft = {
  displayName: 'SummaryRow',
  props: {
    label: 'Label',
    value: '$0.00',
    accent: false,
  },
  custom: {
    note: '',
    locked: false,
    noteStatus: 'pending',
  },
  rules: {
    canDrag(node: { data: { custom?: { locked?: boolean } } }) {
      return !node.data.custom?.locked
    },
  },
}

export default SummaryRow

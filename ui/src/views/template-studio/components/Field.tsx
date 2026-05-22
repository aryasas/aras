import { useNode } from '@craftjs/core'
import { ChevronDown } from 'lucide-react'
import { StudioSelectionChrome, useStudioNodeState } from './Box'

export interface FieldProps {
  label: string
  value: string
  placeholder: string
  type: 'input' | 'select' | 'textarea' | 'date'
  fullWidth: boolean
}

const fieldBaseClass = 'w-full rounded-xl border border-[var(--ts-surface-200)] bg-[var(--ts-surface-50)] px-4 py-3 text-sm font-semibold text-[var(--ts-surface-800)] outline-none'

export function Field({
  label,
  value,
  placeholder,
  type,
  fullWidth,
}: FieldProps) {
  const { connectors: { connect, drag } } = useNode()
  const { selected, hovered, note, locked, enabled } = useStudioNodeState()

  return (
    <div
      ref={(ref: HTMLDivElement | null) => {
        if (!ref) return
        connect(drag(ref))
      }}
      className="relative min-w-0"
      style={{ gridColumn: fullWidth ? '1 / -1' : undefined }}
    >
      <StudioSelectionChrome
        label={label || 'Field'}
        selected={selected}
        hovered={hovered}
        enabled={enabled}
        noteVisible={Boolean(note.trim())}
        locked={locked}
      />
      {label ? (
        <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.18em] text-[var(--ts-surface-500)]">
          {label}
        </label>
      ) : null}
      {type === 'textarea' ? (
        <textarea
          readOnly
          rows={2}
          className={`${fieldBaseClass} resize-none`}
          value={value}
          placeholder={placeholder}
        />
      ) : type === 'select' ? (
        <div className="relative">
          <div className={`${fieldBaseClass} cursor-pointer pr-10`}>
            {value || placeholder}
          </div>
          <ChevronDown className="pointer-events-none absolute right-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--ts-surface-400)]" />
        </div>
      ) : (
        <input
          readOnly
          type={type === 'date' ? 'date' : 'text'}
          className={[
            fieldBaseClass,
            type === 'date' ? 'font-mono' : '',
          ].join(' ').trim()}
          value={value}
          placeholder={placeholder}
        />
      )}
    </div>
  )
}

Field.craft = {
  displayName: 'Field',
  props: {
    label: 'Field',
    value: '',
    placeholder: 'Enter value',
    type: 'input',
    fullWidth: false,
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

export default Field

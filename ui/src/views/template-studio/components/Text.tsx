import { useState } from 'react'
import { useNode } from '@craftjs/core'
import { StudioSelectionChrome, useStudioNodeState } from './Box'

export interface TextProps {
  text: string
  variant: 'heading' | 'paragraph' | 'label'
  className?: string
}

function textClass(variant: TextProps['variant']) {
  if (variant === 'heading') {
    return 'text-lg font-bold tracking-tight text-[var(--ts-surface-900)]'
  }
  if (variant === 'label') {
    return 'text-xs font-bold uppercase tracking-[0.22em] text-[var(--ts-surface-500)]'
  }
  return 'text-sm font-medium leading-relaxed text-[var(--ts-surface-700)]'
}

export function Text({
  text,
  variant,
  className,
}: TextProps) {
  const { connectors: { connect, drag }, actions: { setProp } } = useNode()
  const { selected, hovered, note, locked, enabled } = useStudioNodeState()
  const [editing, setEditing] = useState(false)

  const commit = (value: string) => {
    setProp((props: TextProps) => {
      props.text = value
    })
    setEditing(false)
  }

  return (
    <div
      ref={(ref: HTMLDivElement | null) => {
        if (!ref) return
        connect(drag(ref))
      }}
      className={['relative min-w-0', className ?? ''].join(' ').trim()}
      onDoubleClick={() => {
        if (enabled) setEditing(true)
      }}
    >
      <StudioSelectionChrome
        label={text || 'Text'}
        selected={selected}
        hovered={hovered}
        enabled={enabled}
        noteVisible={Boolean(note.trim())}
        locked={locked}
      />
      {editing ? (
        variant === 'paragraph' ? (
          <textarea
            autoFocus
            className="w-full rounded-xl border border-[var(--ts-brand-300)] bg-white px-3 py-2 text-sm font-medium text-[var(--ts-surface-800)] outline-none"
            defaultValue={text}
            rows={3}
            onBlur={(event) => commit(event.target.value)}
          />
        ) : (
          <input
            autoFocus
            className="w-full rounded-xl border border-[var(--ts-brand-300)] bg-white px-3 py-2 text-sm font-semibold text-[var(--ts-surface-800)] outline-none"
            defaultValue={text}
            onBlur={(event) => commit(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
                commit(event.currentTarget.value)
              }
            }}
          />
        )
      ) : (
        <div className={textClass(variant)}>
          <span className={className}>{text}</span>
        </div>
      )}
    </div>
  )
}

Text.craft = {
  displayName: 'Text',
  props: {
    text: 'Text',
    variant: 'paragraph',
    className: '',
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

export default Text

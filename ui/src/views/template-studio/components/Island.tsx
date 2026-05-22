import type { ReactNode } from 'react'
import { useNode } from '@craftjs/core'
import {
  boxSettingsToStyle,
  StudioSelectionChrome,
  useStudioNodeState,
} from './Box'
import {
  createResponsiveBoxSettings,
  type ResponsiveBoxSettings,
  useBreakpoint,
} from '../lib/breakpoints'

export interface IslandProps {
  label: string
  variant: 'light' | 'dark'
  settings: ResponsiveBoxSettings
  title?: string
  titleStyle?: 'section' | 'kicker'
  className?: string
  children?: ReactNode
}

function titleClass(variant: IslandProps['variant'], titleStyle: IslandProps['titleStyle']) {
  if (titleStyle === 'kicker') {
    return variant === 'dark'
      ? 'text-sm font-bold uppercase tracking-[0.22em] text-[var(--ts-surface-300)]'
      : 'text-sm font-bold uppercase tracking-[0.22em] text-[var(--ts-surface-400)]'
  }
  return variant === 'dark'
    ? 'border-b border-white/10 pb-2 text-lg font-bold text-white'
    : 'border-b border-[rgba(226,232,240,0.6)] pb-2 text-lg font-bold text-[var(--ts-surface-900)]'
}

export function Island({
  label,
  variant,
  settings,
  title,
  titleStyle = 'section',
  className,
  children,
}: IslandProps) {
  const { activeBreakpoint } = useBreakpoint()
  const { connectors: { connect, drag } } = useNode()
  const { selected, hovered, note, locked, enabled } = useStudioNodeState()
  const currentSettings = settings[activeBreakpoint]

  return (
    <section
      ref={(ref: HTMLElement | null) => {
        if (!ref) return
        connect(drag(ref))
      }}
      className={[
        'template-studio-island relative min-w-0 overflow-hidden',
        variant === 'light' ? 'template-studio-glass' : '',
        className ?? '',
      ].join(' ').trim()}
      style={{
        ...boxSettingsToStyle(currentSettings),
        background: currentSettings.bg === 'transparent'
          ? variant === 'dark'
            ? 'var(--ts-surface-900)'
            : 'rgba(255, 255, 255, 0.85)'
          : currentSettings.bg,
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
      {variant === 'dark' ? (
        <div className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-[var(--ts-brand-500)] opacity-30 blur-2xl" />
      ) : null}
      {title ? (
        <div className={titleClass(variant, titleStyle)}>
          {title}
        </div>
      ) : null}
      {children}
    </section>
  )
}

Island.craft = {
  displayName: 'Island',
  props: {
    label: 'Island',
    variant: 'light',
    settings: createResponsiveBoxSettings({
      desktop: { padding: { top: 24, right: 24, bottom: 24, left: 24 }, radius: 24, gap: 16, bg: 'transparent' },
      tablet: { padding: { top: 24, right: 24, bottom: 24, left: 24 }, radius: 24, gap: 16, bg: 'transparent' },
      mobile: { padding: { top: 20, right: 20, bottom: 20, left: 20 }, radius: 24, gap: 14, bg: 'transparent' },
    }),
    title: '',
    titleStyle: 'section',
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

export default Island

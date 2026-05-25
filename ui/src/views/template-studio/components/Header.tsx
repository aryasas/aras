import { useNode } from '@craftjs/core'
import { TemplateIcon } from './ButtonEl'
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

export interface HeaderProps {
  label: string
  title: string
  recordId: string
  subtitle: string
  primaryLabel: string
  secondaryLabel: string
  primaryVariant: 'primary' | 'ghost' | 'danger'
  secondaryVariant: 'primary' | 'ghost' | 'danger'
  settings: ResponsiveBoxSettings
  className?: string
}

function buttonClass(variant: HeaderProps['primaryVariant']) {
  if (variant === 'primary') {
    return 'border-[var(--ts-brand-600)] bg-[var(--ts-brand-500)] text-white shadow-md'
  }
  if (variant === 'danger') {
    return 'border-red-200 bg-red-50 text-red-700'
  }
  return 'border-[var(--ts-surface-200)] bg-[var(--app-panel)] text-[var(--ts-surface-700)] shadow-sm'
}

export function Header({
  label,
  title,
  recordId,
  subtitle,
  primaryLabel,
  secondaryLabel,
  primaryVariant,
  secondaryVariant,
  settings,
  className,
}: HeaderProps) {
  const { activeBreakpoint } = useBreakpoint()
  const { connectors: { connect, drag } } = useNode()
  const { selected, hovered, note, locked, enabled } = useStudioNodeState()
  const currentSettings = settings[activeBreakpoint]

  return (
    <header
      ref={(ref: HTMLElement | null) => {
        if (!ref) return
        connect(drag(ref))
      }}
      className={['template-studio-glass template-studio-island relative min-w-0', className ?? ''].join(' ').trim()}
      style={boxSettingsToStyle(currentSettings)}
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
      <div className="flex min-w-0 items-center gap-4">
        <button type="button" className="flex h-10 w-10 items-center justify-center rounded-[var(--app-radius)] border border-[var(--ts-surface-200)] bg-[var(--app-panel)] text-[var(--ts-surface-500)] shadow-sm">
          <TemplateIcon name="arrow-left" className="h-5 w-5" />
        </button>
        <button type="button" className={['inline-flex items-center gap-2 rounded-[var(--app-radius)] border px-5 py-2.5 text-sm font-bold', buttonClass(primaryVariant)].join(' ')}>
          <TemplateIcon name="save" className="h-4 w-4" />
          <span>{primaryLabel}</span>
        </button>
        <div className="min-w-0">
          <h1 className="truncate text-xl font-bold leading-none text-[var(--ts-surface-900)]">
            {title} <span className="font-mono text-[var(--ts-brand-600)]">{recordId}</span>
          </h1>
          <p className="mt-1 text-xs font-medium text-[var(--ts-surface-500)]">{subtitle}</p>
        </div>
      </div>
      <div className="flex flex-1 justify-end">
        <button type="button" className={['rounded-[var(--app-radius)] border px-5 py-2.5 text-sm font-bold', buttonClass(secondaryVariant)].join(' ')}>
          {secondaryLabel}
        </button>
      </div>
    </header>
  )
}

Header.craft = {
  displayName: 'Header',
  props: {
    label: 'Header',
    title: 'Invoice',
    recordId: '#INV-24-092',
    subtitle: 'Editing Record',
    primaryLabel: 'Save Record',
    secondaryLabel: 'Cancel',
    primaryVariant: 'primary',
    secondaryVariant: 'ghost',
    settings: createResponsiveBoxSettings({
      desktop: {
        direction: 'row',
        align: 'center',
        justify: 'between',
        padding: { top: 0, right: 24, bottom: 0, left: 24 },
        height: 80,
        radius: 24,
        gap: 16,
      },
      tablet: {
        direction: 'row',
        align: 'center',
        justify: 'between',
        padding: { top: 0, right: 20, bottom: 0, left: 20 },
        height: 80,
        radius: 24,
        gap: 16,
      },
      mobile: {
        direction: 'col',
        align: 'stretch',
        justify: 'center',
        padding: { top: 18, right: 18, bottom: 18, left: 18 },
        height: null,
        radius: 24,
        gap: 14,
      },
    }),
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

export default Header

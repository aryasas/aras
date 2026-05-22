import type { ReactNode } from 'react'
import { useNode } from '@craftjs/core'
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Box,
  Briefcase,
  Calendar,
  CheckCircle2,
  ChevronDown,
  FileText,
  LayoutGrid,
  Plus,
  Save,
  Settings2,
  ShoppingCart,
  Trash2,
  Users,
  type LucideIcon,
} from 'lucide-react'
import { StudioSelectionChrome, useStudioNodeState } from './Box'

export type IconName =
  | ''
  | 'activity'
  | 'alert-triangle'
  | 'arrow-left'
  | 'box'
  | 'briefcase'
  | 'calendar'
  | 'check-circle-2'
  | 'chevron-down'
  | 'file-text'
  | 'layout-grid'
  | 'plus'
  | 'save'
  | 'settings-2'
  | 'shopping-cart'
  | 'trash-2'
  | 'users'

export interface ButtonElProps {
  label: string
  variant: 'primary' | 'ghost' | 'danger'
  icon: IconName
  className?: string
}

const iconMap: Record<Exclude<IconName, ''>, LucideIcon> = {
  activity: Activity,
  'alert-triangle': AlertTriangle,
  'arrow-left': ArrowLeft,
  box: Box,
  briefcase: Briefcase,
  calendar: Calendar,
  'check-circle-2': CheckCircle2,
  'chevron-down': ChevronDown,
  'file-text': FileText,
  'layout-grid': LayoutGrid,
  plus: Plus,
  save: Save,
  'settings-2': Settings2,
  'shopping-cart': ShoppingCart,
  'trash-2': Trash2,
  users: Users,
}

export function TemplateIcon({
  name,
  className,
}: {
  name: IconName
  className?: string
}) {
  if (!name) return null
  const Icon = iconMap[name]
  return <Icon className={className} />
}

function variantClass(variant: ButtonElProps['variant']) {
  if (variant === 'primary') {
    return 'border-[var(--ts-brand-600)] bg-[var(--ts-brand-500)] text-white shadow-md hover:bg-[var(--ts-brand-600)]'
  }
  if (variant === 'danger') {
    return 'border-red-200 bg-red-50 text-red-700 hover:bg-red-100'
  }
  return 'border-[var(--ts-surface-200)] bg-white text-[var(--ts-surface-700)] hover:bg-[var(--ts-surface-50)]'
}

export function ButtonEl({
  label,
  variant,
  icon,
  className,
}: ButtonElProps) {
  const { connectors: { connect, drag } } = useNode()
  const { selected, hovered, note, locked, enabled } = useStudioNodeState()

  return (
    <div
      ref={(ref: HTMLDivElement | null) => {
        if (!ref) return
        connect(drag(ref))
      }}
      className="relative min-w-0"
    >
      <StudioSelectionChrome
        label={label || 'Button'}
        selected={selected}
        hovered={hovered}
        enabled={enabled}
        noteVisible={Boolean(note.trim())}
        locked={locked}
      />
      <button
        type="button"
        className={[
          'inline-flex min-w-0 items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-bold transition-colors',
          variantClass(variant),
          className ?? '',
        ].join(' ').trim()}
      >
        <ButtonInner icon={icon}>{label}</ButtonInner>
      </button>
    </div>
  )
}

function ButtonInner({
  icon,
  children,
}: {
  icon: IconName
  children: ReactNode
}) {
  return (
    <>
      <TemplateIcon name={icon} className="h-4 w-4 shrink-0" />
      <span className="truncate">{children}</span>
    </>
  )
}

ButtonEl.craft = {
  displayName: 'ButtonEl',
  props: {
    label: 'Button',
    variant: 'primary',
    icon: '' as IconName,
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

export default ButtonEl

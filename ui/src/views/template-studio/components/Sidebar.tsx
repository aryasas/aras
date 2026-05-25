import type { ReactNode } from 'react'
import { useNode } from '@craftjs/core'
import { TemplateIcon, type IconName } from './ButtonEl'
import {
  boxSettingsToStyle,
  StudioSelectionChrome,
  useStudioNodeState,
} from './Box'
import {
  createResponsiveBoxSettings,
  type Breakpoint,
  type ResponsiveBoxSettings,
  useBreakpoint,
} from '../lib/breakpoints'

export interface SidebarItem {
  label: string
  icon: IconName
  active?: boolean
  badge?: string
}

export interface SidebarProps {
  label: string
  brand: string
  bg: string
  width: Record<Breakpoint, number>
  items: SidebarItem[]
  userName: string
  userRole: string
  settings: ResponsiveBoxSettings
  className?: string
  children?: ReactNode
}

export function Sidebar({
  label,
  brand,
  bg,
  width,
  items,
  userName,
  userRole,
  settings,
  className,
  children,
}: SidebarProps) {
  const { activeBreakpoint } = useBreakpoint()
  const { connectors: { connect, drag } } = useNode()
  const { selected, hovered, note, locked, enabled } = useStudioNodeState()
  const currentSettings = settings[activeBreakpoint]
  const compact = width[activeBreakpoint] <= 96

  return (
    <aside
      ref={(ref: HTMLElement | null) => {
        if (!ref) return
        connect(drag(ref))
      }}
      className={['template-studio-glass template-studio-island relative flex shrink-0 flex-col justify-between', className ?? ''].join(' ').trim()}
      style={{
        ...boxSettingsToStyle(currentSettings),
        width: `${width[activeBreakpoint]}px`,
        background: bg || undefined,
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
      <div className="flex h-full flex-col">
        <div className="mb-8 flex h-12 items-center justify-center px-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--app-radius)] bg-[var(--ts-surface-900)] text-white shadow-md">
            <TemplateIcon name="box" className="h-5 w-5 text-[var(--ts-brand-400)]" />
          </div>
          {!compact ? (
            <span className="ml-3 text-xl font-bold tracking-tight text-[var(--ts-surface-900)]">
              {brand}
            </span>
          ) : null}
        </div>

        <nav className="template-studio-hide-scroll flex-1 space-y-2 overflow-y-auto">
          {items.map((item) => (
            <a
              key={`${item.label}-${item.icon}`}
              href="#"
              className={[
                'group flex items-center gap-3 rounded-[var(--app-radius-lg)] border p-3 text-sm transition-all',
                compact ? 'justify-center px-0' : 'px-4',
                item.active
                  ? 'border-[var(--ts-surface-100)] bg-[var(--app-panel)] font-semibold text-[var(--ts-brand-600)] shadow-sm'
                  : 'border-transparent font-medium text-[var(--ts-surface-500)] hover:border-[var(--ts-surface-100)] hover:bg-[var(--app-panel)] hover:text-[var(--ts-surface-900)]',
              ].join(' ')}
            >
              <TemplateIcon
                name={item.icon}
                className={[
                  'h-5 w-5 shrink-0',
                  item.active ? '' : 'group-hover:text-[var(--ts-brand-500)]',
                ].join(' ')}
              />
              {!compact ? <span>{item.label}</span> : null}
              {!compact && item.badge ? (
                <span className="ml-auto rounded-[var(--app-radius)] border border-[var(--ts-brand-200)] bg-[var(--ts-brand-100)] px-2 py-0.5 text-xs font-bold text-[var(--ts-brand-700)]">
                  {item.badge}
                </span>
              ) : null}
            </a>
          ))}
          {children}
        </nav>

        <div className="mt-4 border-t border-[rgba(226,232,240,0.55)] pt-4">
          <div className="flex items-center gap-3 rounded-[var(--app-radius-lg)] border border-[rgba(226,232,240,0.55)] bg-[rgba(241,245,249,0.6)] p-2">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--app-radius)] bg-[var(--ts-surface-900)] text-sm font-bold text-white">
              {userName.slice(0, 1)}
            </div>
            {!compact ? (
              <div className="min-w-0">
                <span className="block truncate text-sm font-bold leading-tight text-[var(--ts-surface-900)]">
                  {userName}
                </span>
                {userRole ? (
                  <span className="block truncate text-xs font-medium text-[var(--ts-surface-500)]">
                    {userRole}
                  </span>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </aside>
  )
}

Sidebar.craft = {
  displayName: 'Sidebar',
  props: {
    label: 'Sidebar',
    brand: 'Nexus',
    bg: 'rgba(255, 255, 255, 0.85)',
    width: { desktop: 256, tablet: 80, mobile: 80 },
    items: [
      { label: 'Dashboard', icon: 'layout-grid', active: false },
      { label: 'Invoice Form', icon: 'file-text', active: true },
    ],
    userName: 'A. Aras',
    userRole: 'System Admin',
    settings: createResponsiveBoxSettings({
      desktop: {
        padding: { top: 16, right: 16, bottom: 16, left: 16 },
        gap: 0,
        radius: 24,
        bg: 'rgba(255, 255, 255, 0.85)',
      },
      tablet: {
        padding: { top: 16, right: 12, bottom: 16, left: 12 },
        gap: 0,
        radius: 24,
        bg: 'rgba(255, 255, 255, 0.85)',
      },
      mobile: {
        padding: { top: 16, right: 12, bottom: 16, left: 12 },
        gap: 0,
        radius: 24,
        bg: 'rgba(255, 255, 255, 0.85)',
      },
    }),
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

export default Sidebar

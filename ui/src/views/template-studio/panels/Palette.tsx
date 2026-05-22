import type { ReactElement } from 'react'
import { Element, useEditor } from '@craftjs/core'
import { LayoutGrid, Sidebar as SidebarIcon, Rows3, SquareStack, Type, Waypoints, RectangleHorizontal, ListOrdered, MousePointer2 } from 'lucide-react'
import Box from '../components/Box'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'
import Island from '../components/Island'
import FieldGrid from '../components/FieldGrid'
import Field from '../components/Field'
import ButtonEl from '../components/ButtonEl'
import SummaryRow from '../components/SummaryRow'
import Text from '../components/Text'
import { createResponsiveBoxSettings, createResponsiveColumns } from '../lib/breakpoints'

interface PaletteItem {
  label: string
  hint: string
  icon: typeof LayoutGrid
  element: () => ReactElement
}

const paletteItems: PaletteItem[] = [
  {
    label: 'Box',
    hint: 'Canvas container',
    icon: SquareStack,
    element: () => (
      <Element
        is={Box}
        canvas
        label="Box"
        settings={createResponsiveBoxSettings({
          desktop: { padding: { top: 16, right: 16, bottom: 16, left: 16 }, gap: 16, radius: 20 },
          tablet: { padding: { top: 16, right: 16, bottom: 16, left: 16 }, gap: 16, radius: 20 },
          mobile: { padding: { top: 14, right: 14, bottom: 14, left: 14 }, gap: 14, radius: 20 },
        })}
        className="template-studio-checker-border"
      />
    ),
  },
  {
    label: 'Sidebar',
    hint: 'ERP navigation rail',
    icon: SidebarIcon,
    element: () => (
      <Element
        is={Sidebar}
        canvas
        label="Sidebar"
        brand="Nexus"
        bg="rgba(255, 255, 255, 0.85)"
        width={{ desktop: 256, tablet: 80, mobile: 80 }}
        items={[
          { label: 'Dashboard', icon: 'layout-grid', active: false },
          { label: 'Invoice Form', icon: 'file-text', active: true },
        ]}
        userName="A. Aras"
        userRole="System Admin"
        settings={createResponsiveBoxSettings({
          desktop: { padding: { top: 16, right: 16, bottom: 16, left: 16 }, gap: 0, radius: 24, bg: 'rgba(255, 255, 255, 0.85)' },
          tablet: { padding: { top: 16, right: 12, bottom: 16, left: 12 }, gap: 0, radius: 24, bg: 'rgba(255, 255, 255, 0.85)' },
          mobile: { padding: { top: 16, right: 12, bottom: 16, left: 12 }, gap: 0, radius: 24, bg: 'rgba(255, 255, 255, 0.85)' },
        })}
      />
    ),
  },
  {
    label: 'Header',
    hint: 'Back, title, save row',
    icon: Rows3,
    element: () => (
      <Header
        label="Header"
        title="Invoice"
        recordId="#INV-24-092"
        subtitle="Editing Record"
        primaryLabel="Save Record"
        secondaryLabel="Cancel"
        primaryVariant="primary"
        secondaryVariant="ghost"
        settings={createResponsiveBoxSettings({
          desktop: { direction: 'row', align: 'center', justify: 'between', padding: { top: 0, right: 24, bottom: 0, left: 24 }, height: 80, radius: 24, gap: 16 },
          tablet: { direction: 'row', align: 'center', justify: 'between', padding: { top: 0, right: 20, bottom: 0, left: 20 }, height: 80, radius: 24, gap: 16 },
          mobile: { direction: 'col', align: 'stretch', justify: 'center', padding: { top: 18, right: 18, bottom: 18, left: 18 }, height: null, radius: 24, gap: 14 },
        })}
      />
    ),
  },
  {
    label: 'Island',
    hint: 'Light or dark panel',
    icon: RectangleHorizontal,
    element: () => (
      <Element
        is={Island}
        canvas
        label="Island"
        variant="light"
        settings={createResponsiveBoxSettings({
          desktop: { padding: { top: 24, right: 24, bottom: 24, left: 24 }, gap: 16, radius: 24, bg: 'transparent' },
          tablet: { padding: { top: 24, right: 24, bottom: 24, left: 24 }, gap: 16, radius: 24, bg: 'transparent' },
          mobile: { padding: { top: 20, right: 20, bottom: 20, left: 20 }, gap: 14, radius: 24, bg: 'transparent' },
        })}
        title="Section Title"
      />
    ),
  },
  {
    label: 'Field Grid',
    hint: 'Responsive field columns',
    icon: LayoutGrid,
    element: () => (
      <Element
        is={FieldGrid}
        canvas
        label="Field Grid"
        settings={createResponsiveBoxSettings({
          desktop: { gap: 16 },
          tablet: { gap: 16 },
          mobile: { gap: 12 },
        })}
        cols={createResponsiveColumns(2, 2, 1)}
      />
    ),
  },
  {
    label: 'Field',
    hint: 'Input, select, date, textarea',
    icon: Waypoints,
    element: () => <Field label="Field" value="" placeholder="Enter value" type="input" fullWidth={false} />,
  },
  {
    label: 'Button',
    hint: 'Primary, ghost, danger',
    icon: MousePointer2,
    element: () => <ButtonEl label="Action" variant="primary" icon="" />,
  },
  {
    label: 'Summary Row',
    hint: 'Invoice total row',
    icon: ListOrdered,
    element: () => <SummaryRow label="Subtotal" value="$0.00" accent={false} />,
  },
  {
    label: 'Text',
    hint: 'Inline editable copy',
    icon: Type,
    element: () => <Text text="Text block" variant="paragraph" />,
  },
]

export function Palette() {
  const { connectors: { create } } = useEditor()

  return (
    <div className="space-y-3 p-4">
      <div>
        <p className="text-[11px] font-black uppercase tracking-[0.24em] text-[var(--ts-surface-500)]">
          Palette
        </p>
        <p className="mt-1 text-xs leading-relaxed text-[var(--ts-surface-500)]">
          Drag blocks into any Craft container. Container components expose edge handles only when selected.
        </p>
      </div>
      <div className="space-y-2">
        {paletteItems.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.label}
              ref={(ref: HTMLButtonElement | null) => {
                if (!ref) return
                create(ref, item.element())
              }}
              type="button"
              className="flex w-full cursor-grab items-center gap-3 rounded-2xl border border-[var(--ts-surface-200)] bg-white px-3 py-3 text-left transition-all hover:border-[var(--ts-brand-300)] hover:shadow-sm active:cursor-grabbing"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--ts-surface-100)] text-[var(--ts-surface-600)]">
                <Icon className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-bold text-[var(--ts-surface-900)]">{item.label}</div>
                <div className="truncate text-xs text-[var(--ts-surface-500)]">{item.hint}</div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default Palette

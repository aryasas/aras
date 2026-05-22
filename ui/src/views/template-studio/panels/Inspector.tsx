import { useMemo, useState } from 'react'
import { useEditor } from '@craftjs/core'
import { ArrowDown, ArrowUp, Copy, Eye, EyeOff, Lock, Trash2, Unlock } from 'lucide-react'
import type { IconName } from '../components/ButtonEl'
import { BREAKPOINT_LABELS, BREAKPOINT_ORDER, type Breakpoint, type ResponsiveBoxSettings, type ResponsiveColumns } from '../lib/breakpoints'

const inputClass = 'w-full rounded-xl border border-[var(--ts-surface-200)] bg-white px-3 py-2 text-sm text-[var(--ts-surface-800)] outline-none'
const labelClass = 'text-[11px] font-black uppercase tracking-[0.18em] text-[var(--ts-surface-500)]'

function inferLabel(node: { data: { displayName: string; props: Record<string, unknown> } }) {
  const props = node.data.props
  return String(props.label ?? props.title ?? props.text ?? props.brand ?? props.userName ?? node.data.displayName)
}

function cloneNodeTreeWithFreshIds(tree: any) {
  const idMap = new Map<string, string>()

  Object.keys(tree.nodes).forEach((id) => {
    idMap.set(id, `node-${crypto.randomUUID()}`)
  })

  const nextNodes = Object.fromEntries(
    Object.entries<any>(tree.nodes).map(([id, node]) => {
      const nextId = idMap.get(id)!
      const linkedNodes = Object.fromEntries(
        Object.entries<string>(node.data.linkedNodes ?? {}).map(([key, childId]) => [key, idMap.get(childId)!]),
      )
      return [
        nextId,
        {
          ...node,
          id: nextId,
          data: {
            ...node.data,
            parent: node.data.parent ? idMap.get(node.data.parent) ?? node.data.parent : node.data.parent,
            nodes: (node.data.nodes ?? []).map((childId: string) => idMap.get(childId)!),
            linkedNodes,
          },
        },
      ]
    }),
  )

  return {
    rootNodeId: idMap.get(tree.rootNodeId)!,
    nodes: nextNodes,
  }
}

function NumberInput({
  label,
  value,
  onChange,
  allowBlank = false,
}: {
  label: string
  value: number | null
  onChange: (value: number | null) => void
  allowBlank?: boolean
}) {
  return (
    <label className="space-y-1">
      <span className={labelClass}>{label}</span>
      <input
        type="number"
        value={value ?? ''}
        onChange={(event) => {
          if (allowBlank && event.target.value === '') {
            onChange(null)
            return
          }
          onChange(Number(event.target.value) || 0)
        }}
        className={inputClass}
      />
    </label>
  )
}

function TextInput({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <label className="space-y-1">
      <span className={labelClass}>{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={inputClass}
      />
    </label>
  )
}

function SelectInput({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: Array<{ label: string; value: string }>
  onChange: (value: string) => void
}) {
  return (
    <label className="space-y-1">
      <span className={labelClass}>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className={inputClass}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  )
}

function BreakpointAccordion({
  breakpoint,
  open,
  onToggle,
  children,
}: {
  breakpoint: Breakpoint
  open: boolean
  onToggle: () => void
  children: React.ReactNode
}) {
  return (
    <div className="rounded-2xl border border-[var(--ts-surface-200)] bg-white">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-sm font-bold text-[var(--ts-surface-900)]">{BREAKPOINT_LABELS[breakpoint]}</span>
        <span className="text-xs font-black uppercase tracking-[0.18em] text-[var(--ts-surface-500)]">
          {open ? 'Hide' : 'Show'}
        </span>
      </button>
      {open ? <div className="grid grid-cols-2 gap-3 border-t border-[var(--ts-surface-100)] px-4 py-4">{children}</div> : null}
    </div>
  )
}

export function Inspector() {
  const { selected, nodes, actions, query } = useEditor((state) => ({
    selected: state.events.selected,
    nodes: state.nodes,
  }))
  const selectedId = Array.from(selected)[0] ?? null
  const selectedNode = selectedId ? nodes[selectedId] : null
  const [openPanels, setOpenPanels] = useState<Record<Breakpoint, boolean>>({
    desktop: true,
    tablet: true,
    mobile: true,
  })

  const parentInfo = useMemo(() => {
    if (!selectedId || !selectedNode) return null
    const parentId = selectedNode.data.parent
    if (!parentId) return null
    const parent = nodes[parentId]
    if (!parent) return null
    const index = parent.data.nodes.indexOf(selectedId)
    return { parentId, index, siblings: parent.data.nodes.length }
  }, [nodes, selectedId, selectedNode])

  if (!selectedId || !selectedNode) {
    return (
      <div className="p-4">
        <div className="rounded-[24px] border border-dashed border-[var(--ts-surface-300)] bg-white/70 p-5 text-sm text-[var(--ts-surface-500)]">
          Select a node on the canvas to edit its AI note, responsive properties, and structure actions.
        </div>
      </div>
    )
  }

  const props = selectedNode.data.props as Record<string, any>
  const displayName = selectedNode.data.displayName
  const isContainer = ['Box', 'Sidebar', 'Header', 'Island', 'FieldGrid'].includes(displayName)
  const label = inferLabel(selectedNode)
  const hidden = selectedNode.data.hidden
  const locked = Boolean(selectedNode.data.custom?.locked)
  const settings = props.settings as ResponsiveBoxSettings | undefined
  const cols = props.cols as ResponsiveColumns | undefined
  const widths = props.width as Record<Breakpoint, number> | undefined

  const setPropValue = (key: string, value: unknown) => {
    actions.setProp(selectedId, (currentProps: Record<string, unknown>) => {
      currentProps[key] = value
    })
  }

  const setResponsiveSetting = (
    breakpoint: Breakpoint,
    path: Array<string>,
    value: string | number | null,
  ) => {
    actions.setProp(selectedId, (currentProps: { settings: ResponsiveBoxSettings }) => {
      let target: any = currentProps.settings[breakpoint]
      for (const key of path.slice(0, -1)) {
        target = target[key]
      }
      target[path[path.length - 1]] = value
    })
  }

  const duplicateSelected = () => {
    if (!parentInfo) return
    const tree = query.node(selectedId).toNodeTree()
    const clonedTree = cloneNodeTreeWithFreshIds(tree)
    actions.addNodeTree(clonedTree, parentInfo.parentId, parentInfo.index + 1)
  }

  const moveSelected = (direction: -1 | 1) => {
    if (!parentInfo) return
    const nextIndex = parentInfo.index + direction
    if (nextIndex < 0 || nextIndex >= parentInfo.siblings) return
    actions.move(selectedId, parentInfo.parentId, nextIndex)
  }

  return (
    <div className="space-y-4 p-4">
      <div className="rounded-[24px] border border-emerald-200 bg-[linear-gradient(180deg,rgba(236,253,245,0.9),rgba(255,255,255,0.95))] p-4">
        <div className="mb-2">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-emerald-700">
            AI Instruction
          </p>
          <p className="mt-1 text-xs text-emerald-700/80">
            Saved to <code className="font-mono">dev_template_annotations</code> when you hit Save.
          </p>
        </div>
        <textarea
          rows={5}
          value={String(selectedNode.data.custom?.note ?? '')}
          onChange={(event) => {
            actions.setCustom(selectedId, (custom: Record<string, unknown>) => {
              custom.note = event.target.value
              custom.noteStatus = 'pending'
            })
          }}
          placeholder={`Instruction for ${label}`}
          className="w-full rounded-2xl border border-emerald-200 bg-white px-3 py-3 text-sm text-[var(--ts-surface-800)] outline-none"
        />
      </div>

      <div className="rounded-[24px] border border-[var(--ts-surface-200)] bg-white p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-[var(--ts-surface-500)]">
              Properties
            </p>
            <p className="mt-1 text-sm font-bold text-[var(--ts-surface-900)]">{label}</p>
          </div>
          <span className="rounded-full bg-[var(--ts-surface-100)] px-2 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--ts-surface-500)]">
            {displayName}
          </span>
        </div>

        {isContainer && settings ? (
          <div className="space-y-3">
            {BREAKPOINT_ORDER.map((breakpoint) => (
              <BreakpointAccordion
                key={breakpoint}
                breakpoint={breakpoint}
                open={openPanels[breakpoint]}
                onToggle={() => setOpenPanels((current) => ({ ...current, [breakpoint]: !current[breakpoint] }))}
              >
                <NumberInput label="Margin Top" value={settings[breakpoint].margin.top} onChange={(value) => setResponsiveSetting(breakpoint, ['margin', 'top'], value ?? 0)} />
                <NumberInput label="Margin Right" value={settings[breakpoint].margin.right} onChange={(value) => setResponsiveSetting(breakpoint, ['margin', 'right'], value ?? 0)} />
                <NumberInput label="Margin Bottom" value={settings[breakpoint].margin.bottom} onChange={(value) => setResponsiveSetting(breakpoint, ['margin', 'bottom'], value ?? 0)} />
                <NumberInput label="Margin Left" value={settings[breakpoint].margin.left} onChange={(value) => setResponsiveSetting(breakpoint, ['margin', 'left'], value ?? 0)} />
                <NumberInput label="Padding Top" value={settings[breakpoint].padding.top} onChange={(value) => setResponsiveSetting(breakpoint, ['padding', 'top'], value ?? 0)} />
                <NumberInput label="Padding Right" value={settings[breakpoint].padding.right} onChange={(value) => setResponsiveSetting(breakpoint, ['padding', 'right'], value ?? 0)} />
                <NumberInput label="Padding Bottom" value={settings[breakpoint].padding.bottom} onChange={(value) => setResponsiveSetting(breakpoint, ['padding', 'bottom'], value ?? 0)} />
                <NumberInput label="Padding Left" value={settings[breakpoint].padding.left} onChange={(value) => setResponsiveSetting(breakpoint, ['padding', 'left'], value ?? 0)} />
                <NumberInput label="Width" value={settings[breakpoint].width} allowBlank onChange={(value) => setResponsiveSetting(breakpoint, ['width'], value)} />
                <NumberInput label="Height" value={settings[breakpoint].height} allowBlank onChange={(value) => setResponsiveSetting(breakpoint, ['height'], value)} />
                <NumberInput label="Gap" value={settings[breakpoint].gap} onChange={(value) => setResponsiveSetting(breakpoint, ['gap'], value ?? 0)} />
                <NumberInput label="Radius" value={settings[breakpoint].radius} onChange={(value) => setResponsiveSetting(breakpoint, ['radius'], value ?? 0)} />
                <TextInput label="Background" value={settings[breakpoint].bg} onChange={(value) => setResponsiveSetting(breakpoint, ['bg'], value)} />
                <SelectInput
                  label="Direction"
                  value={settings[breakpoint].direction}
                  options={[
                    { label: 'Column', value: 'col' },
                    { label: 'Row', value: 'row' },
                  ]}
                  onChange={(value) => setResponsiveSetting(breakpoint, ['direction'], value)}
                />
                <SelectInput
                  label="Align"
                  value={settings[breakpoint].align}
                  options={[
                    { label: 'Stretch', value: 'stretch' },
                    { label: 'Start', value: 'start' },
                    { label: 'Center', value: 'center' },
                    { label: 'End', value: 'end' },
                  ]}
                  onChange={(value) => setResponsiveSetting(breakpoint, ['align'], value)}
                />
                <SelectInput
                  label="Justify"
                  value={settings[breakpoint].justify}
                  options={[
                    { label: 'Start', value: 'start' },
                    { label: 'Center', value: 'center' },
                    { label: 'End', value: 'end' },
                    { label: 'Between', value: 'between' },
                  ]}
                  onChange={(value) => setResponsiveSetting(breakpoint, ['justify'], value)}
                />
                {displayName === 'Sidebar' && widths ? (
                  <NumberInput
                    label="Sidebar Width"
                    value={widths[breakpoint]}
                    onChange={(value) => {
                      actions.setProp(selectedId, (currentProps: { width: Record<Breakpoint, number> }) => {
                        currentProps.width[breakpoint] = value ?? 0
                      })
                    }}
                  />
                ) : null}
                {displayName === 'FieldGrid' && cols ? (
                  <SelectInput
                    label="Columns"
                    value={String(cols[breakpoint])}
                    options={[
                      { label: '1', value: '1' },
                      { label: '2', value: '2' },
                      { label: '3', value: '3' },
                    ]}
                    onChange={(value) => {
                      actions.setProp(selectedId, (currentProps: { cols: ResponsiveColumns }) => {
                        currentProps.cols[breakpoint] = Number(value) as 1 | 2 | 3
                      })
                    }}
                  />
                ) : null}
              </BreakpointAccordion>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {displayName === 'Field' ? (
              <>
                <TextInput label="Label" value={props.label} onChange={(value) => setPropValue('label', value)} />
                <TextInput label="Value" value={props.value} onChange={(value) => setPropValue('value', value)} />
                <TextInput label="Placeholder" value={props.placeholder} onChange={(value) => setPropValue('placeholder', value)} />
                <SelectInput
                  label="Type"
                  value={props.type}
                  options={[
                    { label: 'Input', value: 'input' },
                    { label: 'Select', value: 'select' },
                    { label: 'Textarea', value: 'textarea' },
                    { label: 'Date', value: 'date' },
                  ]}
                  onChange={(value) => setPropValue('type', value)}
                />
                <SelectInput
                  label="Full Width"
                  value={String(props.fullWidth)}
                  options={[
                    { label: 'False', value: 'false' },
                    { label: 'True', value: 'true' },
                  ]}
                  onChange={(value) => setPropValue('fullWidth', value === 'true')}
                />
              </>
            ) : null}
            {displayName === 'ButtonEl' ? (
              <>
                <TextInput label="Label" value={props.label} onChange={(value) => setPropValue('label', value)} />
                <SelectInput
                  label="Variant"
                  value={props.variant}
                  options={[
                    { label: 'Primary', value: 'primary' },
                    { label: 'Ghost', value: 'ghost' },
                    { label: 'Danger', value: 'danger' },
                  ]}
                  onChange={(value) => setPropValue('variant', value)}
                />
                <TextInput label="Icon" value={props.icon as IconName} onChange={(value) => setPropValue('icon', value as IconName)} />
              </>
            ) : null}
            {displayName === 'SummaryRow' ? (
              <>
                <TextInput label="Label" value={props.label} onChange={(value) => setPropValue('label', value)} />
                <TextInput label="Value" value={props.value} onChange={(value) => setPropValue('value', value)} />
                <SelectInput
                  label="Accent"
                  value={String(props.accent)}
                  options={[
                    { label: 'False', value: 'false' },
                    { label: 'True', value: 'true' },
                  ]}
                  onChange={(value) => setPropValue('accent', value === 'true')}
                />
              </>
            ) : null}
            {displayName === 'Text' ? (
              <>
                <TextInput label="Text" value={props.text} onChange={(value) => setPropValue('text', value)} />
                <SelectInput
                  label="Variant"
                  value={props.variant}
                  options={[
                    { label: 'Heading', value: 'heading' },
                    { label: 'Paragraph', value: 'paragraph' },
                    { label: 'Label', value: 'label' },
                  ]}
                  onChange={(value) => setPropValue('variant', value)}
                />
              </>
            ) : null}
          </div>
        )}

        {displayName === 'Sidebar' ? (
          <div className="mt-4 grid grid-cols-2 gap-3 border-t border-[var(--ts-surface-100)] pt-4">
            <TextInput label="Brand" value={props.brand} onChange={(value) => setPropValue('brand', value)} />
            <TextInput label="User Name" value={props.userName} onChange={(value) => setPropValue('userName', value)} />
            <TextInput label="User Role" value={props.userRole} onChange={(value) => setPropValue('userRole', value)} />
            <label className="col-span-2 space-y-1">
              <span className={labelClass}>Items JSON</span>
              <textarea
                rows={6}
                defaultValue={JSON.stringify(props.items, null, 2)}
                onBlur={(event) => {
                  try {
                    setPropValue('items', JSON.parse(event.target.value))
                  } catch {
                    console.warn('Invalid sidebar items JSON')
                  }
                }}
                className={`${inputClass} font-mono text-xs`}
              />
            </label>
          </div>
        ) : null}

        {displayName === 'Header' ? (
          <div className="mt-4 grid grid-cols-2 gap-3 border-t border-[var(--ts-surface-100)] pt-4">
            <TextInput label="Title" value={props.title} onChange={(value) => setPropValue('title', value)} />
            <TextInput label="Record Id" value={props.recordId} onChange={(value) => setPropValue('recordId', value)} />
            <TextInput label="Subtitle" value={props.subtitle} onChange={(value) => setPropValue('subtitle', value)} />
            <TextInput label="Primary Label" value={props.primaryLabel} onChange={(value) => setPropValue('primaryLabel', value)} />
            <TextInput label="Secondary Label" value={props.secondaryLabel} onChange={(value) => setPropValue('secondaryLabel', value)} />
            <SelectInput
              label="Primary Variant"
              value={props.primaryVariant}
              options={[
                { label: 'Primary', value: 'primary' },
                { label: 'Ghost', value: 'ghost' },
                { label: 'Danger', value: 'danger' },
              ]}
              onChange={(value) => setPropValue('primaryVariant', value)}
            />
            <SelectInput
              label="Secondary Variant"
              value={props.secondaryVariant}
              options={[
                { label: 'Primary', value: 'primary' },
                { label: 'Ghost', value: 'ghost' },
                { label: 'Danger', value: 'danger' },
              ]}
              onChange={(value) => setPropValue('secondaryVariant', value)}
            />
          </div>
        ) : null}

        {displayName === 'Island' ? (
          <div className="mt-4 grid grid-cols-2 gap-3 border-t border-[var(--ts-surface-100)] pt-4">
            <TextInput label="Title" value={props.title ?? ''} onChange={(value) => setPropValue('title', value)} />
            <SelectInput
              label="Variant"
              value={props.variant}
              options={[
                { label: 'Light', value: 'light' },
                { label: 'Dark', value: 'dark' },
              ]}
              onChange={(value) => setPropValue('variant', value)}
            />
            <SelectInput
              label="Title Style"
              value={props.titleStyle}
              options={[
                { label: 'Section', value: 'section' },
                { label: 'Kicker', value: 'kicker' },
              ]}
              onChange={(value) => setPropValue('titleStyle', value)}
            />
          </div>
        ) : null}
      </div>

      <div className="rounded-[24px] border border-[var(--ts-surface-200)] bg-white p-4">
        <p className="mb-3 text-[11px] font-black uppercase tracking-[0.24em] text-[var(--ts-surface-500)]">
          Actions
        </p>
        <div className="grid grid-cols-2 gap-2">
          <button type="button" onClick={() => actions.setHidden(selectedId, !hidden)} className="inline-flex items-center justify-center gap-2 rounded-xl border border-[var(--ts-surface-200)] px-3 py-2 text-sm font-bold text-[var(--ts-surface-700)]">
            {hidden ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            <span>{hidden ? 'Show' : 'Hide'}</span>
          </button>
          <button type="button" onClick={() => actions.setCustom(selectedId, (custom: Record<string, unknown>) => { custom.locked = !locked })} className="inline-flex items-center justify-center gap-2 rounded-xl border border-[var(--ts-surface-200)] px-3 py-2 text-sm font-bold text-[var(--ts-surface-700)]">
            {locked ? <Unlock className="h-4 w-4" /> : <Lock className="h-4 w-4" />}
            <span>{locked ? 'Unlock' : 'Lock'}</span>
          </button>
          <button type="button" onClick={duplicateSelected} disabled={!parentInfo} className="inline-flex items-center justify-center gap-2 rounded-xl border border-[var(--ts-surface-200)] px-3 py-2 text-sm font-bold text-[var(--ts-surface-700)] disabled:opacity-40">
            <Copy className="h-4 w-4" />
            <span>Duplicate</span>
          </button>
          <button type="button" onClick={() => actions.delete(selectedId)} disabled={!query.node(selectedId).isDeletable()} className="inline-flex items-center justify-center gap-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm font-bold text-red-700 disabled:opacity-40">
            <Trash2 className="h-4 w-4" />
            <span>Delete</span>
          </button>
          <button type="button" onClick={() => moveSelected(-1)} disabled={!parentInfo || parentInfo.index === 0} className="inline-flex items-center justify-center gap-2 rounded-xl border border-[var(--ts-surface-200)] px-3 py-2 text-sm font-bold text-[var(--ts-surface-700)] disabled:opacity-40">
            <ArrowUp className="h-4 w-4" />
            <span>Move Up</span>
          </button>
          <button type="button" onClick={() => moveSelected(1)} disabled={!parentInfo || parentInfo.index === parentInfo.siblings - 1} className="inline-flex items-center justify-center gap-2 rounded-xl border border-[var(--ts-surface-200)] px-3 py-2 text-sm font-bold text-[var(--ts-surface-700)] disabled:opacity-40">
            <ArrowDown className="h-4 w-4" />
            <span>Move Down</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default Inspector

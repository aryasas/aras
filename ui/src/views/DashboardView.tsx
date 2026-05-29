// claude-opus-4-7
// ARC dashboard: bento grid of widgets. Drag-reorder using @dnd-kit through DnDGrid.
// Stat widgets are mono-readout; charts keep their data viz but live inside arc-cards.
import React, { useCallback, useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { useAras } from '../aras-core/hooks/useAras'
import { resolveIcon } from '../lib/iconUtils'
import { LoadingState } from '../components/LoadingState'
import { EmptyState } from '../components/EmptyState'
import { useUIStore } from '../store/uiStore'
import {
  DndContext, KeyboardSensor, PointerSensor, closestCenter, useSensor, useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import { SortableContext, rectSortingStrategy, useSortable, sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical } from 'lucide-react'

interface Widget {
  id: number
  name: string
  title: string
  widget_type: 'stat' | 'chart' | 'list' | string
  resource_name: string
  config_json: any
  size: string
}

type WidgetComponent = React.FC<{ widget: Widget }>
const registry = new Map<string, WidgetComponent>()
export const WidgetRegistry = {
  register(type: string, Component: WidgetComponent) { registry.set(type, Component) },
  get(type: string) { return registry.get(type) },
}

function SortableTile({ widget }: { widget: Widget }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: widget.id })
  const Component = WidgetRegistry.get(widget.widget_type)
  if (!Component) return null
  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }
  return (
    <div ref={setNodeRef} style={style} className={`relative ${widget.size || 'col-span-1'}`}>
      <button
        {...attributes}
        {...(listeners as any)}
        aria-label="Drag to reorder"
        className="arc-dnd-handle absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius-sm)]"
      >
        <GripVertical size={14} />
      </button>
      <div className="group h-full">
        <Component widget={widget} />
      </div>
    </div>
  )
}

export const DashboardView: React.FC = () => {
  const [widgets, setWidgets] = useState<Widget[]>([])
  const [loading, setLoading] = useState(true)
  const { notify } = useAras()
  const setPageTitle = useUIStore((state) => state.setPageTitle)
  const location = useLocation()
  const appKey = location.pathname.split('/').filter(Boolean)[0] || 'dashboard'
  const orderPreferenceKey = `dashboard:${appKey}:order`

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  useEffect(() => {
    setPageTitle('Dashboard', 'Real-time overview of your operations and performance.', 'HOME')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  const loadWidgets = useCallback(async () => {
    try {
      const res = await api.get('/dashboard/widgets')
      let nextWidgets = res.data.layout_config?.widgets || []
      try {
        const pref = await api.get('/preference', { params: { key: orderPreferenceKey } })
        const saved = typeof pref.data?.value === 'string' ? JSON.parse(pref.data.value) : pref.data?.value
        if (Array.isArray(saved)) {
          const byId = new Map(nextWidgets.map((widget: Widget) => [widget.id, widget]))
          const ordered = saved.map((id: number) => byId.get(id)).filter(Boolean) as Widget[]
          const remaining = nextWidgets.filter((widget: Widget) => !saved.includes(widget.id))
          nextWidgets = [...ordered, ...remaining]
        }
      } catch {
        // Missing preferences should not block the dashboard.
      }
      setWidgets(nextWidgets)
    } catch (err: any) {
      notify(err.message || 'Failed to load dashboard widgets', 'error')
    } finally {
      setLoading(false)
    }
  }, [notify, orderPreferenceKey])

  useEffect(() => { loadWidgets() }, [loadWidgets])

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const oldIndex = widgets.findIndex((w) => w.id === active.id)
    const newIndex = widgets.findIndex((w) => w.id === over.id)
    if (oldIndex < 0 || newIndex < 0) return
    const next = [...widgets]
    const [moved] = next.splice(oldIndex, 1)
    next.splice(newIndex, 0, moved)
    setWidgets(next)
    api.put('/preference', { key: orderPreferenceKey, value: JSON.stringify(next.map((w) => w.id)) })
      .catch((e) => notify(e.message || 'Failed to save dashboard layout', 'error'))
  }

  if (loading) return <LoadingState label="Loading dashboard..." className="arc-card p-12" />
  if (widgets.length === 0) return <EmptyState title="No dashboard widgets" description="Dashboard widgets will appear here when configured." />

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={widgets.map((w) => w.id)} strategy={rectSortingStrategy}>
        <div className="arc grid grid-cols-1 md:grid-cols-4 gap-4">
          {widgets.map((widget) => <SortableTile key={widget.id} widget={widget} />)}
        </div>
      </SortableContext>
    </DndContext>
  )
}

const ChartWidget: WidgetComponent = ({ widget }) => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const config = widget.config_json || {}
  const { notify } = useAras()

  useEffect(() => {
    api.get(`/${widget.resource_name}`).then((res: any) => {
      const items = res.data.items || res.data || []
      const groupBy = config.group_by || 'status'
      const counts: Record<string, number> = {}
      items.forEach((item: any) => {
        const key = item[groupBy] || 'Other'
        counts[key] = (counts[key] || 0) + 1
      })
      setData(Object.entries(counts).map(([name, value]) => ({ name, value })))
      setLoading(false)
    }).catch((e) => { notify(e.message, 'error'); setLoading(false) })
  }, [widget.resource_name, config.group_by, notify])

  if (loading) return <div className="arc-card p-6 h-64 animate-pulse" />

  const maxValue = Math.max(...data.map((d) => d.value), 1)
  const total = data.reduce((sum, curr) => sum + curr.value, 0) || 1
  const colors = ['var(--accent)', '#10b981', 'var(--warn)', 'var(--danger)', 'var(--info)', '#a78bfa']

  return (
    <div className="arc-card overflow-hidden h-full flex flex-col">
      <div className="px-4 py-2.5 border-b border-[var(--line)] flex items-center justify-between" style={{ background: 'var(--surface-2)' }}>
        <span className="arc-id"><b>chart</b>/{widget.resource_name}</span>
        <span className="text-[12.5px] font-medium text-[var(--text)]">{widget.title}</span>
      </div>
      <div className="p-5 flex-1 flex items-end gap-2 min-h-[180px]">
        {config.chart_type === 'pie' ? (
          <div className="w-full flex justify-center items-center gap-5">
            <svg viewBox="0 0 32 32" className="w-28 h-28 -rotate-90">
              {data.map((d, i) => {
                const percentage = (d.value / total) * 100
                const previousTotal = data.slice(0, i).reduce((sum, curr) => sum + curr.value, 0)
                const strokeDashoffset = -((previousTotal / total) * 100)
                return (
                  <circle key={i} cx="16" cy="16" r="16" fill="transparent"
                          stroke={colors[i % colors.length]} strokeWidth="32"
                          strokeDasharray={`${percentage} 100`} strokeDashoffset={strokeDashoffset} />
                )
              })}
            </svg>
            <div className="flex flex-col gap-1.5">
              {data.map((d, i) => (
                <div key={i} className="flex items-center gap-2 text-[11.5px] arc-dim arc-mono">
                  <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: colors[i % colors.length] }} />
                  {d.name}: <span className="text-[var(--text)]">{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          data.map((d, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-1.5 group">
              <div className="w-full rounded-t-[var(--radius-sm)] transition-all hover:brightness-110"
                   style={{ height: `${(d.value / maxValue) * 140}px`, backgroundColor: colors[i % colors.length] }} />
              <span className="arc-id arc-dim2 truncate w-full text-center">{d.name}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

const StatWidget: WidgetComponent = ({ widget }) => {
  const [value, setValue] = useState<string | number>('…')
  const config = widget.config_json || {}
  const Icon = resolveIcon(config.icon || 'Activity')
  const navigate = useNavigate()
  const { notify } = useAras()

  useEffect(() => {
    api.get(`/${widget.resource_name}`).then((res: any) => {
      setValue(res.data.total || res.data.length || 0)
    }).catch((e) => notify(e.message, 'error'))
  }, [widget.resource_name, notify])

  return (
    <button
      className="arc-card p-5 text-left w-full h-full hover:border-[var(--accent)] transition-colors flex flex-col gap-3"
      onClick={() => navigate(`/${widget.resource_name.replace(/_/g, '-')}`)}
    >
      <div className="flex items-center justify-between">
        <div className="grid place-items-center w-9 h-9 rounded-[var(--radius)]"
             style={{ background: 'color-mix(in oklch, var(--accent) 12%, var(--surface))', color: 'var(--accent)' }}>
          <Icon size={16} />
        </div>
        <span className="arc-id arc-dim2">/{widget.resource_name}</span>
      </div>
      <div>
        <div className="arc-dim text-[10.5px] uppercase tracking-[0.12em] font-medium">{widget.title}</div>
        <div className="arc-mono arc-tnum text-[26px] font-medium text-[var(--text)] tracking-tight mt-1">{value}</div>
      </div>
    </button>
  )
}

const ListWidget: WidgetComponent = ({ widget }) => {
  const [items, setItems] = useState<any[]>([])
  const config = widget.config_json || {}
  const navigate = useNavigate()
  const { notify } = useAras()

  useEffect(() => {
    api.get(`/${widget.resource_name}?per_page=${config.limit || 5}`).then((res: any) => {
      setItems(Array.isArray(res.data.items) ? res.data.items : Array.isArray(res.data) ? res.data : [])
    }).catch((e) => notify(e.message, 'error'))
  }, [widget.resource_name, config.limit, notify])

  return (
    <div className="arc-card overflow-hidden h-full flex flex-col">
      <div className="px-4 py-2.5 border-b border-[var(--line)] flex items-center justify-between" style={{ background: 'var(--surface-2)' }}>
        <span className="arc-id"><b>recent</b>/{widget.resource_name}</span>
        <span className="text-[12.5px] font-medium text-[var(--text)]">{widget.title}</span>
      </div>
      <div className="flex-1 overflow-y-auto">
        {items.length === 0 ? (
          <EmptyState title="No recent activity" />
        ) : (
          items.map((item, idx) => (
            <button
              key={idx}
              className={`group w-full text-left flex items-center gap-3 px-4 py-2.5 hover:bg-[var(--surface-2)] transition-colors ${idx > 0 ? 'border-t border-[var(--line)]' : ''}`}
              onClick={() => navigate(`/${widget.resource_name.replace(/_/g, '-')}/${item.id}`)}
            >
              <span className="arc-stat s-released">●</span>
              <span className="text-[12.5px] text-[var(--text)] truncate flex-1">{item.description || item.name || item.id}</span>
              <span className="arc-id arc-dim2 arc-tnum">{item.created_at ? new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
            </button>
          ))
        )}
      </div>
    </div>
  )
}

WidgetRegistry.register('stat', StatWidget)
WidgetRegistry.register('chart', ChartWidget)
WidgetRegistry.register('list', ListWidget)

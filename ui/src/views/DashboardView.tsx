import React, { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { useAras } from '../aras-core/hooks/useAras'
import { resolveIcon } from '../lib/iconUtils'
import { LoadingState } from '../components/LoadingState'
import { EmptyState } from '../components/EmptyState'
import { useUIStore } from '../store/uiStore'

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
  register(type: string, Component: WidgetComponent) {
    registry.set(type, Component)
  },
  get(type: string) {
    return registry.get(type)
  }
}

export const DashboardView: React.FC = () => {
  const [widgets, setWidgets] = useState<Widget[]>([])
  const [loading, setLoading] = useState(true)
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)
  const { notify } = useAras()
  const setPageTitle = useUIStore((state) => state.setPageTitle)

  useEffect(() => {
    setPageTitle('Dashboard', 'Real-time overview of your operations and performance.')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  const loadWidgets = useCallback(async () => {
    try {
      const res = await api.get('/dashboard/widgets')
      setWidgets(res.data.layout_config?.widgets || [])
    } catch (err: any) {
      notify(err.message || 'Failed to load dashboard widgets', 'error')
    } finally {
      setLoading(false)
    }
  }, [notify])

  useEffect(() => {
    loadWidgets()
  }, [loadWidgets])

  const saveLayout = (newOrder: number[]) => {
    api.post('/dashboard/layout', { widget_order: newOrder }).catch((e) => {
      notify(e.message || 'Failed to save dashboard layout', 'error')
    })
  }

  const handleDrop = (dropIndex: number) => {
    if (dragIndex === null || dragIndex === dropIndex) {
      setDragIndex(null)
      setDragOverIndex(null)
      return
    }

    const nextWidgets = [...widgets]
    ;[nextWidgets[dragIndex], nextWidgets[dropIndex]] = [nextWidgets[dropIndex], nextWidgets[dragIndex]]
    setWidgets(nextWidgets)
    saveLayout(nextWidgets.map((widget) => widget.id))
    setDragIndex(null)
    setDragOverIndex(null)
  }

  if (loading) return <LoadingState label="Loading dashboard..." className="p-12" />
  if (widgets.length === 0) return <EmptyState title="No dashboard widgets" description="Dashboard widgets will appear here when configured." />

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      {widgets.map((widget, index) => {
        const Component = WidgetRegistry.get(widget.widget_type)
        if (!Component) return null

        return (
          <div
            key={widget.id}
            draggable={true}
            onDragStart={() => setDragIndex(index)}
            onDragOver={(event) => {
              event.preventDefault()
              setDragOverIndex(index)
            }}
            onDragLeave={() => {
              if (dragOverIndex === index) setDragOverIndex(null)
            }}
            onDrop={() => handleDrop(index)}
            onDragEnd={() => {
              setDragIndex(null)
              setDragOverIndex(null)
            }}
            className={`${widget.size || 'col-span-1'} cursor-grab transition-transform ${
              dragIndex === index ? 'opacity-50 scale-95' : ''
            } ${dragOverIndex === index && dragIndex !== index ? 'ring-2 ring-indigo-400' : ''}`}
          >
            <Component widget={widget} />
          </div>
        )
      })}
    </div>
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
    }).catch((e) => {
      notify(e.message, 'error')
      setLoading(false)
    })
  }, [widget.resource_name, config.group_by, notify])

  if (loading) return <div className="bg-[var(--app-panel)] p-6 rounded-[var(--app-radius-lg)] border border-[var(--app-border)] h-64 animate-pulse" />

  const maxValue = Math.max(...data.map(d => d.value), 1)
  const total = data.reduce((sum, curr) => sum + curr.value, 0) || 1
  const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

  return (
    <div className="bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-[var(--shadow-premium)] overflow-hidden h-full flex flex-col">
      <div className="p-6 border-b border-[var(--app-border)] flex items-center justify-between bg-[var(--app-panel-soft)]">
        <h2 className="font-extrabold text-[calc(18px*var(--app-font-scale))] text-[var(--app-text)]">{widget.title}</h2>
      </div>
      <div className="p-6 flex-1 flex items-end gap-2 min-h-[200px] bg-[var(--app-panel)]">
        {config.chart_type === 'pie' ? (
          <div className="w-full flex justify-center">
            <svg viewBox="0 0 32 32" className="w-32 h-32 -rotate-90">
              {data.map((d, i) => {
                const percentage = (d.value / total) * 100
                const previousTotal = data.slice(0, i).reduce((sum, curr) => sum + curr.value, 0)
                const strokeDashoffset = -((previousTotal / total) * 100)
                return (
                  <circle
                    key={i}
                    cx="16" cy="16" r="16"
                    fill="transparent"
                    stroke={colors[i % colors.length]}
                    strokeWidth="32"
                    strokeDasharray={`${percentage} 100`}
                    strokeDashoffset={String(strokeDashoffset)}
                  />
                )
              })}
            </svg>
            <div className="ml-6 flex flex-col justify-center gap-2">
              {data.map((d, i) => (
                <div key={i} className="flex items-center gap-2 text-[calc(12px*var(--app-font-scale))] font-bold text-[var(--app-muted)]">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: colors[i % colors.length] }} />
                  {d.name}: {d.value}
                </div>
              ))}
            </div>
          </div>
        ) : (
          data.map((d, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
              <div
                className="w-full rounded-t-[var(--app-radius)] transition-all hover:brightness-110 relative"
                style={{ height: `${(d.value / maxValue) * 150}px`, backgroundColor: colors[i % colors.length] }}
              >
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-[var(--app-text)] text-[var(--app-bg-main)] text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                  {d.value} units
                </div>
              </div>
              <span className="text-[10px] text-[var(--app-muted)] font-bold uppercase truncate w-full text-center">{d.name}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

const StatWidget: WidgetComponent = ({ widget }) => {
  const [value, setValue] = useState<string | number>('...')
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
    <div
      className="bg-[var(--app-panel)] p-7 rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-[var(--shadow-premium)] hover:border-[var(--app-border-strong)] transition-all group h-full cursor-pointer"
      title="Click to view all records"
      onClick={() => navigate(`/${widget.resource_name.replace(/_/g, '-')}`)}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-[var(--app-radius)] transition-colors ${
          config.color === 'indigo' ? 'bg-[var(--app-primary-action)]/10 text-[var(--app-primary-action)]' :
          config.color === 'emerald' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-[var(--app-panel-soft)] text-[var(--app-muted)]'
        }`}>
          <Icon size={20} />
        </div>
      </div>
      <p className="text-[var(--app-muted)] text-[calc(14px*var(--app-font-scale))] font-bold mb-1 uppercase tracking-wide">{widget.title}</p>
      <h3 className="text-[calc(28px*var(--app-font-scale))] font-extrabold text-[var(--app-text)] tracking-tight">{value}</h3>
    </div>
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
    <div className="bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-[var(--shadow-premium)] overflow-hidden h-full flex flex-col">
      <div className="p-6 border-b border-[var(--app-border)] flex items-center justify-between bg-[var(--app-panel-soft)]">
        <h2 className="font-extrabold text-[calc(18px*var(--app-font-scale))] text-[var(--app-text)]">{widget.title}</h2>
      </div>
      <div className="flex-1 overflow-y-auto bg-[var(--app-panel)]">
        {items.length === 0 ? (
          <EmptyState title="No recent activity" />
        ) : (
          <div className="divide-y divide-[var(--app-border)]">
            {items.map((item, idx) => (
              <div
                key={idx}
                className="p-4 hover:bg-[var(--app-panel-soft)] transition-colors flex items-center gap-4 cursor-pointer"
                onClick={() => navigate(`/${widget.resource_name.replace(/_/g, '-')}/${item.id}`)}
              >
                <div className="w-2 h-2 rounded-full bg-[var(--app-primary-action)]" />
                <div className="flex-1 text-[calc(14px*var(--app-font-scale))] text-[var(--app-text)] truncate font-bold">
                  {item.description || item.name || item.id}
                </div>
                <div className="text-[10px] text-[var(--app-muted)] font-bold uppercase">
                  {item.created_at ? new Date(item.created_at).toLocaleTimeString() : ''}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

WidgetRegistry.register('stat', StatWidget)
WidgetRegistry.register('chart', ChartWidget)
WidgetRegistry.register('list', ListWidget)

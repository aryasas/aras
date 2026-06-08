// claude-opus-4-7
// ARC dashboard: bento grid of widgets. Drag-reorder using @dnd-kit through DnDGrid.
// Stat widgets are mono-readout; charts keep their data viz but live inside arc-cards.
import React, { useCallback, useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import api, {
  getTradeDashboard,
  type TradeDashboardData,
  type TradeDashboardLowStockItem,
  type TradeDashboardRecentDocument,
} from '../lib/api'
import { useAras } from '../aras-core/hooks/useAras'
import { resolveIcon } from '../lib/iconUtils'
import { LoadingState } from '../components/LoadingState'
import { EmptyState } from '../components/EmptyState'
import { useUIStore } from '../store/uiStore'
import { useAuthStore } from '../store/authStore'
import { useVocabulary } from '../context/VocabularyContext'
import { formatCurrency } from '../lib/formatters'
import { FormattingService } from '../aras-core/services/FormattingService'
import {
  DndContext, KeyboardSensor, PointerSensor, closestCenter, useSensor, useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import { SortableContext, rectSortingStrategy, useSortable, sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { AlertTriangle, GripVertical } from 'lucide-react'

interface Widget {
  id: number
  name: string
  title: string
  widget_type: 'stat' | 'chart' | 'list' | string
  resource_name: string
  resource_path?: string
  config_json: any
  size: string
}

type WidgetComponent = React.FC<{ widget: Widget }>
type TradeMetricKey = 'today_sales' | 'month_profit' | 'receivables_total' | 'overdue_count' | 'low_stock_count'
type TradeListSource = 'low_stock_items' | 'recent_documents'
type TradeLabels = NonNullable<TradeDashboardData['labels']>

// Convert seeded resource_name ("core_users") to REST path ("core/users").
// Apps register routes as /{app}/{model-seg-with-dashes}; resource_name uses
// the raw __tablename__ ("{app}_{model_seg}") so we split on the first underscore.
const resourcePath = (w: Widget): string => {
  if (w.resource_path) return w.resource_path.replace(/^\/+/, '')
  const name = w.resource_name || ''
  if (!name) return ''
  if (name.includes('/')) return name.replace(/^\/+/, '')
  const i = name.indexOf('_')
  if (i < 0) return name
  return `${name.slice(0, i)}/${name.slice(i + 1).replace(/_/g, '-')}`
}
const registry = new Map<string, WidgetComponent>()
export const WidgetRegistry = {
  register(type: string, Component: WidgetComponent) { registry.set(type, Component) },
  get(type: string) { return registry.get(type) },
}

// claude-opus-4-8
function useTradeDashboardData() {
  const activeOrgId = useAuthStore((state) => state.activeOrgId)
  const vocabulary = useVocabulary()
  const [data, setData] = useState<TradeDashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    getTradeDashboard(activeOrgId ?? undefined)
      .then((payload) => {
        if (cancelled) return
        setData(payload)
      })
      .catch((err: any) => {
        if (cancelled) return
        setError(err.message || 'Failed to load trade dashboard.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [activeOrgId])

  return {
    data,
    loading,
    error,
    labels: (data?.labels || vocabulary) as TradeLabels,
  }
}

// claude-opus-4-8
function formatTradeCount(value: number, locale: string) {
  return new Intl.NumberFormat(locale).format(value)
}

// claude-opus-4-8
function formatTradePercent(value: number, locale: string) {
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(Math.abs(value)) + '%'
}

// claude-opus-4-8
function formatTradeDate(value: string | null | undefined, locale: string) {
  if (!value) return 'No date'
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(value))
}

// claude-opus-4-8
function pluralizeLabel(label: string) {
  if (/[^aeiou]y$/i.test(label)) return `${label.slice(0, -1)}ies`
  return label.endsWith('s') ? label : `${label}s`
}

// claude-opus-4-8
function resolveTradeWidgetTitle(widget: Widget, labels: TradeLabels, metric?: TradeMetricKey) {
  const config = widget.config_json || {}
  const labelKey = config.title_key as keyof TradeLabels | undefined
  const labelValue = labelKey && labels[labelKey] ? labels[labelKey] : null

  if (metric === 'today_sales' && labelValue) return `Today's ${labelValue}`
  if (metric === 'receivables_total' && labelValue) return `Owed by ${pluralizeLabel(labelValue)}`
  if (metric === 'month_profit') return 'This Month Profit'
  return widget.title
}

// claude-opus-4-8
function tradeKpiEmptyState(metric: TradeMetricKey, data: TradeDashboardData | null, labels: TradeLabels) {
  if (!data) return null
  if (metric === 'today_sales' && !data.today_sales && data.recent_documents.length === 0) {
    return `No ${labels.trx_in.toLowerCase()} yet today`
  }
  if (metric === 'month_profit' && !data.month_profit && data.recent_documents.length === 0) {
    return 'No profit data yet this month'
  }
  if (metric === 'receivables_total' && !data.receivables_total && !data.overdue_count) {
    return `No ${pluralizeLabel(labels.party).toLowerCase()} owe you right now`
  }
  if (metric === 'overdue_count' && !data.overdue_count) {
    return 'No overdue invoices'
  }
  if (metric === 'low_stock_count' && !data.low_stock_count) {
    return 'No low stock items'
  }
  return null
}

// claude-opus-4-8
function TradeWidgetSkeleton() {
  return <div className="arc-card p-6 h-full min-h-[180px] animate-pulse" />
}

// claude-opus-4-8
function TradeWidgetError({ title, message }: { title: string; message: string }) {
  return (
    <div className="arc-card p-5 h-full flex flex-col gap-3">
      <div className="arc-dim text-[10.5px] uppercase tracking-[0.12em] font-medium">{title}</div>
      <div className="flex items-start gap-2 text-sm text-[var(--text)]">
        <AlertTriangle size={16} className="mt-0.5 shrink-0" style={{ color: 'var(--danger)' }} />
        <span>{message}</span>
      </div>
    </div>
  )
}

// claude-opus-4-8
function TradeWidgetEmpty({ title, message }: { title: string; message: string }) {
  return (
    <div className="arc-card p-5 h-full flex flex-col gap-3 justify-center">
      <div className="arc-dim text-[10.5px] uppercase tracking-[0.12em] font-medium">{title}</div>
      <div className="text-sm arc-dim">{message}</div>
    </div>
  )
}

// claude-opus-4-8
function tradeDocumentLabel(type?: string | null) {
  if (!type) return 'Document'
  const value = String(type)
  return value.charAt(0).toUpperCase() + value.slice(1)
}

// claude-opus-4-8
function LowStockListRow({ item, locale }: { item: TradeDashboardLowStockItem; locale: string }) {
  const qty = Number(item.balance || 0)

  return (
    <div className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[12.5px] font-medium text-[var(--text)] truncate">{item.name || item.code || 'Unnamed item'}</span>
          {item.code ? <span className="arc-id arc-dim2">{item.code}</span> : null}
        </div>
        <div className="text-[12px] arc-dim mt-1">
          Balance {formatTradeCount(qty, locale)}{item.uom ? ` ${item.uom}` : ''}
        </div>
      </div>
      <div className="arc-id arc-tnum text-[var(--accent)]">{formatTradeCount(qty, locale)}</div>
    </div>
  )
}

// claude-opus-4-8
function RecentDocumentListRow({ item, locale }: { item: TradeDashboardRecentDocument; locale: string }) {
  return (
    <div className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="arc-stat s-released">{tradeDocumentLabel(item.type)}</span>
          <span className="text-[12.5px] font-medium text-[var(--text)]">{item.number || 'No number'}</span>
          {item.status ? <span className="arc-id arc-dim2">{item.status}</span> : null}
        </div>
        <div className="text-[12px] arc-dim mt-1">
          {(item.party_name || 'No party')} · {formatTradeDate(item.doc_date, locale)}
        </div>
      </div>
      <div className="arc-id arc-tnum">{formatCurrency(item.amount || 0)}</div>
    </div>
  )
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
    api.get(`/${resourcePath(widget)}`).then((res: any) => {
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
    api.get(`/${resourcePath(widget)}`).then((res: any) => {
      setValue(res.data.total || res.data.length || 0)
    }).catch((e) => notify(e.message, 'error'))
  }, [widget.resource_name, notify])

  return (
    <button
      className="arc-card p-5 text-left w-full h-full hover:border-[var(--accent)] transition-colors flex flex-col gap-3"
      onClick={() => navigate(`/${resourcePath(widget)}`)}
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
    api.get(`/${resourcePath(widget)}?per_page=${config.limit || 5}`).then((res: any) => {
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
              onClick={() => navigate(`/${resourcePath(widget)}/${item.id}`)}
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

// claude-opus-4-8
const TradeKpiWidget: WidgetComponent = ({ widget }) => {
  const navigate = useNavigate()
  const { data, loading, error, labels } = useTradeDashboardData()
  const config = widget.config_json || {}
  const metric = config.metric as TradeMetricKey
  const locale = FormattingService.getConfig().language || 'en-US'
  const title = resolveTradeWidgetTitle(widget, labels, metric)
  const empty = tradeKpiEmptyState(metric, data, labels)

  if (loading) return <TradeWidgetSkeleton />
  if (error) return <TradeWidgetError title={title} message={error} />
  if (!data) return <TradeWidgetEmpty title={title} message="No dashboard data available." />

  const metricValue = Number(((data as unknown as Record<string, unknown>)[metric]) || 0)
  if (empty) return <TradeWidgetEmpty title={title} message={empty} />

  const content = (
    <>
      <div>
        <div className="arc-dim text-[10.5px] uppercase tracking-[0.12em] font-medium">{title}</div>
        <div className="arc-mono arc-tnum text-[26px] font-medium text-[var(--text)] tracking-tight mt-1">
          {metric === 'today_sales' || metric === 'month_profit' || metric === 'receivables_total'
            ? formatCurrency(metricValue)
            : formatTradeCount(metricValue, locale)}
        </div>
      </div>

      {metric === 'month_profit' ? (
        <div className="flex items-center gap-2 text-[12px] font-medium">
          <span style={{ color: data.month_profit_change_pct >= 0 ? '#10b981' : 'var(--danger)' }}>
            {data.month_profit_change_pct >= 0 ? '▲' : '▼'}
          </span>
          <span className="arc-dim">
            {formatTradePercent(data.month_profit_change_pct || 0, locale)} vs previous month
          </span>
        </div>
      ) : null}

      {metric === 'receivables_total' ? (
        <div className="text-[12px] arc-dim">
          {formatTradeCount(data.overdue_count || 0, locale)} overdue invoice{(data.overdue_count || 0) === 1 ? '' : 's'}
        </div>
      ) : null}
    </>
  )

  const className = 'arc-card p-5 text-left w-full h-full hover:border-[var(--accent)] transition-colors flex flex-col justify-between gap-4'
  if (config.link) {
    return (
      <button className={className} onClick={() => navigate(config.link)}>
        {content}
      </button>
    )
  }

  return <div className={className}>{content}</div>
}

// claude-opus-4-8
const TradeListWidget: WidgetComponent = ({ widget }) => {
  const { data, loading, error } = useTradeDashboardData()
  const config = widget.config_json || {}
  const source = config.source as TradeListSource
  const locale = FormattingService.getConfig().language || 'en-US'
  const items = source === 'low_stock_items' ? (data?.low_stock_items || []) : (data?.recent_documents || [])

  if (loading) return <TradeWidgetSkeleton />
  if (error) return <TradeWidgetError title={widget.title} message={error} />

  return (
    <div className="arc-card overflow-hidden h-full flex flex-col">
      <div className="px-4 py-2.5 border-b border-[var(--line)] flex items-center justify-between" style={{ background: 'var(--surface-2)' }}>
        <span className="arc-id"><b>recent</b>/{widget.resource_name}</span>
        <span className="text-[12.5px] font-medium text-[var(--text)]">{widget.title}</span>
      </div>
      <div className="flex-1 overflow-y-auto">
        {items.length === 0 ? (
          <div className="px-4 py-4 text-sm arc-dim">
            {source === 'low_stock_items' ? 'All stock healthy' : 'No recent activity yet'}
          </div>
        ) : source === 'low_stock_items' ? (
          (items as TradeDashboardLowStockItem[]).map((item, idx) => (
            <div key={(item.code || item.name || 'item') + '-' + String(idx)} className={idx > 0 ? 'border-t border-[var(--line)]' : ''}>
              <LowStockListRow item={item} locale={locale} />
            </div>
          ))
        ) : (
          (items as TradeDashboardRecentDocument[]).map((item, idx) => (
            <div key={(item.type || 'document') + '-' + (item.number || String(idx))} className={idx > 0 ? 'border-t border-[var(--line)]' : ''}>
              <RecentDocumentListRow item={item} locale={locale} />
            </div>
          ))
        )}
      </div>
    </div>
  )
}

WidgetRegistry.register('stat', StatWidget)
WidgetRegistry.register('chart', ChartWidget)
WidgetRegistry.register('list', ListWidget)
WidgetRegistry.register('trade_kpi', TradeKpiWidget)
WidgetRegistry.register('trade_list', TradeListWidget)

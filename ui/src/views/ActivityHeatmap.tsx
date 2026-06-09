import { useMemo, useState } from 'react'
import { Activity, RefreshCw } from 'lucide-react'
import api from '../lib/api'
import { EmptyState } from '../components/EmptyState'
import { LoadingState } from '../components/LoadingState'
import { devApi } from './devtools/devApi'
import { useAsyncData } from '../hooks/useAsyncData'

type ActionName = 'create' | 'update' | 'delete' | 'read'

interface DayBucket {
  date: string
  create: number
  update: number
  delete: number
  read: number
  total: number
}

type ResourceTotals = Record<string, Record<ActionName, number>>

interface HeatmapResponse {
  days: number
  data: ResourceTotals
  calendar?: DayBucket[]
  error?: string
}

const ACTIONS: ActionName[] = ['create', 'update', 'delete', 'read']
const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const RANGE_OPTIONS = [30, 90, 180, 365]

function safeNumber(value: unknown) {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

function toneFor(value: number, max: number) {
  if (!value || !max) return 'var(--surface-2)'
  const ratio = value / max
  if (ratio > 0.75) return 'color-mix(in oklch, var(--accent) 88%, #7a3b1b)'
  if (ratio > 0.5) return 'color-mix(in oklch, var(--accent) 70%, var(--surface))'
  if (ratio > 0.25) return 'color-mix(in oklch, var(--accent) 42%, var(--surface))'
  return 'color-mix(in oklch, var(--accent) 20%, var(--surface))'
}

function formatDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function buildFallbackCalendar(days: number, totals: ResourceTotals): DayBucket[] {
  const total = Object.values(totals).reduce((sum, counts) => (
    sum + ACTIONS.reduce((inner, action) => inner + safeNumber(counts[action]), 0)
  ), 0)
  const today = new Date()
  return Array.from({ length: days }, (_, index) => {
    const date = new Date(today)
    date.setDate(today.getDate() - (days - index - 1))
    const iso = date.toISOString().slice(0, 10)
    return { date: iso, create: 0, update: 0, delete: 0, read: index === days - 1 ? total : 0, total: index === days - 1 ? total : 0 }
  })
}

export default function ActivityHeatmap() {
  const [days, setDays] = useState(90)

  const { data: payload, loading, error, reload } = useAsyncData<HeatmapResponse>(
    () => api.get(devApi.activityHeatmap, { params: { days } }).then((r) => r.data),
    [days],
  )

  const calendar = useMemo(() => {
    if (!payload) return []
    const values = Array.isArray(payload.calendar) && payload.calendar.length
      ? payload.calendar
      : buildFallbackCalendar(payload.days || days, payload.data || {})
    return values.map((item) => ({
      ...item,
      create: safeNumber(item.create),
      update: safeNumber(item.update),
      delete: safeNumber(item.delete),
      read: safeNumber(item.read),
      total: safeNumber(item.total),
    }))
  }, [days, payload])

  const resources = useMemo(() => {
    const totals = payload?.data || {}
    return Object.entries(totals)
      .map(([name, counts]) => ({
        name,
        create: safeNumber(counts.create),
        update: safeNumber(counts.update),
        delete: safeNumber(counts.delete),
        read: safeNumber(counts.read),
        total: ACTIONS.reduce((sum, action) => sum + safeNumber(counts[action]), 0),
      }))
      .sort((a, b) => b.total - a.total)
  }, [payload])

  const max = Math.max(1, ...calendar.map((day) => day.total))
  const totalEvents = calendar.reduce((sum, day) => sum + day.total, 0)
  const activeDays = calendar.filter((day) => day.total > 0).length
  const leadingSlots = calendar.length ? new Date(`${calendar[0].date}T00:00:00`).getDay() : 0
  const cells = [...Array.from({ length: leadingSlots }, () => null), ...calendar]

  return (
    <div className="arc flex flex-col gap-5">
      <div className="arc-card flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between" style={{ background: 'var(--bg-2)' }}>
        <div className="arc-dim text-[12px]">{totalEvents.toLocaleString()} events · {activeDays} active days · {resources.length} resources</div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] p-1">
            {RANGE_OPTIONS.map((option) => (
              <button
                key={option}
                onClick={() => setDays(option)}
                className={`h-8 px-3 rounded-[var(--radius-sm)] text-[12.5px] font-medium ${days === option ? 'bg-[var(--surface-2)] text-[var(--text)]' : 'text-[var(--text-2)] hover:text-[var(--text)]'}`}
              >
                {option}d
              </button>
            ))}
          </div>
          <button onClick={reload} className="arc-btn" disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      {loading && <LoadingState label="Loading activity heatmap..." className="arc-card border-dashed" />}
      {!loading && error && <EmptyState icon={Activity} title="Failed to load activity" description={error} />}
      {!loading && !error && totalEvents === 0 && <EmptyState icon={Activity} title="No activity in this range" description="Audit events will appear after tracked records are created, updated, read, or deleted." />}

      {!loading && !error && totalEvents > 0 && (
        <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_360px] gap-5">
          <section className="arc-card overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
              <span className="arc-id"><b>calendar</b></span>
              <span className="arc-id arc-dim2">max {max.toLocaleString()}/day</span>
            </div>
            <div className="p-4 overflow-x-auto">
              <div className="grid gap-1.5 min-w-[720px]" style={{ gridTemplateColumns: `42px repeat(${Math.ceil(cells.length / 7)}, minmax(13px, 1fr))` }}>
                {DAY_LABELS.map((label) => (
                  <div key={label} className="arc-id arc-dim2 h-4 text-[10px]" style={{ gridColumn: 1, gridRow: DAY_LABELS.indexOf(label) + 1 }}>
                    {label}
                  </div>
                ))}
                {cells.map((day, index) => {
                  const col = Math.floor(index / 7) + 2
                  const row = (index % 7) + 1
                  if (!day) return <div key={`empty-${index}`} style={{ gridColumn: col, gridRow: row }} />
                  return (
                    <div
                      key={day.date}
                      title={`${formatDate(day.date)}: ${day.total} events`}
                      className="h-4 rounded-[4px] border border-[var(--line)]"
                      style={{ gridColumn: col, gridRow: row, background: toneFor(day.total, max) }}
                    />
                  )
                })}
              </div>
              <div className="mt-4 flex items-center justify-end gap-2 arc-id arc-dim2">
                <span>less</span>
                {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
                  <span
                    key={ratio}
                    className="inline-block h-3.5 w-3.5 rounded-[4px] border border-[var(--line)]"
                    style={{ background: toneFor(max * ratio, max) }}
                  />
                ))}
                <span>more</span>
              </div>
            </div>
          </section>

          <section className="arc-card overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
              <span className="arc-id"><b>resources</b></span>
              <span className="arc-id arc-dim2">top {Math.min(resources.length, 12)}</span>
            </div>
            <div className="divide-y divide-[var(--line)]">
              {resources.slice(0, 12).map((resource) => (
                <div key={resource.name} className="px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <code className="text-[12.5px] text-[var(--text)] truncate">{resource.name}</code>
                    <span className="arc-id"><b>{resource.total.toLocaleString()}</b></span>
                  </div>
                  <div className="mt-2 grid grid-cols-4 gap-1.5">
                    {ACTIONS.map((action) => (
                      <div key={action} className="rounded-[var(--radius-sm)] bg-[var(--surface-2)] px-2 py-1.5">
                        <div className="arc-id arc-dim2 text-[10px]">{action}</div>
                        <div className="arc-mono text-[12px] text-[var(--text)]">{resource[action].toLocaleString()}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

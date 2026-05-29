// claude-sonnet-4-6
import React, { useEffect, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { SkeletonRow } from '../../components/SkeletonRow'
import api from '../../lib/api'

type ArasRow = object
type TableRecord = Record<string, unknown>
type ColumnRender<T extends ArasRow> = {
  bivarianceHack(value: unknown, row: T, index: number): React.ReactNode
}['bivarianceHack']

export interface ArasTableColumn<T extends ArasRow = ArasRow> {
  key: string
  label: string
  align?: 'left' | 'right' | 'center'
  width?: number | string
  minWidth?: number | string
  render?: ColumnRender<T>
  field?: string
  sortable?: boolean
}

interface ArasTableProps<T extends ArasRow = ArasRow> {
  columns: ArasTableColumn<T>[]
  rows: T[]
  rowKey?: (row: T, index: number) => string | number
  onRowClick?: (row: T, index: number) => void
  orderBy?: string
  orderDesc?: boolean
  onSort?: (field: string) => void
  loading?: boolean
  loadingRows?: number
  emptyMessage?: React.ReactNode
  className?: string
  minWidth?: number | string
  rowClassName?: (row: T, index: number) => string
  stickyHeader?: boolean
  preferenceKey?: string
}

// claude-sonnet-4-6
const thStyle: React.CSSProperties = {
  background: 'var(--bg)',
  fontFamily: 'var(--font-mono)',
  fontSize: 'var(--fs-xs)',
  letterSpacing: '.14em',
  color: 'var(--text-3)',
  textTransform: 'uppercase',
  fontWeight: 500,
  padding: '10px 12px',
  textAlign: 'left',
  whiteSpace: 'nowrap',
  borderBottom: '1px solid var(--line)',
}

// claude-sonnet-4-6
export function ArasTable<T extends ArasRow = ArasRow>({
  columns,
  rows,
  rowKey,
  onRowClick,
  orderBy,
  orderDesc,
  onSort,
  loading = false,
  loadingRows = 5,
  emptyMessage = 'No records found.',
  className,
  minWidth,
  rowClassName,
  stickyHeader = false,
  preferenceKey,
}: ArasTableProps<T>) {
  const [stacked, setStacked] = useState(false)
  const [widths, setWidths] = useState<Record<string, number>>({})

  useEffect(() => {
    const query = window.matchMedia('(max-width: 767px)')
    const update = () => setStacked(query.matches)
    update()
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    if (!preferenceKey) return
    const controller = new AbortController()
    api.get('/preference', { params: { key: preferenceKey }, signal: controller.signal })
      .then((res) => {
        const saved = typeof res.data?.value === 'string' ? JSON.parse(res.data.value) : res.data?.value
        if (saved && typeof saved === 'object' && !Array.isArray(saved)) setWidths(saved)
      })
      .catch(() => {})
    return () => controller.abort()
  }, [preferenceKey])

  const persistWidths = (next: Record<string, number>) => {
    if (!preferenceKey) return
    api.put('/preference', { key: preferenceKey, value: JSON.stringify(next) }).catch(() => {})
  }

  const startResize = (event: React.PointerEvent, key: string) => {
    event.preventDefault()
    event.stopPropagation()
    const th = event.currentTarget.parentElement as HTMLTableCellElement | null
    const startX = event.clientX
    const startWidth = th?.offsetWidth || widths[key] || 160
    const onMove = (moveEvent: PointerEvent) => {
      const nextWidth = Math.max(80, startWidth + moveEvent.clientX - startX)
      setWidths((prev) => ({ ...prev, [key]: nextWidth }))
    }
    const onUp = (upEvent: PointerEvent) => {
      const nextWidth = Math.max(80, startWidth + upEvent.clientX - startX)
      const next = { ...widths, [key]: nextWidth }
      setWidths(next)
      persistWidths(next)
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
  }

  const onCellKeyDown = (event: React.KeyboardEvent<HTMLTableCellElement | HTMLTableHeaderCellElement>) => {
    const target = event.currentTarget
    if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) return
    event.preventDefault()
    const row = target.parentElement
    const rowIndex = row ? Array.from(row.parentElement?.children ?? []).indexOf(row) : -1
    const cellIndex = Array.from(row?.children ?? []).indexOf(target)
    const rowOffset = event.key === 'ArrowUp' ? -1 : event.key === 'ArrowDown' ? 1 : 0
    const cellOffset = event.key === 'ArrowLeft' ? -1 : event.key === 'ArrowRight' ? 1 : 0
    const nextRow = row?.parentElement?.children[rowIndex + rowOffset] as HTMLElement | undefined
    const nextCell = (rowOffset ? nextRow?.children[cellIndex] : row?.children[cellIndex + cellOffset]) as HTMLElement | undefined
    nextCell?.focus()
  }

  if (stacked) {
    return (
      <div className={`space-y-2 ${className ?? ''}`}>
        {loading ? (
          Array.from({ length: loadingRows }).map((_, i) => <div key={i} className="h-24 animate-pulse rounded border border-[var(--line)] bg-[var(--surface-2)]" />)
        ) : rows.length === 0 ? (
          <div className="py-12 text-center text-[var(--text-3)]" style={{ fontSize: 'var(--fs-base)' }}>{emptyMessage}</div>
        ) : rows.map((row, i) => (
          <button
            key={rowKey ? rowKey(row, i) : i}
            type="button"
            onClick={onRowClick ? () => onRowClick(row, i) : undefined}
            className={`w-full rounded border border-[var(--line)] bg-[var(--surface)] p-3 text-left ${onRowClick ? 'cursor-pointer active:bg-[var(--surface-2)]' : ''} ${rowClassName?.(row, i) ?? ''}`}
          >
            {columns.map((col) => {
              const val = col.field ? (row as TableRecord)[col.field] : undefined
              return (
                <div key={col.key} className="grid grid-cols-[120px_1fr] gap-3 py-1" style={{ fontSize: 'var(--fs-base)' }}>
                  <span className="font-semibold text-[var(--text-3)]">{col.label}</span>
                  <span className={col.align === 'right' ? 'text-right' : ''}>{col.render ? col.render(val, row, i) : val == null ? '-' : String(val)}</span>
                </div>
              )
            })}
          </button>
        ))}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table
        role="table"
        className={`w-full text-left border-collapse ${className ?? ''}`}
        style={minWidth ? { minWidth } : undefined}
      >
        <thead>
          <tr>
            {columns.map((col) => {
              const isSorted = orderBy === (col.field ?? col.key)
              const canSort = col.sortable !== false && !!onSort && !!(col.field ?? col.key)
              return (
                <th
                  key={col.key}
                  scope="col"
                  tabIndex={0}
                  aria-sort={isSorted ? (orderDesc ? 'descending' : 'ascending') : 'none'}
                  style={{
                    ...thStyle,
                    width: widths[col.key] ?? col.width,
                    minWidth: col.minWidth,
                    textAlign: col.align ?? 'left',
                    top: stickyHeader ? 0 : undefined,
                    zIndex: col === columns[0] ? 2 : stickyHeader ? 10 : undefined,
                    cursor: canSort ? 'pointer' : undefined,
                    boxShadow: col === columns[0] ? '8px 0 12px -12px var(--text-3)' : undefined,
                    left: col === columns[0] ? 0 : undefined,
                    position: col === columns[0] ? 'sticky' : stickyHeader ? 'sticky' : undefined,
                  }}
                  onClick={canSort ? () => onSort!(col.field ?? col.key) : undefined}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && canSort) onSort!(col.field ?? col.key)
                    else onCellKeyDown(event)
                  }}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {isSorted && (
                      orderDesc
                        ? <ChevronDown size={12} style={{ color: 'var(--accent)' }} />
                        : <ChevronUp size={12} style={{ color: 'var(--accent)' }} />
                    )}
                  </span>
                  <span
                    role="separator"
                    aria-orientation="vertical"
                    aria-label={`Resize ${col.label}`}
                    onPointerDown={(event) => startResize(event, col.key)}
                    className="absolute right-0 top-0 h-full w-2 cursor-col-resize touch-none"
                    style={{ transform: 'translateX(50%)' }}
                  />
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            Array.from({ length: loadingRows }).map((_, i) => (
              <SkeletonRow key={i} columns={columns.length} />
            ))
          ) : rows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                style={{ padding: '48px 12px', textAlign: 'center', color: 'var(--text-3)', fontSize: 13 }}
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row, i) => {
              const key = rowKey ? rowKey(row, i) : i
              const extra = rowClassName?.(row, i) ?? ''
              return (
                <tr
                  key={key}
                  className={`group border-b border-[var(--line)] transition-colors ${onRowClick ? 'cursor-pointer hover:bg-[var(--surface-2)]' : 'hover:bg-[var(--surface-2)]/50'} ${extra}`}
                  onClick={onRowClick ? () => onRowClick(row, i) : undefined}
                >
                  {columns.map((col) => {
                    const val = col.field ? (row as TableRecord)[col.field] : undefined
                    return (
                      <td
                        key={col.key}
                        tabIndex={0}
                        onKeyDown={onCellKeyDown}
                        style={{
                          padding: '10px 12px',
                          textAlign: col.align ?? 'left',
                          width: widths[col.key] ?? col.width,
                          minWidth: col.minWidth,
                          fontSize: 'var(--fs-base)',
                          color: 'var(--text)',
                          position: col === columns[0] ? 'sticky' : undefined,
                          left: col === columns[0] ? 0 : undefined,
                          background: col === columns[0] ? 'var(--surface)' : undefined,
                          boxShadow: col === columns[0] ? '8px 0 12px -12px var(--text-3)' : undefined,
                        }}
                      >
                        {col.render ? col.render(val, row, i) : val == null ? '—' : String(val)}
                      </td>
                    )
                  })}
                </tr>
              )
            })
          )}
        </tbody>
      </table>
    </div>
  )
}

export default ArasTable

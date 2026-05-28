// claude-sonnet-4-6
import React from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

export interface ArasTableColumn<T = any> {
  key: string
  label: string
  align?: 'left' | 'right' | 'center'
  width?: number | string
  minWidth?: number | string
  render?: (value: any, row: T, index: number) => React.ReactNode
  field?: string
  sortable?: boolean
}

interface ArasTableProps<T = any> {
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
}

// claude-sonnet-4-6
const thStyle: React.CSSProperties = {
  background: 'var(--bg)',
  fontFamily: 'var(--font-mono)',
  fontSize: 10.5,
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
export function ArasTable<T = any>({
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
}: ArasTableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table
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
                  style={{
                    ...thStyle,
                    width: col.width,
                    minWidth: col.minWidth,
                    textAlign: col.align ?? 'left',
                    position: stickyHeader ? 'sticky' : undefined,
                    top: stickyHeader ? 0 : undefined,
                    zIndex: stickyHeader ? 10 : undefined,
                    cursor: canSort ? 'pointer' : undefined,
                  }}
                  onClick={canSort ? () => onSort!(col.field ?? col.key) : undefined}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {isSorted && (
                      orderDesc
                        ? <ChevronDown size={12} style={{ color: 'var(--accent)' }} />
                        : <ChevronUp size={12} style={{ color: 'var(--accent)' }} />
                    )}
                  </span>
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            Array.from({ length: loadingRows }).map((_, i) => (
              <tr key={i} className="animate-pulse border-b border-[var(--line)]">
                {columns.map((col) => (
                  <td key={col.key} style={{ padding: '10px 12px' }}>
                    <div className="h-4 rounded bg-[var(--surface-2)]" style={{ width: '60%' }} />
                  </td>
                ))}
              </tr>
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
                    const val = col.field ? (row as any)[col.field] : undefined
                    return (
                      <td
                        key={col.key}
                        style={{
                          padding: '10px 12px',
                          textAlign: col.align ?? 'left',
                          minWidth: col.minWidth,
                          fontSize: 13,
                          color: 'var(--text)',
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

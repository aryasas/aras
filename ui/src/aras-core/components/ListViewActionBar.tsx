// claude-sonnet-4-6
// Thin re-export — ListViewActionBar is now ArasActionBar variant="full".
// Kept for backward compatibility; existing callers need no changes.
import React from 'react'
import { ArasActionBar } from './ArasActionBar'
import type { ViewMode, FilterChip } from './ArasActionBar'

export type { ViewMode, FilterChip }

interface ListViewActionBarProps {
  title: string
  search: string
  onSearchChange: (value: string) => void
  isFilterOpen: boolean
  onFilterToggle: () => void
  filterCount: number
  selectedCount: number
  onBulkEdit: () => void
  onBulkDelete: () => void
  onExport: () => void
  isExporting: boolean
  onImport: (e: React.ChangeEvent<HTMLInputElement>) => void
  onColumnPickerToggle: () => void
  isColumnPickerOpen: boolean
  onAdd: () => void
  onArchive?: () => void
  onSettings?: () => void
  fields: any[]
  visibleColumns: string[]
  onVisibleColumnsChange: (columns: string[]) => void
  viewMode?: ViewMode
  onViewModeChange?: (mode: ViewMode) => void
  hasTreeSupport?: boolean
  onSaveFilter: () => void
  onApplySavedFilter: (filterId: string) => void
  onDeleteSavedFilter: (filterId: string) => void
  savedFilters: { id: string; name: string; is_default: boolean }[]
  groupField?: string | null
  onGroupFieldChange?: (field: string | null) => void
  groupableFields?: { name: string; label: string }[]
  filterChips?: FilterChip[]
  page?: number
  perPage?: number
  total?: number
  totalPages?: number
  onPageChange?: (page: number) => void
  onPerPageChange?: (perPage: number) => void
}

// claude-sonnet-4-6
export const ListViewActionBar: React.FC<ListViewActionBarProps> = (props) => (
  <ArasActionBar variant="full" {...props} />
)

export default ListViewActionBar

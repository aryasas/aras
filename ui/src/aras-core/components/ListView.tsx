import { useState, useEffect, useCallback, useMemo } from 'react'
import type { CSSProperties } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../../lib/api'
import { cleanResourcePath } from '../../lib/resourceUtils'
import {
  Plus, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight,
  CheckSquare, Square, X, Pencil,
  ChevronDown, ChevronUp, Trash2, Search
} from 'lucide-react'
import { resolveFieldComponent, resolveFilterComponent } from '../SchemaRegistry'
import { useAras } from '../hooks/useAras'
import { useUIStore } from '../../store/uiStore'
import Combobox from './Combobox'
import FormSettings from './FormSettings'

import { ArasActionBar, type ViewMode } from './ArasActionBar'
import { validateField } from '../lib/validate'
import { bulkDelete, exportCsv, importCsv } from '../lib/listActions'
import { useVocabulary } from '../../context/VocabularyContext'
import { FormattingService } from '../services/FormattingService'
import { DesignContainer } from './design/DesignContainer'
import { DesignElement } from './design/DesignElement'
import { SkeletonRow } from '../../components/SkeletonRow'
import { InsightStrip } from './InsightStrip'
import {
  type FieldValue, getErrorMessage, isCanceledError, renderCellValue, StatusGlyph,
} from './listView.helpers'

interface Field {
  name: string
  label: string
  type: string
  required: boolean
  read_only: boolean
  hidden: boolean
  list_hidden: boolean
  searchable: boolean
  target_resource?: string
  options?: { label: string; value: string | number }[]
  section?: string
  min_length?: number
  max_length?: number
  pattern?: string
  info?: { pattern_hint?: string }
}

interface ListTab {
  label: string
  filter: { field: string; value: FieldValue }
}

interface Metadata {
  resource: string
  api_path?: string | null
  title: string
  fields: Field[]
  is_auditable?: boolean
  list_tabs?: ListTab[]
  insights?: Array<{ key: string; label: string; format: 'number' | 'currency' | 'percent'; icon?: string | null; prefix?: string | null; suffix?: string | null }>
}

interface FilterRule {
  field: string
  op: string
  value: FieldValue
}

interface SavedFilter {
  id: string;
  resource: string;
  name: string;
  filters_json: string;
  is_default: boolean;
}

type ListRow = Record<string, FieldValue> & { id: string | number }
type ListParams = {
  page: number
  per_page: number
  sort: string
  order: 'asc' | 'desc'
  search?: string
  filters?: string
}

const ListView = ({ resource, onRowClick, onAdd, fixedFilters }: {
  resource: string,
  onRowClick?: (id: string | number) => void,
  onAdd?: () => void,
  fixedFilters?: Record<string, FieldValue>
}) => {
  const vocabulary = useVocabulary()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [metadata, setMetadata] = useState<Metadata | null>(null)
  const [data, setData] = useState<ListRow[]>([])
  const [loading, setLoading] = useState(true)
  const { notify, confirm } = useAras()
  const setPageTitle = useUIStore(state => state.setPageTitle)
  const showPanel = useUIStore(state => state.showPanel)
  const inlineEdit = useUIStore(state => state.inlineEdit)

  // Query State
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(20)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState<FilterRule[]>([])
  const [orderBy, setOrderBy] = useState('id')
  const [desc, setDesc] = useState(true)

  // Saved Filters State
  const [savedFilters, setSavedFilters] = useState<SavedFilter[]>([]);

  // UI State
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [selectedIds, setSelectedIds] = useState<(string | number)[]>([])
  const [visibleColumns, setVisibleColumns] = useState<string[]>([])
  const [isColumnPickerOpen, setIsColumnPickerOpen] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [bulkEditOpen, setBulkEditOpen] = useState(false)
  const [bulkEditField, setBulkEditField] = useState('')
  const [bulkEditValue, setBulkEditValue] = useState<FieldValue>('')
  const [bulkEditing, setBulkEditing] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [groupField, setGroupField] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<number>(0)
  const [editingCell, setEditingCell] = useState<{ id: string | number; field: string } | null>(null)
  const [editingValue, setEditingValue] = useState<FieldValue>('')
  const [cellErrors, setCellErrors] = useState<Record<string, string>>({})

  const roleFilter = searchParams.get('role') || 'all'
  const isPartyResource = useMemo(() => /(^|\/)(parties|party)$/.test(cleanResourcePath(resource)), [resource])
  const resourceApiPath = useMemo(
    () => cleanResourcePath(metadata?.api_path || resource),
    [metadata?.api_path, resource]
  )

  const [debouncedSearch, setDebouncedSearch] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300)
    return () => clearTimeout(timer)
  }, [search])

  const fetchData = useCallback(async (signal?: AbortSignal) => {
    try {
      setLoading(true)
      const cleanResource = cleanResourcePath(resource)
      const resourceApiPath = metadata?.api_path || cleanResource

      const params: ListParams = {
        page,
        per_page: perPage,
        sort: orderBy,
        order: desc ? 'desc' : 'asc',
      }

      if (debouncedSearch) params.search = debouncedSearch
      
      const allFilters = [...filters]
      if (fixedFilters) {
        Object.entries(fixedFilters).forEach(([field, value]) => {
          allFilters.push({ field, op: '=', value })
        })
      }

      if (isPartyResource && roleFilter !== 'all') {
        allFilters.push({ field: 'role', op: '=', value: roleFilter })
      }

      const listTabs = metadata?.list_tabs ?? []
      if (listTabs.length > 0 && activeTab > 0 && listTabs[activeTab - 1]) {
        const tabFilter = listTabs[activeTab - 1].filter
        allFilters.push({ field: tabFilter.field, op: '=', value: tabFilter.value })
      }

      if (allFilters.length > 0) {
        params.filters = JSON.stringify(allFilters)
      }

      const res = await api.get(`/${resourceApiPath}`, { params, signal })
      setData(res.data.items || [])
      setTotal(res.data.total || 0)
      setTotalPages(res.data.pages || 0)
    } catch (err) {
      if (isCanceledError(err)) return
      notify(getErrorMessage(err, "Failed to fetch data"), "error")
    } finally {
      setLoading(false)
    }
  }, [resource, metadata, page, perPage, orderBy, desc, debouncedSearch, filters, fixedFilters, isPartyResource, roleFilter, notify, activeTab])

  useEffect(() => { setActiveTab(0) }, [resource])

  useEffect(() => {
    const controller = new AbortController()
    const fetchMetadata = async () => {
      try {
        const cleanResource = cleanResourcePath(resource)
        const metaRes = await api.get(`/metadata/${cleanResource}`, { signal: controller.signal })
        const meta = metaRes.data
        setMetadata(meta)
        
        const defaultVisible = meta.fields
          .filter((f: Field) => !f.list_hidden && !f.hidden)
          .map((f: Field) => f.name)
        try {
          const pref = await api.get('/preference', { params: { key: `list:${cleanResource}:columns` }, signal: controller.signal })
          const saved = typeof pref.data?.value === 'string' ? JSON.parse(pref.data.value) : pref.data?.value
          setVisibleColumns(Array.isArray(saved) ? saved : defaultVisible)
        } catch {
          setVisibleColumns(defaultVisible)
        }
        const statusField = meta.fields.find((f: Field) => f.name === 'status' || f.name === 'state')
        if (statusField) setGroupField(statusField.name)
      } catch (err) {
        if (isCanceledError(err)) return
        notify(getErrorMessage(err, "Failed to load metadata"), "error")
      }
    }
    fetchMetadata()
    return () => controller.abort()
  }, [resource, notify])

  useEffect(() => {
    if (metadata) {
      const title = vocabulary.get(metadata.title)
      const resourceCrumb = cleanResourcePath(resource)
        .split('/')
        .filter(Boolean)
        .map(part => part.replace(/-/g, ' ').replace(/\b\w/g, char => char.toUpperCase()))
        .join(' / ')
      
      setPageTitle(
        title, 
        `Create, search, and manage ${title.toLowerCase()} records.`,
        resourceCrumb
      )
    }
    return () => setPageTitle('', '', '')
  }, [metadata, resource, vocabulary, setPageTitle])

  useEffect(() => {
    const controller = new AbortController()
    if (metadata) fetchData(controller.signal)
    return () => controller.abort()
  }, [fetchData, metadata])

  useEffect(() => {
    if (!metadata) return
    let timer: number | null = null
    const currentResource = cleanResourcePath(metadata.resource || resource)
    const handler = (event: Event) => {
      const detail = (event as CustomEvent).detail
      if (detail?.resource !== currentResource) return
      if (timer !== null) window.clearTimeout(timer)
      timer = window.setTimeout(() => fetchData(), 200)
    }
    window.addEventListener('aras:record-event', handler)
    return () => {
      if (timer !== null) window.clearTimeout(timer)
      window.removeEventListener('aras:record-event', handler)
    }
  }, [fetchData, metadata, resource])

  const fetchSavedFilters = useCallback(async () => {
    try {
      const cleanResource = cleanResourcePath(resource)
      const res = await api.get(`/sys_filters`, {
        params: { filters: JSON.stringify([{ field: 'resource', op: '=', value: cleanResource }]) }
      });
      setSavedFilters(res.data.items || []);
    } catch (e) { console.warn("Failed to fetch saved filters", e); }
  }, [resource]);

  useEffect(() => {
    fetchSavedFilters();
  }, [fetchSavedFilters]);

  const handleApplySavedFilter = (id: string) => {
    const sf = savedFilters.find(f => f.id === id);
    if (sf) {
      try {
        setFilters(JSON.parse(sf.filters_json));
        setPage(1);
      } catch (e) { notify("Invalid filter data", "error"); }
    }
  };

  const handleDeleteSavedFilter = async (id: string) => {
    if (!await confirm({ title: "Delete Filter", message: "Remove this saved filter?", type: 'danger' })) return;
    try {
      await api.delete(`/sys_filters/${id}`);
      fetchSavedFilters();
    } catch (e) { notify("Delete failed", "error"); }
  };

  const handleSelectAll = () => {
    if (selectedIds.length === data.length) setSelectedIds([])
    else setSelectedIds(data.map(item => item.id))
  }

  // Export this page's live schema + data sample to .aras/context/ for Claude Code (CLI).
  const handleSendToAI = async () => {
    try {
      const res = await api.post(`/ai-context/${resource}`, null, { params: { sample: 20 } })
      const d = res.data
      notify(`Context written: ${d.written} (${d.total_rows} rows). Read it in Claude Code.`, "success")
    } catch (err) {
      notify(getErrorMessage(err, "Failed to export AI context"), "error")
    }
  }

  const handleSelectOne = (id: string | number) => {
    if (selectedIds.includes(id)) setSelectedIds(selectedIds.filter(i => i !== id))
    else setSelectedIds([...selectedIds, id])
  }

  const handleBulkDelete = async () => {
    const ok = await confirm({
      title: 'Bulk Delete',
      message: `Are you sure you want to delete ${selectedIds.length} records?`,
      confirmText: 'Delete All',
      type: 'danger'
    })
    if (!ok) return
    try {
      await bulkDelete(resourceApiPath, selectedIds)
      notify(`${selectedIds.length} records deleted`, "success")
      setSelectedIds([])
      fetchData()
    } catch (err) {
      notify(getErrorMessage(err, "Bulk delete failed"), "error")
    }
  }

  const handleBulkEditSubmit = async () => {
    setBulkEditing(true)
    try {
      const ops = selectedIds.map(id => ({
        action: 'update',
        id,
        data: { [bulkEditField]: bulkEditValue }
      }))
      await api.post(`/${resourceApiPath}/batch`, ops)
      notify(`Updated ${selectedIds.length} records`, "success")
      setBulkEditOpen(false)
      setSelectedIds([])
      fetchData()
    } catch (err) {
      notify(getErrorMessage(err, "Bulk update failed"), "error")
    } finally {
      setBulkEditing(false)
    }
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      await exportCsv(resourceApiPath, `${resource.replace(/\//g, '_')}_export.csv`)
    } catch {
      notify("Export failed", "error")
    } finally {
      setIsExporting(false)
    }
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      await importCsv(resourceApiPath, file)
      notify("Import successful", "success")
      fetchData()
    } catch {
      notify("Import failed", "error")
    }
  }

  const handleDeleteOne = async (item: ListRow) => {
    if (!await confirm({ title: 'Delete record', message: `Are you sure you want to delete this record?`, type: 'danger' })) return
    try {
      await api.delete(`/${resourceApiPath}/${item.id}`)
      notify("Record deleted", "success")
      fetchData()
    } catch {
      notify("Delete failed", "error")
    }
  }

  const updateVisibleColumns = (columns: string[]) => {
    setVisibleColumns(columns)
    api.put('/preference', { key: `list:${cleanResourcePath(resource)}:columns`, value: columns }).catch(() => {})
  }

  const startCellEdit = (item: ListRow, field: Field) => {
    if (field.read_only) return
    setEditingCell({ id: item.id, field: field.name })
    setEditingValue(item[field.name] ?? '')
  }

  const cancelCellEdit = () => {
    setEditingCell(null)
    setEditingValue('')
  }

  const commitCellEdit = async () => {
    if (!editingCell) return
    const { id, field } = editingCell
    const fieldMeta = metadata?.fields.find((f) => f.name === field)
    if (fieldMeta) {
      const error = validateField(fieldMeta, editingValue)
      if (error) {
        setCellErrors((prev) => ({ ...prev, [`${id}:${field}`]: error }))
        notify(error, 'error')
        return
      }
    }
    try {
      await api.patch(`/${resourceApiPath}/${id}`, { [field]: editingValue })
      setData((rows) => rows.map((row) => row.id === id ? { ...row, [field]: editingValue } : row))
      setCellErrors((prev) => {
        const next = { ...prev }
        delete next[`${id}:${field}`]
        return next
      })
      notify('Cell updated', 'success')
      cancelCellEdit()
    } catch (err) {
      notify(getErrorMessage(err, 'Cell update failed'), 'error')
    }
  }


  const addFilter = () => {
    setFilters([...filters, { field: metadata?.fields[0]?.name || 'id', op: '=', value: '' }])
  }

  const updateFilter = (index: number, key: keyof FilterRule, value: FieldValue) => {
    const newFilters = [...filters]
    newFilters[index] = { ...newFilters[index], [key]: value }
    setFilters(newFilters)
  }

  const removeFilter = (index: number) => {
    setFilters(filters.filter((_, i) => i !== index))
  }

  if (!metadata) return <div className="p-8 text-center text-[var(--aras-muted)]">Loading component...</div>

  const fields = metadata.fields
  const orderedFields = fields.filter(f => !f.hidden)
  const listColumns = orderedFields
    .filter(f => visibleColumns.includes(f.name))
    .map(f => ({
      key: f.name,
      label: vocabulary.get(f.label),
      field: f,
      align: (f.type === 'number' || f.type === 'currency') ? 'right' : 'left',
      primary: f.name === 'name' || f.name === 'number' || f.name === 'title'
    }))

  const gridTemplateColumns = `48px ${listColumns.map(() => 'minmax(120px, 1fr)').join(' ')} 100px`
  const listMinWidth = 150 * listColumns.length + 150

  const getFieldValue = (item: ListRow, field: Field): FieldValue => {
    const val = item[field.name]
    if (field.type === 'lookup') {
      if (typeof val === 'object' && val !== null && !Array.isArray(val))
        return String((val as Record<string, unknown>).name || (val as Record<string, unknown>).title || (val as Record<string, unknown>).number || (val as Record<string, unknown>).id || '')
      const label = item[`${field.name}_label`]
      if (label != null) return String(label)
    }
    return val
  }

  const title = vocabulary.get(metadata.title)

  const groupableFields = orderedFields
    .filter(f => f.name === 'status' || f.name === 'state' || f.type === 'select' || f.type === 'lookup' || f.type === 'boolean')
    .map(f => ({ name: f.name, label: vocabulary.get(f.label) }))

  const groupedRows: { key: string; label: string; items: ListRow[] }[] = (() => {
    if (!groupField) return [{ key: '__all', label: '', items: data }]
    const fieldDef = fields.find(f => f.name === groupField)
    if (!fieldDef) return [{ key: '__all', label: '', items: data }]
    const groups = new Map<string, ListRow[]>()
    for (const item of data) {
      const raw = getFieldValue(item, fieldDef)
      const k = raw == null || raw === '' ? '—' : String(raw)
      if (!groups.has(k)) groups.set(k, [])
      groups.get(k)!.push(item)
    }
    return Array.from(groups.entries()).map(([key, items]) => ({ key, label: key, items }))
  })()

  return (
    <div className="aras-list-view flex flex-col h-full w-full min-w-0 overflow-hidden animate-in fade-in duration-500">
      <DesignContainer id="list-view-layout" className="flex flex-col flex-1 min-h-0 w-full min-w-0">
        
        {(metadata?.insights?.length ?? 0) > 0 && (
          <InsightStrip resource={resource} insights={metadata!.insights!} />
        )}

        <DesignElement id="toolbar" className="w-full">
          <ArasActionBar
            variant="full"
            title={title}
            search={search}
            onSearchChange={setSearch}
            isFilterOpen={isFilterOpen}
            onFilterToggle={() => setIsFilterOpen(!isFilterOpen)}
            filterCount={filters.length}
            selectedCount={selectedIds.length}
            onBulkEdit={() => setBulkEditOpen(true)}
            onBulkDelete={handleBulkDelete}
            onExport={handleExport}
            isExporting={isExporting}
            onImport={handleImport}
            onColumnPickerToggle={() => setIsColumnPickerOpen(!isColumnPickerOpen)}
            isColumnPickerOpen={isColumnPickerOpen}
            onAdd={onAdd || (() => navigate(`${resourceApiPath}/new`))}
            onArchive={metadata?.is_auditable ? () => navigate(`/${resourceApiPath}/archived`) : undefined}
            onSettings={() => showPanel('Form Settings', <FormSettings resource={resource} metadata={metadata} visibleColumns={visibleColumns} onVisibleColumnsChange={updateVisibleColumns} />, 'max-w-3xl')}
            onSendToAI={handleSendToAI}
            fields={orderedFields}
            visibleColumns={visibleColumns}
            onVisibleColumnsChange={updateVisibleColumns}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            hasTreeSupport={false}
            onSaveFilter={() => {}}
            onApplySavedFilter={handleApplySavedFilter}
            onDeleteSavedFilter={handleDeleteSavedFilter}
            savedFilters={savedFilters}
            groupField={groupField}
            onGroupFieldChange={setGroupField}
            groupableFields={groupableFields}
            page={page}
            perPage={perPage}
            total={total}
            totalPages={totalPages}
            onPerPageChange={(n) => { setPerPage(n); setPage(1); }}
          />
        </DesignElement>

        {isFilterOpen && (
          <DesignElement id="filter-bar" className="w-full bg-[var(--aras-panel-soft)] p-4 rounded-[var(--aras-radius)] border border-[var(--aras-border)] mb-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] font-semibold text-[var(--aras-muted)] uppercase tracking-wider">Filter Conditions</span>
              <button onClick={addFilter} className="text-xs font-semibold text-[var(--aras-accent)] hover:underline flex items-center gap-1">
                <Plus size={15} /> Add Rule
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {filters.map((f, i) => (
                <div key={i} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 bg-[var(--aras-panel)] p-3 rounded-[var(--aras-radius)] border border-[var(--aras-border)]">
                  <div className="flex-1 min-w-[120px]">
                    <Combobox
                      options={fields.map(field => ({ label: vocabulary.get(field.label), value: field.name }))}
                      value={f.field}
                      onChange={(val) => updateFilter(i, 'field', String(val))}
                      placeholder="Field..."
                    />
                  </div>
                  <div className="flex-1">
                    {(() => {
                      const fieldDef = fields.find(fd => fd.name === f.field);
                      if (!fieldDef) return null;
                      const FilterComponent = resolveFilterComponent(fieldDef);
                      return (
                        <FilterComponent
                          field={fieldDef}
                          value={f.value}
                          onChange={(val) => updateFilter(i, 'value', val as FieldValue)}
                          formData={{}}
                          disabled={false}
                        />
                      );
                    })()}
                  </div>
                  <button onClick={() => removeFilter(i)} className="flex-shrink-0 p-2 text-[var(--aras-muted)] hover:text-rose-500 rounded-[var(--app-radius)] transition-colors">
                    <X size={15} />
                  </button>
                </div>
              ))}
            </div>
            <div className="flex justify-end pt-2">
              <button onClick={() => { setFilters([]); setPage(1); }} className="text-xs font-semibold text-[var(--aras-muted)] mr-4">Reset</button>
              <button onClick={() => { setPage(1); fetchData(); }} className="px-4 py-2 bg-[var(--aras-accent)] text-white text-xs font-semibold rounded-[var(--aras-radius)] hover:opacity-90">Apply</button>
            </div>
          </DesignElement>
        )}

        {(metadata?.list_tabs?.length ?? 0) > 0 && (
          <DesignElement id="list-tabs" className="w-full px-1 pt-1 pb-0">
            <div className="flex items-center gap-1 border-b border-[var(--line)]">
              <button
                type="button"
                onClick={() => { setActiveTab(0); setPage(1); }}
                className={`px-4 py-2 text-[11.5px] font-bold transition-colors border-b-2 -mb-px ${activeTab === 0 ? 'border-[var(--accent)] text-[var(--accent)]' : 'border-transparent text-[var(--text-3)] hover:text-[var(--text-2)]'}`}
              >
                All
              </button>
              {metadata!.list_tabs!.map((tab, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => { setActiveTab(idx + 1); setPage(1); }}
                  className={`px-4 py-2 text-[11.5px] font-bold transition-colors border-b-2 -mb-px ${activeTab === idx + 1 ? 'border-[var(--accent)] text-[var(--accent)]' : 'border-transparent text-[var(--text-3)] hover:text-[var(--text-2)]'}`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </DesignElement>
        )}

        <DesignElement id="table" className="flex-1 overflow-auto w-full">
          {isPartyResource && (
            <div className="flex flex-wrap gap-1 border-b border-[var(--app-border)] bg-[var(--app-panel-soft)] px-4 py-2">
               <span className="text-[10px] font-black uppercase text-[var(--app-muted)] px-3">Role filtering active</span>
            </div>
          )}
          {viewMode === 'list' && (
            <div className="md:overflow-x-auto">
            <div className="aras-list-table md:[min-width:var(--list-min-width)]" aria-live="polite" aria-busy={loading} style={{ '--list-min-width': typeof listMinWidth === 'number' ? `${listMinWidth}px` : listMinWidth } as CSSProperties & Record<'--list-min-width', string>}>
              {/* Section header row — only when at least one visible column has a section */}
              {listColumns.some(c => c.field.section) && (() => {
                // Build section spans: [{label, span}] where span = number of grid columns
                const spans: { label: string; span: number }[] = [{ label: '', span: 1 }] // checkbox col
                for (const col of listColumns) {
                  const sec = col.field.section ?? ''
                  if (spans.length > 1 && spans[spans.length - 1].label === sec) {
                    spans[spans.length - 1].span++
                  } else {
                    spans.push({ label: sec, span: 1 })
                  }
                }
                spans.push({ label: '', span: 1 }) // actions col
                return (
                  <div className="hidden md:flex sticky top-0 z-10 border-t border-b border-[var(--line)]" style={{ background: 'var(--bg)' }}>
                    {spans.map((s, i) => (
                      <div key={i} style={{ flex: s.label ? s.span : '0 0 auto', minWidth: s.label ? undefined : i === 0 ? 48 : 100 }} className={`text-[9.5px] font-black uppercase tracking-[0.2em] px-3 py-1 ${s.label ? 'text-[var(--accent)] border-r border-[var(--line)]' : 'text-transparent'}`}>
                        {s.label || '.'}
                      </div>
                    ))}
                  </div>
                )
              })()}
              <div className="aras-list-header hidden md:grid sticky top-0 z-10 border-b border-[var(--line)]" style={{ gridTemplateColumns, background: 'var(--bg)', fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '.14em', color: 'var(--text-3)', textTransform: 'uppercase' }}>
                <div style={{ padding: '10px 12px' }}><button onClick={handleSelectAll} className="hover:text-[var(--app-accent)]">{selectedIds.length === data.length && data.length > 0 ? <CheckSquare size={15} className="text-[var(--app-accent)]" /> : <Square size={15} className="text-[var(--app-muted)]" />}</button></div>
                {listColumns.map((column) => (
                  <div key={column.key} className={`flex items-center gap-1.5 cursor-pointer hover:text-[var(--text)] transition-colors ${column.align === 'right' ? 'justify-end text-right' : ''}`} style={{ padding: '10px 12px', fontWeight: 500 }} onClick={() => { if (orderBy === column.field.name) setDesc(!desc); else { setOrderBy(column.field.name); setDesc(true); } }}>
                    {column.label}
                    {orderBy === column.field.name && (desc ? <ChevronDown size={14} className="text-[var(--app-accent)]" /> : <ChevronUp size={14} className="text-[var(--app-accent)]" />)}
                  </div>
                ))}
                <div style={{ padding: '10px 12px', textAlign: 'right' }}>&nbsp;</div>
              </div>

              {loading ? (
                <div role="status" aria-label="Loading...">
                  {Array.from({ length: 10 }).map((_, i) => (
                    <SkeletonRow
                      key={i}
                      variant="grid"
                      columns={listColumns.length + 2}
                      gridTemplateColumns={gridTemplateColumns}
                    />
                  ))}
                </div>
              ) : data.length === 0 ? (
                <div className="px-6 py-20 text-center">
                  <Search size={53} className="mb-4 text-[var(--app-border-strong)] mx-auto" />
                  <p className="text-[calc(15px*var(--app-font-scale))] font-extrabold text-[var(--app-text)]">No records found.</p>
                </div>
              ) : (
                groupedRows.map((group) => (
                  <div key={group.key}>
                    {groupField && (
                      <div className="md:hidden flex items-center gap-2 px-4 pt-3 pb-1 text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-3)]">
                        <StatusGlyph value={group.key} />
                        <span>{group.label}</span>
                        <span>·</span>
                        <span>{group.items.length}</span>
                      </div>
                    )}
                    {groupField && (
                      <div className="hidden md:grid items-center" style={{ gridTemplateColumns }}>
                        <div className="px-[calc(16px*var(--app-density))] py-2 flex items-center">
                          <StatusGlyph value={group.key} />
                        </div>
                        <div className="col-span-full px-2 py-2 text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-3)] flex items-center gap-2" style={{ gridColumn: `2 / -1` }}>
                          <span>{group.label}</span>
                          <span>·</span>
                          <span>{group.items.length}</span>
                        </div>
                      </div>
                    )}
                    {group.items.map((item) => {
                      return (
                      <div key={item.id} className={`aras-list-row hidden md:grid items-center group border-b border-[var(--line)] hover:bg-[var(--surface-2)] transition-colors ${inlineEdit ? '' : 'cursor-pointer'} ${selectedIds.includes(item.id) ? 'bg-[var(--accent)]/8' : ''}`} style={{ gridTemplateColumns }} onClick={() => { if (!inlineEdit) onRowClick?.(item.id) }}>
                        <div className="px-[calc(16px*var(--app-density))] py-[calc(8px*var(--app-density))]" onClick={(e) => e.stopPropagation()}>
                          <button onClick={() => handleSelectOne(item.id)} className={`${selectedIds.includes(item.id) ? 'text-[var(--accent)]' : 'text-[var(--text-3)]'}`}>
                            {selectedIds.includes(item.id) ? <CheckSquare size={17} /> : <Square size={17} />}
                          </button>
                        </div>
                        {listColumns.map((column, colIdx) => {
                          const value = getFieldValue(item, column.field)
                          const isIdCol = colIdx === 0 && (column.field.name === 'id' || column.field.name === 'number' || column.field.name === 'code')
                          const isEditing = editingCell?.id === item.id && editingCell?.field === column.field.name
                          return (
                            <div key={column.key} onClick={(e) => { if (inlineEdit) { e.stopPropagation(); startCellEdit(item, column.field) } }} className={`px-[calc(6px*var(--app-density))] py-[calc(8px*var(--app-density))] min-w-0 ${column.align === 'right' ? 'text-right' : ''} ${inlineEdit && !column.field.read_only ? 'cursor-cell hover:bg-[var(--accent)]/5' : ''}`}>
                              {isEditing ? (() => {
                                const FieldComponent = resolveFieldComponent(column.field)
                                const error = cellErrors[`${item.id}:${column.field.name}`]
                                return (
                                  <div
                                    onClick={(e) => e.stopPropagation()}
                                    onKeyDown={(e) => {
                                      if (e.key === 'Escape') cancelCellEdit()
                                      if (e.key === 'Enter' || e.key === 'Tab') {
                                        e.preventDefault()
                                        commitCellEdit()
                                      }
                                    }}
                                    onBlur={(e) => {
                                      if (!e.currentTarget.contains(e.relatedTarget as Node)) commitCellEdit()
                                    }}
                                  >
                                    <FieldComponent
                                      field={column.field}
                                      value={editingValue}
                                      onChange={(val) => setEditingValue(val as FieldValue)}
                                      formData={item}
                                      disabled={false}
                                      aria-invalid={!!error}
                                    />
                                    {error && <div className="mt-1 text-[11px] text-rose-600">{error}</div>}
                                  </div>
                                )
                              })() : isIdCol ? (
                                <span className="arc-id text-[12px]">
                                  <b>{String(value)}</b>
                                </span>
                              ) : (
                                <div className={`${column.primary ? 'font-semibold text-[var(--text)]' : 'text-[var(--text-2)]'} truncate text-[calc(13px*var(--app-font-scale))]`}>
                                  {renderCellValue(value, column.field.type, column.field.name)}
                                </div>
                              )}
                            </div>
                          )
                        })}
                        <div className="px-[calc(16px*var(--app-density))] py-[calc(8px*var(--app-density))] flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          {inlineEdit && (
                            <button type="button" onClick={(e) => { e.stopPropagation(); onRowClick?.(item.id) }} className="p-1.5 text-[var(--text-3)] hover:text-[var(--accent)] rounded transition-colors" title="Open form"><Pencil size={14} /></button>
                          )}
                          <button type="button" onClick={(e) => { e.stopPropagation(); handleDeleteOne(item); }} className="p-1.5 text-[var(--text-3)] hover:text-rose-500 rounded transition-colors"><Trash2 size={15} /></button>
                          {!inlineEdit && <ChevronRight size={15} className="text-[var(--text-3)]" />}
                        </div>
                      </div>
                      )
                    })}
                    {/* Mobile cards */}
                    {group.items.map((item) => {
                      const idField = listColumns.find((c, i) => i === 0 && (c.field.name === 'id' || c.field.name === 'number' || c.field.name === 'code'))
                      const idValue = idField ? getFieldValue(item, idField.field) : item.id
                      const primaryCol = listColumns.find((c) => c.primary) || listColumns[1] || listColumns[0]
                      const primaryValue = primaryCol ? getFieldValue(item, primaryCol.field) : ''
                      const statusValue = item.status ?? item.state
                      return (
                        <div
                          key={`m-${item.id}`}
                          className={`md:hidden flex items-start gap-3 px-4 py-3 border-b border-[var(--line)] active:bg-[var(--surface-2)] cursor-pointer ${selectedIds.includes(item.id) ? 'bg-[var(--accent)]/8' : ''}`}
                          onClick={() => onRowClick?.(item.id)}
                        >
                          <div className="pt-0.5"><StatusGlyph value={statusValue} /></div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="arc-id text-[11.5px]"><b>{String(idValue)}</b></span>
                            </div>
                            <div className="mt-0.5 truncate text-[13.5px] font-semibold text-[var(--text)]">{String(primaryValue ?? '')}</div>
                          </div>
                          <ChevronRight size={17} className="text-[var(--text-3)] shrink-0 mt-1" />
                        </div>
                      )
                    })}
                  </div>
                ))
              )}
              </div>
            </div>
          )}
        </DesignElement>

        {viewMode === 'list' && totalPages > 1 && (
          <DesignElement id="pagination" className="mt-2 px-5 sm:px-7 lg:px-8 py-2 flex items-center justify-center gap-1 w-full">
            <button
              disabled={page === 1}
              onClick={() => setPage(1)}
              className="h-7 w-7 grid place-items-center rounded-full text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              title="First page"
            >
              <ChevronsLeft size={15} />
            </button>
            <button
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="h-7 w-7 grid place-items-center rounded-full text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              title="Previous page"
            >
              <ChevronLeft size={15} />
            </button>
            <span className="px-3 text-[11.5px] tabular-nums text-[var(--text-2)]">
              <b>{page}</b> <span className="text-[var(--text-3)]">/ {totalPages}</span>
            </span>
            <button
              disabled={page === totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="h-7 w-7 grid place-items-center rounded-full text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              title="Next page"
            >
              <ChevronRight size={15} />
            </button>
            <button
              disabled={page === totalPages}
              onClick={() => setPage(totalPages)}
              className="h-7 w-7 grid place-items-center rounded-full text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              title="Last page"
            >
              <ChevronsRight size={15} />
            </button>
          </DesignElement>
        )}

      </DesignContainer>

      {/* Bottom status footer — locked to viewport bottom, hints always visible */}
      <div className="flex items-center justify-between gap-4 border-t border-[var(--line)] py-2 px-5 sm:px-7 lg:px-8 text-[11px] text-[var(--text-3)] flex-shrink-0 w-full min-w-0">
        <div className="flex-shrink-0 whitespace-nowrap">
          {selectedIds.length > 0 ? (
            <><span className="arc-id"><b>{selectedIds.length}</b></span> selected</>
          ) : (
            <>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-2)' }}>
                {Math.min(page * perPage, total).toLocaleString()}
              </span>
              <span> of </span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-2)' }}>
                {total.toLocaleString()}
              </span>
              <span> {total === 1 ? 'record' : 'records'}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-3 flex-wrap justify-end min-w-0">
          <span className="whitespace-nowrap">↑↓ navigate</span>
          <span aria-hidden>·</span>
          <span className="whitespace-nowrap">Enter open</span>
          <span aria-hidden>·</span>
          <span className="whitespace-nowrap">/ search</span>
          <span aria-hidden>·</span>
          <span className="whitespace-nowrap"><span className="arc-kbd">⌘K</span> commands</span>
        </div>
      </div>

      {/* Bulk Edit Modal */}
      {bulkEditOpen && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-[var(--aras-panel)] rounded-[var(--aras-radius)] border border-[var(--aras-border)] w-full max-w-md p-6 space-y-5">
            <h3 className="text-lg font-semibold">Bulk Edit — {selectedIds.length} rows</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold mb-1 block">Field</label>
                <Combobox
                  options={(metadata?.fields ?? []).filter(f => !f.read_only && !f.hidden).map(f => ({ label: vocabulary.get(f.label), value: f.name }))}
                  value={bulkEditField}
                  onChange={val => { setBulkEditField(String(val)); setBulkEditValue(''); }}
                  placeholder="Select field..."
                />
              </div>
              <div>
                <label className="text-xs font-semibold mb-1 block">New Value</label>
                {(() => {
                  const field = metadata?.fields.find(f => f.name === bulkEditField);
                  if (!field) return null;
                  const FieldComponent = resolveFieldComponent(field);
                  return <FieldComponent field={field} value={bulkEditValue} onChange={(val) => setBulkEditValue(val as FieldValue)} formData={{}} disabled={false} />;
                })()}
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setBulkEditOpen(false)} className="flex-1 px-4 py-2 border border-[var(--app-border)] rounded-[var(--app-radius)] text-[var(--app-muted)] hover:bg-[var(--app-panel-soft)] transition-colors">Cancel</button>
              <button onClick={handleBulkEditSubmit} disabled={bulkEditing || !bulkEditField} className="flex-1 px-4 py-2 bg-[var(--app-primary-action)] text-white rounded-[var(--app-radius)] font-bold shadow-lg shadow-[var(--app-accent-glow)] hover:brightness-110 active:scale-95 transition-all">{bulkEditing ? 'Saving...' : 'Apply Changes'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ListView

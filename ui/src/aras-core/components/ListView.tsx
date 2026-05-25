import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../../lib/api'
import { cleanResourcePath } from '../../lib/resourceUtils'
import {
  Plus, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight,
  CheckSquare, Square, X,
  ChevronDown, ChevronUp, Trash2, Search
} from 'lucide-react'
import { resolveFieldComponent, resolveFilterComponent } from '../SchemaRegistry'
import { useAras } from '../hooks/useAras'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'
import Combobox from './Combobox'

import ListViewActionBar from './ListViewActionBar'
import type { ViewMode } from './ListViewActionBar'
import { useVocabulary } from '../../context/VocabularyContext'
import { FormattingService } from '../services/FormattingService'
import { DesignContainer } from './design/DesignContainer'
import { DesignElement } from './design/DesignElement'

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
  options?: { label: string; value: any }[]
}

interface Metadata {
  resource: string
  api_path?: string | null
  title: string
  fields: Field[]
  is_auditable?: boolean
}

interface FilterRule {
  field: string
  op: string
  value: any
}

interface SavedFilter {
  id: string;
  resource: string;
  name: string;
  filters_json: string;
  is_default: boolean;
}

const ListView = ({ resource, onRowClick, onAdd, fixedFilters }: {
  resource: string,
  onRowClick?: (id: string | number) => void,
  onAdd?: () => void,
  fixedFilters?: Record<string, any>
}) => {
  const vocabulary = useVocabulary()
  const navigate = useNavigate()
  const { activeOrgId } = useAuthStore()
  const [searchParams] = useSearchParams()
  const [metadata, setMetadata] = useState<Metadata | null>(null)
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const { notify, confirm } = useAras()
  const setPageTitle = useUIStore(state => state.setPageTitle)

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
  const [bulkEditValue, setBulkEditValue] = useState<any>('')
  const [bulkEditing, setBulkEditing] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [groupField, setGroupField] = useState<string | null>(null)

  const roleFilter = searchParams.get('role') || 'all'
  const isPartyResource = useMemo(() => /(^|\/)(parties|party)$/.test(cleanResourcePath(resource)), [resource])
  const resourceApiPath = useMemo(
    () => cleanResourcePath(metadata?.api_path || resource),
    [metadata?.api_path, resource]
  )

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      const cleanResource = cleanResourcePath(resource)
      const resourceApiPath = metadata?.api_path || cleanResource

      const params: any = {
        page,
        per_page: perPage,
        sort: orderBy,
        order: desc ? 'desc' : 'asc',
      }

      if (search) params.search = search
      
      const allFilters = [...filters]
      if (fixedFilters) {
        Object.entries(fixedFilters).forEach(([field, value]) => {
          allFilters.push({ field, op: '=', value })
        })
      }
      
      if (activeOrgId) {
        allFilters.push({ field: 'org_id', op: '=', value: activeOrgId })
      }

      if (isPartyResource && roleFilter !== 'all') {
        allFilters.push({ field: 'role', op: '=', value: roleFilter })
      }

      if (allFilters.length > 0) {
        params.filters = JSON.stringify(allFilters)
      }

      const res = await api.get(`/${resourceApiPath}`, { params })
      setData(res.data.items || [])
      setTotal(res.data.total || 0)
      setTotalPages(res.data.pages || 0)
    } catch (err: any) {
      notify(err.response?.data?.detail || "Failed to fetch data", "error")
    } finally {
      setLoading(false)
    }
  }, [resource, metadata, page, perPage, orderBy, desc, search, filters, fixedFilters, activeOrgId, isPartyResource, roleFilter, notify])

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const cleanResource = cleanResourcePath(resource)
        const metaRes = await api.get(`/metadata/${cleanResource}`)
        const meta = metaRes.data
        setMetadata(meta)
        
        const defaultVisible = meta.fields
          .filter((f: any) => !f.list_hidden && !f.hidden)
          .map((f: any) => f.name)
        setVisibleColumns(defaultVisible)
        const statusField = meta.fields.find((f: any) => f.name === 'status' || f.name === 'state')
        if (statusField) setGroupField(statusField.name)
      } catch (err: any) {
        notify(err.response?.data?.detail || "Failed to load metadata", "error")
      }
    }
    fetchMetadata()
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
    if (metadata) fetchData()
  }, [fetchData, metadata])

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
      await api.post(`/${resourceApiPath}/batch-delete`, { ids: selectedIds })
      notify(`${selectedIds.length} records deleted`, "success")
      setSelectedIds([])
      fetchData()
    } catch (err: any) {
      notify(err.response?.data?.detail || "Bulk delete failed", "error")
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
    } catch (err: any) {
      notify(err.response?.data?.detail || "Bulk update failed", "error")
    } finally {
      setBulkEditing(false)
    }
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      const res = await api.get(`/${resourceApiPath}/export`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${resource.replace(/\//g, '_')}_export.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err: any) {
      notify("Export failed", "error")
    } finally {
      setIsExporting(false)
    }
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      await api.post(`/${resourceApiPath}/import`, formData)
      notify("Import successful", "success")
      fetchData()
    } catch (err: any) {
      notify("Import failed", "error")
    }
  }

  const handleDeleteOne = async (item: any) => {
    if (!await confirm({ title: 'Delete record', message: `Are you sure you want to delete this record?`, type: 'danger' })) return
    try {
      await api.delete(`/${resourceApiPath}/${item.id}`)
      notify("Record deleted", "success")
      fetchData()
    } catch (err: any) {
      notify("Delete failed", "error")
    }
  }

  const addFilter = () => {
    setFilters([...filters, { field: metadata?.fields[0]?.name || 'id', op: '=', value: '' }])
  }

  const updateFilter = (index: number, key: keyof FilterRule, value: any) => {
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

  const getFieldValue = (item: any, field: Field) => {
    const val = item[field.name]
    if (field.type === 'lookup' && typeof val === 'object' && val !== null) {
      return val.name || val.title || val.number || val.id
    }
    return val
  }

  const title = vocabulary.get(metadata.title)

  const groupableFields = orderedFields
    .filter(f => f.name === 'status' || f.name === 'state' || f.type === 'select' || f.type === 'lookup' || f.type === 'boolean')
    .map(f => ({ name: f.name, label: vocabulary.get(f.label) }))

  const groupedRows: { key: string; label: string; items: any[] }[] = (() => {
    if (!groupField) return [{ key: '__all', label: '', items: data }]
    const fieldDef = fields.find(f => f.name === groupField)
    if (!fieldDef) return [{ key: '__all', label: '', items: data }]
    const groups = new Map<string, any[]>()
    for (const item of data) {
      const raw = getFieldValue(item, fieldDef)
      const k = raw == null || raw === '' ? '—' : String(raw)
      if (!groups.has(k)) groups.set(k, [])
      groups.get(k)!.push(item)
    }
    return Array.from(groups.entries()).map(([key, items]) => ({ key, label: key, items }))
  })()

  return (
    <div className="aras-list-view flex flex-col h-full animate-in fade-in duration-500">
      <DesignContainer id="list-view-layout" className="flex flex-col h-full w-full">
        
        <DesignElement id="toolbar" className="w-full">
          <ListViewActionBar
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
            fields={orderedFields}
            visibleColumns={visibleColumns}
            onVisibleColumnsChange={setVisibleColumns}
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
                <Plus size={14} /> Add Rule
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
                          onChange={(val) => updateFilter(i, 'value', val)}
                          formData={{}}
                          disabled={false}
                        />
                      );
                    })()}
                  </div>
                  <button onClick={() => removeFilter(i)} className="flex-shrink-0 p-2 text-[var(--aras-muted)] hover:text-rose-500 rounded-[var(--app-radius)] transition-colors">
                    <X size={14} />
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

        <DesignElement id="table" className="border-t border-[var(--line)] flex-1 overflow-auto w-full mt-2">
          {isPartyResource && (
            <div className="flex flex-wrap gap-1 border-b border-[var(--app-border)] bg-[var(--app-panel-soft)] px-4 py-2">
               <span className="text-[10px] font-black uppercase text-[var(--app-muted)] px-3">Role filtering active</span>
            </div>
          )}
          {viewMode === 'list' && (
            <div className="md:overflow-x-auto">
              <div className="aras-list-table md:[min-width:var(--list-min-width)]" style={{ ['--list-min-width' as any]: typeof listMinWidth === 'number' ? `${listMinWidth}px` : listMinWidth }}>
              <div className="aras-list-header hidden md:grid sticky top-0 z-10 border-b border-[var(--line)] bg-[var(--surface)]/80 backdrop-blur" style={{ gridTemplateColumns }}>
                <div className="px-[calc(16px*var(--app-density))] py-[calc(18px*var(--app-density))]"><button onClick={handleSelectAll} className="hover:text-[var(--app-accent)]">{selectedIds.length === data.length && data.length > 0 ? <CheckSquare size={18} className="text-[var(--app-accent)]" /> : <Square size={18} className="text-[var(--app-muted)]" />}</button></div>
                {listColumns.map((column) => (
                  <div key={column.key} className={`px-[calc(6px*var(--app-density))] py-2.5 flex items-center gap-1.5 text-[10px] font-bold text-[var(--text-3)] uppercase tracking-[0.14em] cursor-pointer hover:text-[var(--text)] transition-colors ${column.align === 'right' ? 'justify-end text-right' : ''}`} onClick={() => { if (orderBy === column.field.name) setDesc(!desc); else { setOrderBy(column.field.name); setDesc(true); } }}>
                    {column.label}
                    {orderBy === column.field.name && (desc ? <ChevronDown size={14} className="text-[var(--app-accent)]" /> : <ChevronUp size={14} className="text-[var(--app-accent)]" />)}
                  </div>
                ))}
                <div className="px-[calc(16px*var(--app-density))] py-2.5 text-right text-[10px] font-bold text-[var(--text-3)] uppercase tracking-[0.14em]">&nbsp;</div>
              </div>

              {loading ? (
                <div className="p-[calc(80px*var(--app-density))] text-center animate-pulse text-[var(--app-muted)] font-bold">Fetching records...</div>
              ) : data.length === 0 ? (
                <div className="px-6 py-20 text-center">
                  <Search size={48} className="mb-4 text-[var(--app-border-strong)] mx-auto" />
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
                      const prefix = (resource.split('/').pop() || '').toUpperCase().slice(0, 3) || 'ARC'
                      return (
                      <div key={item.id} className={`aras-list-row hidden md:grid items-center group border-b border-[var(--line)] hover:bg-[var(--surface-2)] transition-colors cursor-pointer ${selectedIds.includes(item.id) ? 'bg-[var(--accent)]/8' : ''}`} style={{ gridTemplateColumns }} onClick={() => onRowClick?.(item.id)}>
                        <div className="px-[calc(16px*var(--app-density))] py-[calc(8px*var(--app-density))]" onClick={(e) => e.stopPropagation()}>
                          <button onClick={() => handleSelectOne(item.id)} className={`${selectedIds.includes(item.id) ? 'text-[var(--accent)]' : 'text-[var(--text-3)]'}`}>
                            {selectedIds.includes(item.id) ? <CheckSquare size={15} /> : <Square size={15} />}
                          </button>
                        </div>
                        {listColumns.map((column, colIdx) => {
                          const value = getFieldValue(item, column.field)
                          const isIdCol = colIdx === 0 && (column.field.name === 'id' || column.field.name === 'number' || column.field.name === 'code')
                          return (
                            <div key={column.key} className={`px-[calc(6px*var(--app-density))] py-[calc(8px*var(--app-density))] min-w-0 ${column.align === 'right' ? 'text-right' : ''}`}>
                              {isIdCol ? (
                                <span className="arc-id text-[12px]">
                                  <b>{prefix}</b> · <b>{String(value)}</b>
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
                          <button type="button" onClick={(e) => { e.stopPropagation(); handleDeleteOne(item); }} className="p-1.5 text-[var(--text-3)] hover:text-rose-500 rounded transition-colors"><Trash2 size={14} /></button>
                          <ChevronRight size={14} className="text-[var(--text-3)]" />
                        </div>
                      </div>
                      )
                    })}
                    {/* Mobile cards */}
                    {group.items.map((item) => {
                      const prefix = (resource.split('/').pop() || '').toUpperCase().slice(0, 3) || 'ARC'
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
                              <span className="arc-id text-[11.5px]"><b>{prefix}</b> · <b>{String(idValue)}</b></span>
                            </div>
                            <div className="mt-0.5 truncate text-[13.5px] font-semibold text-[var(--text)]">{String(primaryValue ?? '')}</div>
                          </div>
                          <ChevronRight size={15} className="text-[var(--text-3)] shrink-0 mt-1" />
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
              <ChevronsLeft size={14} />
            </button>
            <button
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="h-7 w-7 grid place-items-center rounded-full text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              title="Previous page"
            >
              <ChevronLeft size={14} />
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
              <ChevronRight size={14} />
            </button>
            <button
              disabled={page === totalPages}
              onClick={() => setPage(totalPages)}
              className="h-7 w-7 grid place-items-center rounded-full text-[var(--text-3)] hover:text-[var(--text)] hover:bg-[var(--surface-2)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              title="Last page"
            >
              <ChevronsRight size={14} />
            </button>
          </DesignElement>
        )}

      </DesignContainer>

      {/* Bottom status footer */}
      <div className="flex items-center justify-between border-t border-[var(--line)] py-2 px-5 sm:px-7 lg:px-8 text-[11px] text-[var(--text-3)]">
        <div>
          {selectedIds.length > 0
            ? <><span className="arc-id"><b>{selectedIds.length}</b></span> selected</>
            : <>{total} {total === 1 ? 'record' : 'records'}</>}
        </div>
        <div className="flex items-center gap-3">
          <span>↑↓ navigate</span>
          <span>·</span>
          <span>Enter open</span>
          <span>·</span>
          <span>/ search</span>
          <span>·</span>
          <span className="arc-kbd">⌘K</span>
          <span>commands</span>
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
                  return <FieldComponent field={field} value={bulkEditValue} onChange={setBulkEditValue} formData={{}} disabled={false} />;
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

const roleColors: Record<string, string> = {
  customer: 'bg-sky-50 text-sky-700 border-sky-100',
  supplier: 'bg-amber-50 text-amber-700 border-amber-100',
  member: 'bg-violet-50 text-violet-700 border-violet-100',
  other: 'bg-[var(--aras-panel-soft)] text-[var(--aras-muted)] border-[var(--aras-border)]',
}

// claude-opus-4-7
const STATUS_GLYPH: Record<string, { ch: string; color: string }> = {
  in_progress: { ch: '◐', color: 'var(--accent)' },
  'in progress': { ch: '◐', color: 'var(--accent)' },
  draft:       { ch: '○', color: 'var(--text-3)' },
  open:        { ch: '○', color: 'var(--text-3)' },
  in_review:   { ch: '△', color: '#d97706' },
  'in review': { ch: '△', color: '#d97706' },
  pending:     { ch: '△', color: '#d97706' },
  released:    { ch: '●', color: '#059669' },
  active:      { ch: '●', color: '#059669' },
  posted:      { ch: '●', color: '#059669' },
  approved:    { ch: '●', color: '#059669' },
  blocked:     { ch: '✕', color: '#e11d48' },
  cancelled:   { ch: '✕', color: '#e11d48' },
  rejected:    { ch: '✕', color: '#e11d48' },
}
// claude-opus-4-7
function StatusGlyph({ value }: { value: any }) {
  const key = String(value ?? '').toLowerCase().trim()
  const g = STATUS_GLYPH[key] || { ch: '○', color: 'var(--text-3)' }
  return <span style={{ color: g.color, fontFamily: 'Geist Mono, ui-monospace, monospace', fontSize: 13 }}>{g.ch}</span>
}

const renderCellValue = (value: any, type: string, fieldName?: string) => {
  if (value === null || value === undefined) return <span className="text-[var(--aras-muted)]">-</span>
  if (fieldName === 'status' || fieldName === 'state' || type === 'boolean') {
    const rawLabel = typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)
    return <span className="inline-flex items-center gap-2 text-[13px] font-medium capitalize text-[var(--text-2)]"><StatusGlyph value={rawLabel} />{rawLabel.replace(/_/g, ' ')}</span>
  }
  if (fieldName === 'role') {
    return <span className={`inline-flex rounded-[var(--aras-radius)] border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${roleColors[String(value)] || roleColors.other}`}>{String(value)}</span>
  }
  switch (type) {
    case 'currency': return <span className="text-[var(--aras-text)] font-bold">{FormattingService.formatCurrency(value)}</span>
    case 'date':
    case 'datetime': return FormattingService.formatDate(value)
    default: return String(value)
  }
}

export default ListView

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../../lib/api'
import { cleanResourcePath } from '../../lib/resourceUtils'
import {
  Plus, ChevronLeft, ChevronRight,
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
                  <button onClick={() => removeFilter(i)} className="flex-shrink-0 p-2 text-[var(--aras-muted)] hover:text-rose-500 rounded-xl transition-colors">
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

        <DesignElement id="table" className="glass-panel island flex-1 overflow-auto w-full mt-4">
          {isPartyResource && (
            <div className="flex flex-wrap gap-1 border-b border-[var(--aras-border)] bg-[var(--aras-panel-soft)] px-4 py-2">
               <span className="text-[10px] font-black uppercase text-[var(--aras-muted)] px-3">Role filtering active</span>
            </div>
          )}
          {viewMode === 'list' && (
            <div className="overflow-x-auto">
              <div className="aras-list-table" style={{ minWidth: listMinWidth }}>
              <div className="aras-list-header hidden md:grid" style={{ gridTemplateColumns }}>
                <div><button onClick={handleSelectAll} className="hover:text-[var(--aras-accent)]">{selectedIds.length === data.length && data.length > 0 ? <CheckSquare size={16} className="text-[var(--aras-accent)]" /> : <Square size={16} />}</button></div>
                {listColumns.map((column) => (
                  <div key={column.key} className={`aras-list-header__cell ${column.align === 'right' ? 'justify-end text-right' : ''}`} onClick={() => { if (orderBy === column.field.name) setDesc(!desc); else { setOrderBy(column.field.name); setDesc(true); } }}>
                    {column.label}
                    {orderBy === column.field.name && (desc ? <ChevronDown size={14} className="text-[var(--aras-accent)]" /> : <ChevronUp size={14} className="text-[var(--aras-accent)]" />)}
                  </div>
                ))}
                <div className="text-right">Action</div>
              </div>

              {loading ? (
                <div className="p-20 text-center animate-pulse text-[var(--aras-muted)]">Fetching records...</div>
              ) : data.length === 0 ? (
                <div className="px-6 py-20 text-center">
                  <Search size={48} className="mb-4 opacity-20 mx-auto" />
                  <p className="text-[15px] font-bold text-[var(--aras-text)]">No records found.</p>
                </div>
              ) : (
                data.map((item) => (
                  <div key={item.id} className={`aras-list-row grid items-center group ${selectedIds.includes(item.id) ? 'is-selected' : ''}`} style={{ gridTemplateColumns }} onClick={() => onRowClick?.(item.id)}>
                    <div onClick={(e) => e.stopPropagation()}><button onClick={() => handleSelectOne(item.id)} className={`${selectedIds.includes(item.id) ? 'text-[var(--aras-accent)]' : 'text-[var(--aras-border-strong)]'}`}>{selectedIds.includes(item.id) ? <CheckSquare size={18} /> : <Square size={18} />}</button></div>
                    {listColumns.map((column) => {
                      const value = getFieldValue(item, column.field)
                      return (
                        <div key={column.key} className={`min-w-0 ${column.align === 'right' ? 'text-right' : ''}`}>
                          <div className={`${column.primary ? 'font-extrabold text-[var(--aras-foreground)]' : 'font-semibold text-[var(--aras-muted)]'} truncate text-sm`}>
                            {renderCellValue(value, column.field.type, column.field.name)}
                          </div>
                        </div>
                      )
                    })}
                    <div className="flex items-center justify-end gap-1">
                      <button type="button" onClick={(e) => { e.stopPropagation(); handleDeleteOne(item); }} className="p-2 text-[var(--aras-muted)] hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-colors"><Trash2 size={16} /></button>
                      <ChevronRight size={18} className="text-[var(--aras-muted)]" />
                    </div>
                  </div>
                ))
              )}
              </div>
            </div>
          )}
        </DesignElement>

        {viewMode === 'list' && (
          <DesignElement id="pagination" className="mt-3 aras-island p-3 flex flex-wrap items-center justify-between gap-3 w-full">
            <div className="flex items-center gap-4">
              <span className="text-xs font-medium text-[var(--aras-muted)]">Showing {(page-1)*perPage + 1} to {Math.min(page*perPage, total)} of {total}</span>
              <div className="min-w-[120px]">
                <Combobox
                  options={[
                    { label: '10 per page', value: 10 },
                    { label: '20 per page', value: 20 },
                    { label: '50 per page', value: 50 },
                    { label: '100 per page', value: 100 }
                  ]}
                  value={perPage}
                  onChange={(val) => { setPerPage(Number(val)); setPage(1); }}
                />
              </div>
            </div>
            <div className="flex items-center border border-[var(--aras-border-strong)] rounded-[var(--aras-radius)] overflow-hidden">
              <button disabled={page === 1} onClick={() => setPage(p => p - 1)} className="px-3 py-2 text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)] border-r border-[var(--aras-border)]"><ChevronLeft size={16} /></button>
              <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)} className="px-3 py-2 text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)]"><ChevronRight size={16} /></button>
            </div>
          </DesignElement>
        )}

      </DesignContainer>

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
              <button onClick={() => setBulkEditOpen(false)} className="flex-1 px-4 py-2 border rounded-xl">Cancel</button>
              <button onClick={handleBulkEditSubmit} disabled={bulkEditing || !bulkEditField} className="flex-1 px-4 py-2 bg-[var(--aras-accent)] text-white rounded-xl">{bulkEditing ? 'Saving...' : 'Apply'}</button>
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

const statusColors: Record<string, string> = {
  draft: 'bg-[var(--aras-muted)]',
  posted: 'bg-emerald-500',
  active: 'bg-emerald-500',
  cancelled: 'bg-rose-500',
}

const renderCellValue = (value: any, type: string, fieldName?: string) => {
  if (value === null || value === undefined) return <span className="text-[var(--aras-muted)]">-</span>
  if (fieldName === 'status' || type === 'boolean') {
    const rawLabel = typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)
    const dotClass = statusColors[String(rawLabel).toLowerCase()] || 'bg-[var(--aras-muted)]'
    return <span className="inline-flex items-center gap-2 text-sm font-bold capitalize"><span className={`h-2 w-2 rounded-full ${dotClass}`} />{rawLabel}</span>
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

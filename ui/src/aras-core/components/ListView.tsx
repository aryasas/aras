import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../../lib/api'
import { cleanResourcePath } from '../../lib/resourceUtils'
import {
  Search, Plus, ChevronLeft, ChevronRight,
  CheckSquare, Square, X,
  ChevronDown, ChevronUp
} from 'lucide-react'
import { FormattingService } from '../services/FormattingService'
import { useAras } from '../hooks/useAras'
import { useUIStore } from '../../store/uiStore'
import { ImportMapping } from './ImportMapping'
import Combobox from './Combobox'
import ListToolbar from './ListToolbar'
import type { ViewMode } from './ListToolbar'
import TreeView from './TreeView'
import GenericReport from './GenericReport'
import { useVocabulary } from '../../context/VocabularyContext'

interface Field {
  name: string
  label: string
  type: string
  required: boolean
  read_only: boolean
  hidden: boolean
  searchable: boolean
  target_resource?: string
  options?: { label: string; value: any }[]
}

interface Metadata {
  resource: string
  title: string
  fields: Field[]
}

interface FilterRule {
  field: string
  op: string
  value: any
}

const ListView = ({ resource, onRowClick, onAdd, fixedFilters }: { 
  resource: string, 
  onRowClick?: (id: string | number) => void,
  onAdd?: () => void,
  fixedFilters?: Record<string, any>
}) => {
  const vocabulary = useVocabulary()
  const [searchParams, setSearchParams] = useSearchParams()
  const [metadata, setMetadata] = useState<Metadata | null>(null)
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { notify, confirm } = useAras()
  
  // Query State
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(20)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState<FilterRule[]>([])
  const [orderBy, setOrderBy] = useState('id')
  const [desc, setDesc] = useState(true)

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

  // Inline editing: { rowId, fieldName, value }
  const [inlineEdit, setInlineEdit] = useState<{ rowId: string | number; field: string; value: any } | null>(null)
  const inlineInputRef = useRef<HTMLInputElement>(null)

  const showPanel = useUIStore(state => state.showPanel)
  const closePanel = useUIStore(state => state.closePanel)
  const roleFilter = searchParams.get('role') || 'all'
  const isPartyResource = useMemo(() => /(^|\/)(parties|party)$/.test(cleanResourcePath(resource)), [resource])

  const hasTreeSupport = useMemo(() => {
    if (!metadata) return false;
    return metadata.fields.some((f: any) => f.name === 'parent_id');
  }, [metadata]);

  // Fetch Metadata & Initial Data
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const cleanResource = cleanResourcePath(resource)
        const res = await api.get(`/metadata/${cleanResource}`)
        setMetadata(res.data)
        setVisibleColumns(res.data.fields.filter((f: Field) => !f.hidden).map((f: Field) => f.name))
      } catch (err: any) {
        notify("Failed to load resource metadata", "error")
      }
    }
    fetchMetadata()
  }, [resource, notify])

  const fetchData = useCallback(async () => {
    if (!metadata) return
    try {
      setLoading(true)
      
      // Merge user filters with fixed filters
      const finalFilters = [...filters]
      if (fixedFilters) {
        Object.entries(fixedFilters).forEach(([field, value]) => {
          finalFilters.push({ field, op: '=', value })
        })
      }
      if (isPartyResource && roleFilter !== 'all') {
        finalFilters.push({ field: 'role', op: '=', value: roleFilter })
      }

      const params = {
        page,
        per_page: perPage,
        search: search || undefined,
        filters: finalFilters.length > 0 ? JSON.stringify(finalFilters) : undefined,
        order_by: orderBy,
        desc
      }
      const dataPath = cleanResourcePath(resource)
      const res = await api.get(`${dataPath}/`, { params })
      setData(res.data.items)
      setTotal(res.data.total)
      setTotalPages(res.data.pages)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to fetch data")
    } finally {
      setLoading(false)
    }
  }, [resource, metadata, page, perPage, search, filters, fixedFilters, orderBy, desc, isPartyResource, roleFilter])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Handlers
  const handleSelectAll = () => {
    if (selectedIds.length === data.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(data.map(item => item.id))
    }
  }

  const handleSelectOne = (id: string | number) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  const handleDeleteBulk = async () => {
    const ok = await confirm({
      title: 'Delete Items',
      message: `Are you sure you want to delete ${selectedIds.length} items? This action cannot be undone.`,
      type: 'danger',
      confirmText: 'Delete Now'
    })
    
    if (ok) {
      try {
        await api.post(`/${cleanResourcePath(resource)}/bulk-delete`, selectedIds)
        setSelectedIds([])
        notify(`Successfully deleted ${selectedIds.length} items`, 'success')
        fetchData()
      } catch (err: any) {
        notify(err.response?.data?.message || "Failed to delete items", 'error')
      }
    }
  }

  const handleBulkEditSubmit = async () => {
    if (!bulkEditField) { notify('Select a field to edit', 'error'); return }
    setBulkEditing(true)
    try {
      const operations = selectedIds.map(id => ({
        action: 'update',
        id,
        data: { [bulkEditField]: bulkEditValue }
      }))
      await api.post(`/${cleanResourcePath(resource)}/batch`, operations)
      notify(`Updated ${selectedIds.length} records`, 'success')
      setBulkEditOpen(false)
      setBulkEditField('')
      setBulkEditValue('')
      setSelectedIds([])
      fetchData()
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Bulk update failed', 'error')
    } finally {
      setBulkEditing(false)
    }
  }

  const handleInlineSave = async () => {
    if (!inlineEdit) return
    try {
      await api.patch(`/${cleanResourcePath(resource)}/${inlineEdit.rowId}`, { [inlineEdit.field]: inlineEdit.value })
      setInlineEdit(null)
      fetchData()
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Save failed', 'error')
    }
  }

  const handleExport = async () => {
    try {
      setIsExporting(true)
      const finalFilters = [...filters]
      if (fixedFilters) {
        Object.entries(fixedFilters).forEach(([field, value]) => {
          finalFilters.push({ field, op: '=', value })
        })
      }
      if (isPartyResource && roleFilter !== 'all') {
        finalFilters.push({ field: 'role', op: '=', value: roleFilter })
      }

      const params = {
        search: search || undefined,
        filters: finalFilters.length > 0 ? JSON.stringify(finalFilters) : undefined,
        order_by: orderBy,
        desc
      }
      const cleanResource = cleanResourcePath(resource)
      const res = await api.get(`/${cleanResource}/export`, { 
        params, 
        responseType: 'blob' 
      })
      
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${cleanResource}_export_${new Date().toISOString().split('T')[0]}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      notify("Data exported successfully", "success")
    } catch (err: any) {
      notify("Failed to export data", "error")
    } finally {
      setIsExporting(false)
    }
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // 1. Parse CSV Headers
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      const firstLine = text.split('\n')[0];
      const headers = firstLine.split(',').map(h => h.trim().replace(/^"|"$/g, ''));
      
      // 2. Show Mapping Panel
      showPanel(
        `Import Mapping: ${metadata?.title}`,
        <ImportMapping 
          csvHeaders={headers}
          resourceFields={metadata?.fields.filter(f => !f.read_only).map(f => ({ name: f.name, label: f.label })) || []}
          onCancel={closePanel}
          onConfirm={async (mapping) => {
            closePanel();
            await executeImport(file, mapping);
          }}
        />,
        'max-w-2xl'
      );
    };
    reader.readAsText(file);
    
    // Reset input so same file can be selected again
    e.target.value = '';
  }

  const executeImport = async (file: File, mapping: Record<string, string>) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      setLoading(true)
      const cleanResource = cleanResourcePath(resource)
      await api.post(`/${cleanResource}/import`, formData, {
        params: { mapping: JSON.stringify(mapping) },
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      notify('Data import initiated in background', 'success')
      fetchData()
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Import failed'
      notify(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  const addFilter = () => {
    if (!metadata) return
    const firstField = metadata.fields[0].name
    setFilters([...filters, { field: firstField, op: '=', value: '' }])
  }

  const removeFilter = (index: number) => {
    setFilters(filters.filter((_, i) => i !== index))
  }

  const updateFilter = (index: number, key: keyof FilterRule, value: any) => {
    const newFilters = [...filters]
    newFilters[index] = { ...newFilters[index], [key]: value }
    setFilters(newFilters)
  }

  if (error) return <div className="p-8 text-red-500 bg-red-50 rounded-xl border border-red-100">{error}</div>
  if (!metadata) return <div className="p-8 animate-pulse text-slate-400">Initializing {resource}...</div>

  const fields = metadata.fields
  const visibleFields = fields.filter(f => visibleColumns.includes(f.name))
  const toolbarFields = fields.map(field => ({ ...field, label: vocabulary.get(field.label) }))
  const title = vocabulary.get(metadata.title)
  const roleTabs = [
    { value: 'all', label: 'All' },
    { value: 'customer', label: 'Customer' },
    { value: 'supplier', label: 'Supplier' },
    { value: 'member', label: 'Member' },
    { value: 'student', label: 'Student' },
    { value: 'patient', label: 'Patient' },
    { value: 'donor', label: 'Donor' },
    { value: 'citizen', label: 'Citizen' },
    { value: 'other', label: 'Other' },
  ]

  const setRoleFilter = (role: string) => {
    const next = new URLSearchParams(searchParams)
    if (role === 'all') next.delete('role')
    else next.set('role', role)
    setSearchParams(next, { replace: true })
    setPage(1)
  }

  return (
    <>
    <div className="flex flex-col h-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* ── Toolbar ────────────────────────────────────────────────────────── */}
      <ListToolbar 
        title={title}
        search={search}
        onSearchChange={setSearch}
        isFilterOpen={isFilterOpen}
        onFilterToggle={() => setIsFilterOpen(!isFilterOpen)}
        filterCount={filters.length}
        selectedCount={selectedIds.length}
        onBulkEdit={() => setBulkEditOpen(true)}
        onBulkDelete={handleDeleteBulk}
        onExport={handleExport}
        isExporting={isExporting}
        onImport={handleImport}
        onColumnPickerToggle={() => setIsColumnPickerOpen(!isColumnPickerOpen)}
        isColumnPickerOpen={isColumnPickerOpen}
        onAdd={() => onAdd ? onAdd() : null}
        fields={toolbarFields}
        visibleColumns={visibleColumns}
        onVisibleColumnsChange={setVisibleColumns}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        hasTreeSupport={hasTreeSupport}
      />

        {/* ── Advanced Filter Builder ────────────────────────────────────── */}
        {isFilterOpen && (
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase">Filter Conditions</span>
              <button onClick={addFilter} className="text-xs font-bold text-indigo-600 hover:underline flex items-center gap-1">
                <Plus size={14} /> Add Rule
              </button>
            </div>
            {filters.length === 0 ? (
              <p className="text-sm text-slate-400 italic">No filters applied. Add a rule to refine results.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {filters.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 bg-white p-2 rounded-xl border border-slate-200">
                    <div className="flex-1">
                      <Combobox
                        options={fields.map(field => ({ label: vocabulary.get(field.label), value: field.name }))}
                        value={f.field}
                        onChange={(val) => updateFilter(i, 'field', val)}
                        placeholder="Field..."
                      />
                    </div>
                    <select 
                      value={f.op} 
                      onChange={(e) => updateFilter(i, 'op', e.target.value)}
                      className="text-xs bg-indigo-50 text-indigo-700 rounded-lg p-2 outline-none font-bold h-[42px]"
                    >
                      <option value="=">=</option>
                      <option value="!=">!=</option>
                      <option value=">">&gt;</option>
                      <option value="<">&lt;</option>
                      <option value="ilike">contains</option>
                    </select>
                    <div className="flex-1">
                      {(() => {
                        const field = fields.find(fd => fd.name === f.field)
                        if (field?.type === 'lookup' && field.target_resource) {
                          return (
                            <Combobox 
                              resource={field.target_resource}
                              value={f.value}
                              onChange={(val) => updateFilter(i, 'value', val)}
                              placeholder="Value..."
                            />
                          )
                        }
                        if (field?.type === 'select' && field.options) {
                          return (
                            <Combobox 
                              options={field.options}
                              value={f.value}
                              onChange={(val) => updateFilter(i, 'value', val)}
                              placeholder="Value..."
                            />
                          )
                        }
                        return (
                          <input 
                            type="text" 
                            value={f.value}
                            placeholder="Value..."
                            onChange={(e) => updateFilter(i, 'value', e.target.value)}
                            className="w-full px-3 py-2.5 bg-slate-50 border border-slate-100 rounded-xl text-xs outline-none focus:ring-1 focus:ring-indigo-400"
                          />
                        )
                      })()}
                    </div>
                    <button onClick={() => removeFilter(i)} className="p-2 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-colors">
                      <X size={14} />
                    </button>
                  </div>

                ))}
              </div>
            )}
            <div className="flex justify-end pt-2">
               <button 
                 onClick={() => { setFilters([]); setPage(1); }}
                 className="text-xs font-bold text-slate-500 hover:text-slate-700 mr-4"
               >
                 Reset All
               </button>
               <button 
                 onClick={() => { setPage(1); fetchData(); }}
                 className="px-4 py-1.5 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700"
               >
                 Apply Filters
               </button>
            </div>
          </div>
        )}

      {/* ── Content View ─────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-auto">
        {isPartyResource && (
          <div className="flex flex-wrap gap-2 border-b border-slate-100 bg-white px-6 py-3">
            {roleTabs.map(tab => (
              <button
                key={tab.value}
                type="button"
                onClick={() => setRoleFilter(tab.value)}
                className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
                  roleFilter === tab.value
                    ? 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-100'
                    : 'bg-slate-50 text-slate-500 hover:bg-slate-100 hover:text-slate-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        )}
        {viewMode === 'list' && (
          <table className="w-full text-left border-collapse min-w-[800px]">
            <thead className="sticky top-0 z-10">
              <tr className="bg-slate-50/80 backdrop-blur-sm border-b border-slate-200">
                <th className="px-6 py-4 w-10">
                  <button onClick={handleSelectAll} className="text-slate-400 hover:text-indigo-600">
                    {selectedIds.length === data.length && data.length > 0 ? <CheckSquare size={18} className="text-indigo-600" /> : <Square size={18} />}
                  </button>
                </th>
                {visibleFields.map(field => (
                  <th 
                    key={field.name} 
                    className="px-8 py-5 text-xs font-bold text-slate-600 uppercase tracking-wider cursor-pointer hover:bg-slate-50 transition-colors"

                    onClick={() => {
                      if (orderBy === field.name) setDesc(!desc)
                      else { setOrderBy(field.name); setDesc(true); }
                    }}
                  >
                    <div className="flex items-center gap-2">
                      {vocabulary.get(field.label)}
                      {orderBy === field.name && (desc ? <ChevronDown size={14} /> : <ChevronUp size={14} />)}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-6 py-4"><div className="w-5 h-5 bg-slate-100 rounded"></div></td>
                    {visibleFields.map(f => <td key={f.name} className="px-6 py-4"><div className="h-4 bg-slate-50 rounded w-3/4"></div></td>)}
                  </tr>
                ))
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={visibleFields.length + 1} className="px-6 py-12 text-center">
                    <div className="max-w-xs mx-auto text-slate-400">
                      <Search size={48} className="mx-auto mb-4 opacity-20" />
                      <p className="text-sm font-medium">No records found matching your criteria.</p>
                      <button onClick={() => {setSearch(''); setFilters([]);}} className="mt-2 text-xs text-indigo-600 font-bold hover:underline">Clear all filters</button>
                    </div>
                  </td>
                </tr>
              ) : (
                data.map((item) => (
                  <tr 
                    key={item.id} 
                    className={`hover:bg-indigo-50/30 transition-colors cursor-pointer group ${selectedIds.includes(item.id) ? 'bg-indigo-50/50' : ''}`}
                    onClick={() => onRowClick ? onRowClick(item.id) : null}
                  >
                    <td className="px-6 py-4" onClick={(e) => e.stopPropagation()}>
                      <button onClick={() => handleSelectOne(item.id)} className={`${selectedIds.includes(item.id) ? 'text-indigo-600' : 'text-slate-300 group-hover:text-slate-400'}`}>
                        {selectedIds.includes(item.id) ? <CheckSquare size={18} /> : <Square size={18} />}
                      </button>
                    </td>
                    {visibleFields.map(field => {
                      const isInline = inlineEdit?.rowId === item.id && inlineEdit?.field === field.name
                      const inlineTypes = ['text', 'string', 'number', 'integer', 'email', 'url']
                    const canInline = !field.read_only && inlineTypes.includes(field.type)
                    return (
                      <td
                        key={field.name}
                        className="px-6 py-4 text-sm text-slate-600 font-medium"
                        onDoubleClick={(e) => {
                          if (!canInline) return
                          e.stopPropagation()
                          setInlineEdit({ rowId: item.id, field: field.name, value: item[field.name] ?? '' })
                          setTimeout(() => inlineInputRef.current?.select(), 30)
                        }}
                      >
                        {isInline ? (
                          <input
                            ref={inlineInputRef}
                            type={field.type === 'number' || field.type === 'integer' ? 'number' : 'text'}
                            className="w-full border-b-2 border-indigo-400 bg-indigo-50 rounded px-1 py-0.5 text-sm outline-none"
                            value={inlineEdit.value}
                            onChange={e => setInlineEdit(prev => prev ? { ...prev, value: e.target.value } : prev)}
                            onBlur={handleInlineSave}
                            onKeyDown={e => { if (e.key === 'Enter') handleInlineSave(); if (e.key === 'Escape') setInlineEdit(null); }}
                            onClick={e => e.stopPropagation()}
                          />
                        ) : (
                          <span title={canInline ? 'Double-click to edit' : undefined} className={canInline ? 'cursor-text' : ''}>
                            {renderCellValue(item[`${field.name}_label`] ?? item[field.name], field.type, field.name)}
                          </span>
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
        )}

        {viewMode === 'tree' && (
          <TreeView resource={resource} onRowClick={onRowClick} />
        )}

        {viewMode === 'report' && metadata && (
          <GenericReport
            title={`${title} Report`}
            data={data}
            columns={visibleFields.map(f => ({ field: f.name, label: vocabulary.get(f.label), type: f.type }))}
            onBack={() => setViewMode('list')}
          />
        )}
      </div>

      {/* ── Footer / Pagination ────────────────────────────────────────────── */}
      {viewMode === 'list' && (
      <div className="p-4 bg-slate-50/50 border-t border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-xs font-medium text-slate-500">
            Showing <span className="text-slate-900 font-bold">{(page-1)*perPage + 1}</span> to <span className="text-slate-900 font-bold">{Math.min(page*perPage, total)}</span> of <span className="text-slate-900 font-bold">{total}</span>
          </span>
          <select 
            className="text-xs bg-white border border-slate-200 rounded-lg p-1 outline-none focus:ring-1 focus:ring-indigo-500"
            value={perPage}
            onChange={(e) => { setPerPage(Number(e.target.value)); setPage(1); }}
          >
            <option value={10}>10 per page</option>
            <option value={20}>20 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
            <option value={999999}>All</option>
          </select>
        </div>

        <div className="flex items-center gap-1">
          <button 
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className="p-2 text-slate-500 hover:bg-white border border-transparent hover:border-slate-200 rounded-xl disabled:opacity-30 disabled:hover:bg-transparent"
          >
            <ChevronLeft size={18} />
          </button>
          
          <div className="flex items-center gap-1">
            {[...Array(Math.min(5, totalPages))].map((_, i) => {
              let p = page <= 3 ? i + 1 : page + i - 2
              if (p > totalPages) return null
              return (
                <button 
                  key={p}
                  onClick={() => setPage(p)}
                  className={`w-9 h-9 flex items-center justify-center text-xs font-bold rounded-xl transition-all ${page === p ? 'bg-indigo-600 text-white shadow-md shadow-indigo-100' : 'text-slate-600 hover:bg-white hover:border-slate-200 border border-transparent'}`}
                >
                  {p}
                </button>
              )
            })}
          </div>

          <button 
            disabled={page === totalPages}
            onClick={() => setPage(p => p + 1)}
            className="p-2 text-slate-500 hover:bg-white border border-transparent hover:border-slate-200 rounded-xl disabled:opacity-30 disabled:hover:bg-transparent"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>
      )}
    </div>

    {/* Bulk Edit Modal */}
    {bulkEditOpen && (
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md p-6 space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-extrabold text-slate-900">Bulk Edit — {selectedIds.length} rows</h3>
            <button onClick={() => setBulkEditOpen(false)} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-500 transition-all">
              <X size={18} />
            </button>
          </div>
          <p className="text-sm text-slate-500">Choose a field and set a new value for all selected rows.</p>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-bold text-slate-600 mb-1 block">Field</label>
              <select
                className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                value={bulkEditField}
                onChange={e => {
                  setBulkEditField(e.target.value)
                  setBulkEditValue('')
                }}
              >
                <option value="">— Select field —</option>
                {(metadata?.fields ?? []).filter(f => !f.read_only && !f.hidden && !['id','created_at','updated_at','created_by','updated_by'].includes(f.name)).map(f => (
                  <option key={f.name} value={f.name}>{vocabulary.get(f.label)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-bold text-slate-600 mb-1 block">New Value</label>
              {(() => {
                const field = metadata?.fields.find(f => f.name === bulkEditField)
                if (field?.type === 'lookup' && field.target_resource) {
                  return (
                    <Combobox
                      resource={field.target_resource}
                      value={bulkEditValue}
                      onChange={setBulkEditValue}
                      placeholder={`Select ${vocabulary.get(field.label)}...`}
                    />
                  )
                }
                if (field?.type === 'select' && field.options) {
                  return (
                    <Combobox
                      options={field.options}
                      value={bulkEditValue}
                      onChange={setBulkEditValue}
                      placeholder={`Select ${vocabulary.get(field.label)}...`}
                    />
                  )
                }

                if (field?.type === 'boolean') {
                  return (
                    <select
                      className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={bulkEditValue}
                      onChange={e => setBulkEditValue(e.target.value === 'true')}
                    >
                      <option value="">— Select —</option>
                      <option value="true">True / Active</option>
                      <option value="false">False / Inactive</option>
                    </select>
                  )
                }
                if (field?.type === 'date' || field?.type === 'datetime') {
                  return (
                    <input
                      type={field.type === 'date' ? 'date' : 'datetime-local'}
                      className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={bulkEditValue}
                      onChange={e => setBulkEditValue(e.target.value)}
                    />
                  )
                }
                return (
                  <input
                    type={field?.type === 'number' ? 'number' : 'text'}
                    className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                    value={bulkEditValue}
                    onChange={e => setBulkEditValue(e.target.value)}
                    placeholder="Enter new value..."
                  />
                )
              })()}
            </div>
          </div>
          <div className="flex gap-3 pt-1">
            <button onClick={() => setBulkEditOpen(false)} className="flex-1 px-4 py-2 border border-slate-200 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-50 transition-all">
              Cancel
            </button>
            <button
              onClick={handleBulkEditSubmit}
              disabled={bulkEditing || !bulkEditField}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-bold hover:bg-indigo-700 disabled:opacity-50 transition-all"
            >
              {bulkEditing ? 'Saving…' : 'Apply'}
            </button>
          </div>
        </div>
      </div>
    )}
    </>
  )
}

const roleColors: Record<string, string> = {
  customer: 'bg-sky-50 text-sky-700 border-sky-100',
  supplier: 'bg-amber-50 text-amber-700 border-amber-100',
  member: 'bg-violet-50 text-violet-700 border-violet-100',
  student: 'bg-emerald-50 text-emerald-700 border-emerald-100',
  patient: 'bg-rose-50 text-rose-700 border-rose-100',
  donor: 'bg-fuchsia-50 text-fuchsia-700 border-fuchsia-100',
  citizen: 'bg-cyan-50 text-cyan-700 border-cyan-100',
  other: 'bg-slate-50 text-slate-600 border-slate-100',
}

const renderCellValue = (value: any, type: string, fieldName?: string) => {
  if (value === null || value === undefined) return <span className="text-slate-300">-</span>
  if (fieldName === 'role') {
    const role = String(value)
    const roleLabel = role.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
    return (
      <span className={`inline-flex rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${roleColors[role] || roleColors.other}`}>
        {roleLabel}
      </span>
    )
  }
  
  switch (type) {
    case 'currency':
      return <span className="text-slate-900 font-bold">{FormattingService.formatCurrency(value)}</span>
    case 'number':
      return <span className="text-slate-900">{FormattingService.formatNumber(value)}</span>
    case 'boolean':
      return value ? <span className="px-2 py-0.5 bg-green-50 text-green-600 text-[10px] font-bold rounded uppercase">Active</span> : <span className="px-2 py-0.5 bg-slate-50 text-slate-400 text-[10px] font-bold rounded uppercase">Inactive</span>
    case 'date':
    case 'datetime':
      return FormattingService.formatDate(value)
    case 'email':
      return <span className="text-indigo-600 underline">{value}</span>
    default:
      if (typeof value === 'object') return <span className="text-[10px] font-mono text-slate-400 truncate block max-w-[200px]">{JSON.stringify(value)}</span>
      return String(value)
  }
}

export default ListView

import { useState, useEffect, useCallback } from 'react'
import api from '../../lib/api'
import { 
  Search, Filter, Plus, ChevronLeft, ChevronRight, 
  Settings, Trash2, CheckSquare, Square, X, 
  ChevronDown, ChevronUp, Download
} from 'lucide-react'
import { useUIStore } from '../../store/uiStore'
import { FormattingService } from '../services/FormattingService'

interface Field {
  name: string
  label: string
  type: string
  required: boolean
  read_only: boolean
  hidden: boolean
  searchable: boolean
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
  onRowClick?: (id: number) => void,
  onAdd?: () => void,
  fixedFilters?: Record<string, any>
}) => {
  const [metadata, setMetadata] = useState<Metadata | null>(null)
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const showConfirm = useUIStore((state) => state.showConfirm);
  const showError = useUIStore((state) => state.showError);
  const showAlert = useUIStore((state) => state.showAlert);
  
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
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [visibleColumns, setVisibleColumns] = useState<string[]>([])
  const [isColumnPickerOpen, setIsColumnPickerOpen] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  // Fetch Metadata & Initial Data
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const cleanResource = resource.startsWith('/') ? resource.substring(1) : resource
        const res = await api.get(`/metadata/${cleanResource}`)
        setMetadata(res.data)
        setVisibleColumns(res.data.fields.filter((f: Field) => !f.hidden).map((f: Field) => f.name))
      } catch (err: any) {
        showError("Metadata Error", "Failed to load resource metadata")
      }
    }
    fetchMetadata()
  }, [resource])

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

      const params = {
        page,
        per_page: perPage,
        search: search || undefined,
        filters: finalFilters.length > 0 ? JSON.stringify(finalFilters) : undefined,
        order_by: orderBy,
        desc
      }
      const dataPath = resource.startsWith('/') ? resource.substring(1) : resource
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
  }, [resource, metadata, page, perPage, search, filters, fixedFilters, orderBy, desc])

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

  const handleSelectOne = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  const handleDeleteBulk = async () => {
    showConfirm(
      'Delete Items', 
      `Are you sure you want to delete ${selectedIds.length} items?`,
      async () => {
        try {
          await api.post(`/${resource}/bulk-delete`, selectedIds)
          setSelectedIds([])
          fetchData()
        } catch (err: any) {
          showError("Delete Error", err.response?.data?.message || "Failed to delete items")
        }
      }
    )
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

      const params = {
        search: search || undefined,
        filters: finalFilters.length > 0 ? JSON.stringify(finalFilters) : undefined,
        order_by: orderBy,
        desc
      }
      const cleanResource = resource.startsWith('/') ? resource.substring(1) : resource
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

  return (
    <div className="flex flex-col h-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* ── Toolbar ────────────────────────────────────────────────────────── */}
      <div className="p-4 border-b border-slate-100 space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-1">
            <h2 className="text-xl font-bold text-slate-900 hidden md:block">{metadata.title}</h2>
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="text" 
                placeholder={`Search in ${metadata.title}...`}
                className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button 
              onClick={() => setIsFilterOpen(!isFilterOpen)}
              className={`p-2 rounded-xl border transition-all flex items-center gap-2 text-sm font-medium ${isFilterOpen ? 'bg-indigo-50 border-indigo-200 text-indigo-600' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'}`}
            >
              <Filter size={18} />
              <span>Filters {filters.length > 0 && `(${filters.length})`}</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            {selectedIds.length > 0 && (
              <button 
                onClick={handleDeleteBulk}
                className="flex items-center gap-2 px-4 py-2 bg-rose-50 text-rose-600 rounded-xl text-sm font-bold hover:bg-rose-100 transition-all"
              >
                <Trash2 size={18} />
                <span>Delete ({selectedIds.length})</span>
              </button>
            )}

            <button 
              onClick={handleExport}
              disabled={isExporting}
              className="p-2 border border-slate-200 rounded-xl text-slate-600 hover:bg-slate-50 disabled:opacity-50"
              title="Export to CSV"
            >
              <Download size={18} className={isExporting ? 'animate-bounce' : ''} />
            </button>
            
            <button 
              className="p-2 border border-slate-200 rounded-xl text-slate-600 hover:bg-slate-50 relative"
              onClick={() => setIsColumnPickerOpen(!isColumnPickerOpen)}
            >
              <Settings size={18} />
              {isColumnPickerOpen && (
                <div 
                  className="absolute right-0 mt-3 w-64 bg-white border border-slate-200 shadow-xl rounded-2xl z-50 p-4"
                  onClick={(e) => e.stopPropagation()}
                >
                  <h4 className="text-xs font-bold text-slate-400 uppercase mb-3">Visible Columns</h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {fields.map(f => (
                      <label key={f.name} className="flex items-center gap-2 cursor-pointer hover:bg-slate-50 p-1 rounded-lg">
                        <input 
                          type="checkbox" 
                          checked={visibleColumns.includes(f.name)} 
                          onChange={(e) => {
                            const checked = e.target.checked;
                            setVisibleColumns(prev => 
                              checked ? [...prev, f.name] : prev.filter(c => c !== f.name)
                            )
                          }}
                          className="rounded text-indigo-600 focus:ring-indigo-500"
                        />
                        <span className="text-sm text-slate-700">{f.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </button>

            <button 
              onClick={() => onAdd ? onAdd() : null}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-bold hover:bg-indigo-700 transition-all shadow-md shadow-indigo-100"
            >
              <Plus size={18} />
              <span className="hidden sm:inline">Add New</span>
            </button>
          </div>
        </div>

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
                    <select 
                      value={f.field} 
                      onChange={(e) => updateFilter(i, 'field', e.target.value)}
                      className="text-xs bg-transparent outline-none font-medium text-slate-700 flex-1"
                    >
                      {fields.map(field => <option key={field.name} value={field.name}>{field.label}</option>)}
                    </select>
                    <select 
                      value={f.op} 
                      onChange={(e) => updateFilter(i, 'op', e.target.value)}
                      className="text-xs bg-indigo-50 text-indigo-700 rounded px-1 outline-none font-bold"
                    >
                      <option value="=">=</option>
                      <option value="!=">!=</option>
                      <option value=">">&gt;</option>
                      <option value="<">&lt;</option>
                      <option value="ilike">contains</option>
                    </select>
                    <input 
                      type="text" 
                      value={f.value}
                      placeholder="Value..."
                      onChange={(e) => updateFilter(i, 'value', e.target.value)}
                      className="text-xs bg-transparent outline-none flex-1 border-b border-slate-100 focus:border-indigo-400"
                    />
                    <button onClick={() => removeFilter(i)} className="text-slate-400 hover:text-rose-500">
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
      </div>

      {/* ── Table ──────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-auto">
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
                  className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100 transition-colors"
                  onClick={() => {
                    if (orderBy === field.name) setDesc(!desc)
                    else { setOrderBy(field.name); setDesc(true); }
                  }}
                >
                  <div className="flex items-center gap-2">
                    {field.label}
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
                  {visibleFields.map(field => (
                    <td key={field.name} className="px-6 py-4 text-sm text-slate-600 font-medium">
                       {renderCellValue(item[`${field.name}_label`] ?? item[field.name], field.type)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ── Footer / Pagination ────────────────────────────────────────────── */}
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
    </div>
  )
}

const renderCellValue = (value: any, type: string) => {
  if (value === null || value === undefined) return <span className="text-slate-300">-</span>
  
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
(value)}</span>
      return String(value)
  }
}

export default ListView
ate block max-w-[200px]">{JSON.stringify(value)}</span>
      return String(value)
  }
}

export default ListView
late-400 truncate block max-w-[200px]">{JSON.stringify(value)}</span>
      return String(value)
  }
}

export default ListView
an>
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

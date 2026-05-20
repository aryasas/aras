import { useCallback, useState, useEffect } from 'react'
import api from '../lib/api'
import { FileText, Play, Search, Loader2, ChevronLeft } from 'lucide-react'
import GenericReport from '../aras-core/components/GenericReport'
import { useAras } from '../aras-core/hooks/useAras'
import { useUIStore } from '../store/uiStore'

interface Report {
  id: number
  name: string
  code: string
  module: string
  report_type: string
  linked_doctype?: string
  filters_json?: ReportFilter[] | string | null
}

interface ReportResult {
  title: string
  data: Record<string, unknown>[]
  columns: { field: string; label: string; type?: string }[]
}

type FilterValue = string | number

interface ReportFilter {
  field: string
  label?: string
  type?: string
  default?: FilterValue | null
  options?: Array<[FilterValue, string] | { label: string; value: FilterValue }>
}

const getErrorDetail = (err: unknown, fallback: string) => (
  (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || fallback
)

export default function ReportCenter() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const setPageTitle = useUIStore(state => state.setPageTitle)

  useEffect(() => {
    setPageTitle('Report Center', 'Browse and execute system reports across all modules.', 'ANALYTICS')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  const [search, setSearch] = useState('')
  const [activeModule, setActiveModule] = useState<string | null>(null)
  const [runningReport, setRunningReport] = useState<number | null>(null)
  const [reportResult, setReportResult] = useState<ReportResult | null>(null)
  const [activeReport, setActiveReport] = useState<Report | null>(null)
  const [reportFilters, setReportFilters] = useState<ReportFilter[]>([])
  const [reportParams, setReportParams] = useState<Record<string, FilterValue>>({})
  const { notify } = useAras()

  const fetchReports = useCallback(async () => {
    try {
      setLoading(true)
      const res = await api.get('erp/report/reports')
      setReports(res.data.items)
    } catch {
      notify("Failed to load reports", "error")
    } finally {
      setLoading(false)
    }
  }, [notify])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      fetchReports()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [fetchReports])

  const parseFilters = (filters: Report['filters_json']): ReportFilter[] => {
    if (!filters) return []
    if (Array.isArray(filters)) return filters
    if (typeof filters === 'string') {
      try {
        const parsed = JSON.parse(filters)
        return Array.isArray(parsed) ? parsed : []
      } catch {
        return []
      }
    }
    return []
  }

  const defaultParamsFor = (filters: ReportFilter[]) => (
    filters.reduce<Record<string, FilterValue>>((acc, filter) => {
      acc[filter.field] = filter.default ?? ''
      return acc
    }, {})
  )

  const loadReportForRun = async (report: Report) => {
    try {
      const detailRes = await api.get(`erp/report/reports/${report.id}`)
      const reportDetail = { ...report, ...detailRes.data }
      const filters = parseFilters(reportDetail.filters_json)

      if (filters.length === 0) {
        await runReport(reportDetail, {})
        return
      }

      setActiveReport(reportDetail)
      setReportFilters(filters)
      setReportParams(defaultParamsFor(filters))
    } catch (err) {
      notify(getErrorDetail(err, "Failed to load report filters"), "error")
    }
  }

  const runReport = async (report: Report, params = reportParams) => {
    try {
      setRunningReport(report.id)
      const res = await api.post(`erp/report/reports/${report.id}/action/generate_report`, { params })

      const reportData = res.data.result
      if (!reportData || reportData.error) {
        notify(reportData?.error || "Failed to generate report", "error")
        return
      }

      setReportResult(reportData)
    } catch (err) {
      notify(getErrorDetail(err, "Failed to generate report"), "error")
    } finally {
      setRunningReport(null)
    }
  }

  const modules = Array.from(new Set(reports.map(r => r.module))).sort()
  
  const filteredReports = reports.filter(r => {
    const matchesSearch = r.name.toLowerCase().includes(search.toLowerCase()) || 
                          r.code.toLowerCase().includes(search.toLowerCase())
    const matchesModule = !activeModule || r.module === activeModule
    return matchesSearch && matchesModule
  })

  const renderFilterInput = (filter: ReportFilter) => {
    const value = reportParams[filter.field] ?? ''
    const label = filter.label || filter.field.replace(/_/g, ' ')
    const baseClass = "w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-700 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"

    if (filter.type === 'select') {
      return (
        <label key={filter.field} className="space-y-1.5">
          <span className="block text-xs font-black text-slate-400 uppercase tracking-wider">{label}</span>
          <select
            className={baseClass}
            value={value}
            onChange={(e) => setReportParams(prev => ({ ...prev, [filter.field]: e.target.value }))}
          >
            {(filter.options || []).map((option) => {
              const optionValue = Array.isArray(option) ? option[0] : option.value
              const optionLabel = Array.isArray(option) ? option[1] : option.label
              return <option key={`${filter.field}-${optionValue}`} value={optionValue}>{optionLabel}</option>
            })}
          </select>
        </label>
      )
    }

    return (
      <label key={filter.field} className="space-y-1.5">
        <span className="block text-xs font-black text-slate-400 uppercase tracking-wider">{label}</span>
        <input
          type={filter.type === 'date' ? 'date' : 'text'}
          className={baseClass}
          value={value}
          onChange={(e) => setReportParams(prev => ({ ...prev, [filter.field]: e.target.value }))}
        />
      </label>
    )
  }

  if (reportResult) {
    return (
      <div className="space-y-4 animate-in fade-in duration-300">
        <button 
          onClick={() => setReportResult(null)}
          className="flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-indigo-600 transition-colors"
        >
          <ChevronLeft size={18} />
          Back to Report Center
        </button>
        <GenericReport 
          title={reportResult.title}
          data={reportResult.data}
          columns={reportResult.columns}
          onBack={() => setReportResult(null)}
        />
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="flex flex-col md:flex-row md:items-center justify-end gap-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text"
              placeholder="Search reports..."
              className="pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all w-64"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Module Filter */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
        <button
          onClick={() => setActiveModule(null)}
          className={`px-4 py-2 rounded-xl text-sm font-bold transition-all whitespace-nowrap ${
            activeModule === null 
              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200' 
              : 'bg-white text-slate-600 border border-slate-200 hover:border-indigo-200 hover:text-indigo-600'
          }`}
        >
          All Modules
        </button>
        {modules.map(mod => (
          <button
            key={mod}
            onClick={() => setActiveModule(mod)}
            className={`px-4 py-2 rounded-xl text-sm font-bold transition-all whitespace-nowrap ${
              activeModule === mod 
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200' 
                : 'bg-white text-slate-600 border border-slate-200 hover:border-indigo-200 hover:text-indigo-600'
            }`}
          >
            {mod}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
          <Loader2 className="animate-spin mb-4" size={40} />
          <p className="text-sm font-medium">Loading report catalog...</p>
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="p-20 text-center bg-white rounded-3xl border border-dashed border-slate-200">
          <FileText size={48} className="mx-auto mb-4 text-slate-200" />
          <h3 className="text-lg font-bold text-slate-900">No reports found</h3>
          <p className="text-slate-500 max-w-xs mx-auto mt-1">Try adjusting your search or module filter to find what you're looking for.</p>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredReports.map(report => (
            <div 
              key={report.id}
              className="group relative bg-white border border-slate-200 rounded-2xl p-6 shadow-sm transition-all hover:shadow-xl hover:border-indigo-200 flex flex-col h-full"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-xl bg-slate-50 text-slate-500 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                  <FileText size={24} />
                </div>
                <span className="text-[10px] font-black uppercase tracking-widest px-2 py-1 bg-slate-100 text-slate-500 rounded-lg">
                  {report.report_type}
                </span>
              </div>
              
              <div className="flex-1">
                <h3 className="text-lg font-extrabold text-slate-900 group-hover:text-indigo-600 transition-colors mb-1">
                  {report.name}
                </h3>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-tight">
                  {report.module} • {report.linked_doctype || 'Custom'}
                </p>
              </div>

              <div className="mt-6 pt-6 border-t border-slate-50">
                {activeReport?.id === report.id && reportFilters.length > 0 && (
                  <div className="mb-5 w-full space-y-4">
                    <div className="grid gap-3">
                      {reportFilters.map(renderFilterInput)}
                    </div>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <button
                    disabled={runningReport !== null}
                    onClick={() => activeReport?.id === report.id ? runReport(report) : loadReportForRun(report)}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white text-sm font-bold rounded-xl transition-all shadow-md shadow-indigo-100"
                  >
                    {runningReport === report.id ? (
                      <Loader2 className="animate-spin" size={16} />
                    ) : (
                      <Play size={16} fill="currentColor" />
                    )}
                    {runningReport === report.id ? 'Generating...' : 'Generate'}
                  </button>

                  <span className="text-[10px] font-bold text-slate-400">
                    ID: {report.code}
                  </span>
                </div>
              </div>
              {runningReport === report.id && (
                <div className="absolute inset-0 bg-white/80 backdrop-blur-sm rounded-2xl p-6 animate-pulse">
                  <div className="h-6 w-32 bg-slate-200 rounded mb-4" />
                  <div className="space-y-3">
                    <div className="h-4 w-full bg-slate-100 rounded" />
                    <div className="h-4 w-5/6 bg-slate-100 rounded" />
                    <div className="h-10 w-full bg-slate-100 rounded-xl mt-6" />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

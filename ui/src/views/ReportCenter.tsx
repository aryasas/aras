import { useCallback, useState, useEffect } from 'react'
import api from '../lib/api'
import { FileText, Play, Search, Loader2 } from 'lucide-react'
import GenericReport from '../aras-core/components/GenericReport'
import { useAras } from '../aras-core/hooks/useAras'
import { useUIStore } from '../store/uiStore'
import Combobox from '../aras-core/components/Combobox'

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

  const [search, setSearch] = useState('')
  const [activeModule, setActiveModule] = useState<string | null>(null)
  const [runningReport, setRunningReport] = useState<number | null>(null)
  const [reportResult, setReportResult] = useState<ReportResult | null>(null)
  const [activeReport, setActiveReport] = useState<Report | null>(null)
  const [reportFilters, setReportFilters] = useState<ReportFilter[]>([])
  const [reportParams, setReportParams] = useState<Record<string, FilterValue>>({})
  const { notify } = useAras()

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

  const runReport = useCallback(async (report: Report, params: Record<string, FilterValue>) => {
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
  }, [notify])

  const handleSelectReport = useCallback(async (report: Report) => {
    setReportResult(null)
    setActiveReport(report)
    
    try {
      const detailRes = await api.get(`erp/report/reports/${report.id}`)
      const reportDetail = { ...report, ...detailRes.data }
      const filters = parseFilters(reportDetail.filters_json)
      
      setReportFilters(filters)
      const params = defaultParamsFor(filters)
      setReportParams(params)

      // If no filters, auto-run
      if (filters.length === 0) {
        await runReport(reportDetail, params)
      }
    } catch (err) {
      notify(getErrorDetail(err, "Failed to load report filters"), "error")
    }
  }, [notify, runReport])

  const fetchReports = useCallback(async () => {
    try {
      setLoading(true)
      const res = await api.get('erp/report/reports')
      const items = res.data?.items || []
      setReports(items)
      
      // Auto-select first report if none active
      if (items.length > 0) {
        handleSelectReport(items[0])
      }
    } catch {
      notify("Failed to load reports", "error")
    } finally {
      setLoading(false)
    }
  }, [notify, handleSelectReport])

  useEffect(() => {
    setPageTitle('Report Center', 'Browse and execute system reports across all modules.', 'ANALYTICS')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  useEffect(() => {
    fetchReports()
  }, [fetchReports])

  const modules = Array.from(new Set((reports || []).map(r => r.module))).sort()
  
  const filteredReports = (reports || []).filter(r => {
    const matchesSearch = (r.name || '').toLowerCase().includes(search.toLowerCase()) || 
                          (r.code || '').toLowerCase().includes(search.toLowerCase())
    const matchesModule = !activeModule || r.module === activeModule
    return matchesSearch && matchesModule
  })

  const renderFilterInput = (filter: ReportFilter) => {
    const value = reportParams[filter.field] ?? ''
    const label = filter.label || filter.field.replace(/_/g, ' ')
    const baseClass = "w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-700 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"

    if (filter.type === 'select') {
      return (
        <label key={filter.field} className="space-y-1.5 block">
          <span className="block text-xs font-black text-slate-400 uppercase tracking-wider">{label}</span>
          <Combobox
            options={(filter.options || []).map((option) => {
              const optionValue = Array.isArray(option) ? option[0] : option.value
              const optionLabel = Array.isArray(option) ? option[1] : option.label
              return { label: optionLabel, value: optionValue }
            })}
            value={value}
            onChange={(val) => setReportParams(prev => ({ ...prev, [filter.field]: String(val) }))}
            placeholder={`Select ${label}...`}
          />
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

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-180px)] overflow-hidden animate-in fade-in duration-300">
      {/* Sidebar: Report List */}
      <div className="w-full lg:w-80 flex flex-col bg-white border border-slate-200 rounded-3xl overflow-hidden shrink-0">
        <div className="p-4 border-b border-slate-100 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input 
              type="text"
              placeholder="Search reports..."
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border-none rounded-xl text-sm outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          
          <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-hide text-nowrap">
            <button
              onClick={() => setActiveModule(null)}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                activeModule === null ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
              }`}
            >
              All
            </button>
            {modules.map(mod => (
              <button
                key={mod}
                onClick={() => setActiveModule(mod)}
                className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all whitespace-nowrap ${
                  activeModule === mod ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                }`}
              >
                {mod}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-10 text-slate-400">
              <Loader2 className="animate-spin mb-2" size={24} />
              <p className="text-[10px] font-bold uppercase tracking-widest">Loading catalog...</p>
            </div>
          ) : filteredReports.length === 0 ? (
            <div className="py-10 text-center text-slate-400 text-xs italic">No reports found</div>
          ) : (
            filteredReports.map(report => (
              <button
                key={report.id}
                onClick={() => handleSelectReport(report)}
                className={`w-full text-left p-3 rounded-2xl transition-all group ${
                  activeReport?.id === report.id 
                    ? 'bg-indigo-50 border-indigo-100' 
                    : 'hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-xl shrink-0 ${
                    activeReport?.id === report.id ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-400 group-hover:bg-slate-200'
                  }`}>
                    <FileText size={16} />
                  </div>
                  <div className="min-w-0">
                    <div className={`text-sm font-bold truncate ${activeReport?.id === report.id ? 'text-indigo-900' : 'text-slate-700'}`}>
                      {report.name}
                    </div>
                    <div className="text-[10px] font-black uppercase tracking-tight text-slate-400">
                      {report.module} • {report.report_type}
                    </div>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main Content: Active Report */}
      <div className="flex-1 flex flex-col min-w-0">
        {activeReport ? (
          <div className="flex flex-col h-full gap-4">
            {/* Report Header & Filters */}
            <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm shrink-0">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-2xl font-black text-slate-900 tracking-tight">{activeReport.name}</h2>
                  <p className="text-sm font-bold text-slate-400 uppercase tracking-wider">{activeReport.module} Report — {activeReport.code}</p>
                </div>
                <button
                  disabled={runningReport !== null}
                  onClick={() => runReport(activeReport, reportParams)}
                  className="flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-extrabold rounded-2xl transition-all shadow-lg shadow-indigo-100 active:scale-[0.98]"
                >
                  {runningReport === activeReport.id ? (
                    <Loader2 className="animate-spin" size={18} />
                  ) : (
                    <Play size={18} fill="currentColor" />
                  )}
                  {runningReport === activeReport.id ? 'Generating...' : 'Generate Report'}
                </button>
              </div>

              {reportFilters.length > 0 && (
                <div className="pt-6 border-t border-slate-50">
                   <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {reportFilters.map(renderFilterInput)}
                  </div>
                </div>
              )}
            </div>

            {/* Report Results */}
            <div className="flex-1 bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-sm relative">
              {runningReport ? (
                <div className="absolute inset-0 z-10 bg-white/60 backdrop-blur-[2px] flex flex-col items-center justify-center animate-in fade-in duration-300">
                  <div className="w-16 h-16 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin mb-4" />
                  <p className="text-sm font-black text-slate-900 uppercase tracking-widest">Generating Report...</p>
                  <p className="text-xs text-slate-400 mt-2">This may take a few seconds depending on the data size.</p>
                </div>
              ) : null}

              {reportResult ? (
                <div className="h-full overflow-y-auto">
                  <GenericReport 
                    title={reportResult.title}
                    data={reportResult.data}
                    columns={reportResult.columns}
                  />
                </div>
              ) : !runningReport ? (
                <div className="h-full flex flex-col items-center justify-center p-12 text-center text-slate-300">
                  <Play size={64} className="mb-4 opacity-20" />
                  <h3 className="text-xl font-black uppercase tracking-tight">Ready to Generate</h3>
                  <p className="max-w-xs mt-2 text-sm font-medium">Click the "Generate Report" button above to fetch the latest data for this report.</p>
                </div>
              ) : null}
            </div>
          </div>
        ) : (
          <div className="flex-1 bg-white border border-slate-200 border-dashed rounded-3xl flex flex-col items-center justify-center p-12 text-center">
            <div className="w-20 h-20 bg-slate-50 rounded-3xl flex items-center justify-center text-slate-200 mb-6">
              <FileText size={40} />
            </div>
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">Select a Report</h2>
            <p className="text-slate-500 max-w-sm mt-2 font-medium">Choose a report from the catalog on the left to view its details and generate data.</p>
          </div>
        )}
      </div>
    </div>
  )
}

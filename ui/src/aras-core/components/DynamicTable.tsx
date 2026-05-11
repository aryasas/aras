import { useState, useEffect } from 'react'
import api from '../../lib/api'
import { Search, Filter, MoreHorizontal, Plus } from 'lucide-react'

interface Field {
  name: string
  label: string
  type: string
  required: boolean
  read_only: boolean
  hidden: boolean
}

interface Metadata {
  resource: string
  title: string
  fields: Field[]
}

const DynamicTable = ({ resource }: { resource: string }) => {
  const [metadata, setMetadata] = useState<Metadata | null>(null)
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')

  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true)
        setError(null)
        const [metaRes, dataRes] = await Promise.all([
          api.get(`/${resource}/metadata`),
          api.get(`/${resource}/`)
        ])
        setMetadata(metaRes.data)
        setData(dataRes.data)
      } catch (err: any) {
        console.error('Failed to fetch resource', err)
        setError(err.response?.data?.message || err.message || 'An unexpected error occurred')
      } finally {
        setLoading(false)
      }
    }
    fetchAll()
  }, [resource])

  if (loading) return (
    <div className="p-12 text-center">
      <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent"></div>
      <p className="mt-4 text-slate-500 font-medium">Loading {resource}...</p>
    </div>
  )

  if (error) return (
    <div className="p-12 text-center">
      <div className="bg-rose-50 border border-rose-200 text-rose-600 p-6 rounded-2xl max-w-lg mx-auto">
        <h3 className="font-bold text-lg mb-2">Error Loading Data</h3>
        <p className="text-sm">{error}</p>
        <button 
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-rose-600 text-white rounded-xl text-sm font-bold hover:bg-rose-700 transition-all"
        >
          Try Again
        </button>
      </div>
    </div>
  )

  if (!metadata) return <div className="p-12 text-center text-slate-500">Metadata not available for {resource}</div>

  const visibleFields = metadata.fields.filter(f => !f.hidden)

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-all">
      {/* Table Header */}
      <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-50/30">
        <div>
          <h2 className="text-xl font-bold text-slate-900">{metadata.title}</h2>
          <p className="text-slate-500 text-sm mt-1">Manage and view your {metadata.title.toLowerCase()} records.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input 
              type="text" 
              placeholder="Search..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all w-64"
            />
          </div>
          <button className="p-2 border border-slate-200 rounded-xl hover:bg-white text-slate-600 transition-colors">
            <Filter size={18} />
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-bold hover:bg-indigo-700 transition-all shadow-md shadow-indigo-100">
            <Plus size={18} />
            <span>Add New</span>
          </button>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/50">
              {visibleFields.map(field => (
                <th key={field.name} className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100">
                  {field.label}
                </th>
              ))}
              <th className="px-6 py-4 border-b border-slate-100"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.length === 0 ? (
              <tr>
                <td colSpan={visibleFields.length + 1} className="px-6 py-12 text-center text-slate-400 italic">
                  No records found in {metadata.title}.
                </td>
              </tr>
            ) : (
              data.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50/80 transition-colors group">
                  {visibleFields.map(field => (
                    <td key={field.name} className="px-6 py-4 text-sm text-slate-600">
                      {field.type === 'currency' ? (
                        <span className="font-semibold text-slate-900">
                          {new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(item[field.name])}
                        </span>
                      ) : field.type === 'email' ? (
                        <a href={`mailto:${item[field.name]}`} className="text-indigo-600 hover:underline">{item[field.name]}</a>
                      ) : (
                        item[field.name] || '-'
                      )}
                    </td>
                  ))}
                  <td className="px-6 py-4 text-right">
                    <button className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all opacity-0 group-hover:opacity-100">
                      <MoreHorizontal size={18} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Table Footer */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/30 flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500">Showing {data.length} records</span>
        <div className="flex gap-2">
          <button className="px-3 py-1 text-xs font-bold text-slate-500 border border-slate-200 rounded-lg hover:bg-white disabled:opacity-50" disabled>Previous</button>
          <button className="px-3 py-1 text-xs font-bold text-slate-500 border border-slate-200 rounded-lg hover:bg-white disabled:opacity-50" disabled>Next</button>
        </div>
      </div>
    </div>
  )
}

export default DynamicTable

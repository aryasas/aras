import { useState, useEffect } from 'react'
import { Globe, Search, Shield, ChevronLeft } from 'lucide-react'
import api from '../lib/api'
import { useNavigate } from 'react-router-dom'

interface RouteInfo {
  path: string
  name: string
  methods: string[]
}

export default function InspectRoutes() {
  const [routes, setRoutes] = useState<RouteInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/dev/inspect/routes')
      .then(res => setRoutes(res.data))
      .catch(err => console.error('Failed to fetch routes', err))
      .finally(() => setLoading(false))
  }, [])

  const filteredRoutes = routes.filter(r => 
    r.path.toLowerCase().includes(search.toLowerCase()) || 
    (r.name && r.name.toLowerCase().includes(search.toLowerCase()))
  ).sort((a, b) => a.path.localeCompare(b.path))

  return (
    <div className="p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/dev')}
            className="p-3 bg-white border border-slate-200 rounded-2xl text-slate-600 hover:bg-slate-50 transition-all shadow-sm"
          >
            <ChevronLeft size={20} />
          </button>
          <div>
            <h1 className="text-3xl font-black text-slate-900 tracking-tight flex items-center gap-3">
              <Globe className="text-indigo-600" />
              API Route Map
            </h1>
            <p className="text-slate-500 mt-1 font-medium">Full manifest of registered endpoints in the framework.</p>
          </div>
        </div>
        
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="text"
            placeholder="Search routes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-12 pr-6 py-3 bg-white border border-slate-200 rounded-2xl w-80 focus:ring-2 focus:ring-indigo-500 outline-none transition-all font-bold text-slate-700 shadow-sm"
          />
        </div>
      </div>

      <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-100">
              <th className="px-8 py-5 text-xs font-black text-slate-400 uppercase tracking-wider w-32">Methods</th>
              <th className="px-8 py-5 text-xs font-black text-slate-400 uppercase tracking-wider">Endpoint Path</th>
              <th className="px-8 py-5 text-xs font-black text-slate-400 uppercase tracking-wider">Internal Name</th>
              <th className="px-8 py-5 text-xs font-black text-slate-400 uppercase tracking-wider text-right">Security Scope</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {loading ? (
              [...Array(8)].map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td className="px-8 py-6"><div className="h-6 bg-slate-100 rounded-lg w-20"></div></td>
                  <td className="px-8 py-6"><div className="h-6 bg-slate-100 rounded-lg w-64"></div></td>
                  <td className="px-8 py-6"><div className="h-6 bg-slate-100 rounded-lg w-32"></div></td>
                  <td className="px-8 py-6 text-right"><div className="h-6 bg-slate-100 rounded-lg w-24 ml-auto"></div></td>
                </tr>
              ))
            ) : filteredRoutes.length > 0 ? (
              filteredRoutes.map((route, i) => (
                <tr key={i} className="hover:bg-slate-50/50 transition-colors group">
                  <td className="px-8 py-6">
                    <div className="flex flex-wrap gap-1">
                      {route.methods.filter(m => m !== 'OPTIONS' && m !== 'HEAD').map(m => (
                        <span key={m} className={`px-2 py-0.5 rounded-md text-[10px] font-black uppercase ${
                          m === 'GET' ? 'bg-blue-100 text-blue-700' :
                          m === 'POST' ? 'bg-emerald-100 text-emerald-700' :
                          m === 'PUT' ? 'bg-amber-100 text-amber-700' :
                          m === 'DELETE' ? 'bg-rose-100 text-rose-700' :
                          'bg-slate-100 text-slate-700'
                        }`}>
                          {m}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-2">
                       <code className="text-indigo-600 font-bold text-sm bg-indigo-50/50 px-2 py-1 rounded-lg group-hover:bg-indigo-100 transition-colors">
                        {route.path}
                      </code>
                    </div>
                  </td>
                  <td className="px-8 py-6 text-sm font-bold text-slate-400 italic">
                    {route.name || '-'}
                  </td>
                  <td className="px-8 py-6 text-right">
                     {route.path.includes('/dev/') ? (
                       <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 text-amber-600 text-[10px] font-black uppercase rounded-full border border-amber-100">
                         <Shield size={12} /> Maintenance
                       </span>
                     ) : route.path.includes('/auth/') ? (
                       <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 text-blue-600 text-[10px] font-black uppercase rounded-full border border-blue-100">
                         Identity
                       </span>
                     ) : (
                       <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-50 text-slate-400 text-[10px] font-black uppercase rounded-full border border-slate-100">
                         Resource
                       </span>
                     )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="px-8 py-20 text-center">
                   <div className="text-slate-300 font-bold text-lg">No routes found matching your search.</div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

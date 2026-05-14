import { useState, useEffect, useRef } from 'react'
import { Package, Plus, RefreshCw, CheckCircle2, Trash2, X, AlertCircle, Upload, Code } from 'lucide-react'
import api from '../lib/api'
import { MetadataService } from '../aras-core/services/MetadataService'
import * as Icons from 'lucide-react'

interface AppManifest {
  name: string
  label: string
  description: string
  icon: string
  version: string
  models: string[]
  is_active?: boolean
  is_registered?: boolean
}

const YAML_TEMPLATE = `app:
  name: my_new_app
  label: My New App
  description: A custom application for specialized tasks.
  icon: Box
  version: 1.0.0

tables:
  - name: items
    title: Inventory Items
    columns:
      - name: sku
        label: SKU
        field_type: string
        required: true
      - name: price
        label: Unit Price
        field_type: float
      - name: stock
        label: Stock Level
        field_type: integer
      - name: is_active
        label: Active
        field_type: boolean
`;

const JSON_TEMPLATE = `{
  "app": {
    "name": "my_json_app",
    "label": "My JSON App",
    "description": "App defined via JSON",
    "icon": "Package",
    "version": "1.0.0"
  },
  "tables": [
    {
      "name": "data",
      "columns": [
        { "name": "title", "field_type": "string", "required": true }
      ]
    }
  ]
}`;

export default function AppManager() {
  const [apps, setApps] = useState<AppManifest[]>([])
  const [syncing, setSyncing] = useState(false)
  const [installModalOpen, setInstallModalOpen] = useState(false)
  const [installMode, setInstallMode] = useState<'yaml' | 'json' | 'upload'>('yaml')
  const [yamlContent, setYamlContent] = useState(YAML_TEMPLATE)
  const [jsonContent, setJsonContent] = useState(JSON_TEMPLATE)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [installing, setInstalling] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchApps = async () => {
    try {
      const res = await api.get('/admin/apps')
      setApps(res.data)
    } catch (error) {
      console.error('Failed to fetch apps', error)
    }
  }

  const handleSync = async () => {
    setSyncing(true)
    try {
      await api.post('/dev/sync')
      MetadataService.clearCache()
      fetchApps()
    } catch (error) {
      alert('Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  const handleInstall = async () => {
    setInstalling(true)
    setError(null)
    try {
      let payload: any = null
      let config: any = {}

      if (installMode === 'yaml') {
        payload = yamlContent
        config = { headers: { 'Content-Type': 'text/plain' } }
      } else if (installMode === 'json') {
        payload = JSON.parse(jsonContent)
        // FastAPI will handle this as json_content Body
      } else if (installMode === 'upload' && selectedFile) {
        const formData = new FormData()
        formData.append('file', selectedFile)
        payload = formData
        config = { headers: { 'Content-Type': 'multipart/form-data' } }
      } else {
        throw new Error('Please select a file or provide content.')
      }

      await api.post('/admin/install', payload, config)
      setInstallModalOpen(false)
      fetchApps()
      alert('App installed successfully!')
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Installation failed')
    } finally {
      setInstalling(false)
    }
  }

  useEffect(() => {
    fetchApps()
  }, [])

  return (
    <div className="p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight flex items-center gap-3">
            <Package className="text-indigo-600" />
            App Manager
          </h1>
          <p className="text-slate-500 mt-1 font-medium">Install, configure, and manage framework extensions.</p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-6 py-3 bg-white border border-slate-200 text-slate-700 rounded-2xl font-bold hover:bg-slate-50 transition-all shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={syncing ? 'animate-spin' : ''} size={18} />
            {syncing ? 'Syncing...' : 'Sync Registry'}
          </button>
          <button 
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200"
            onClick={() => setInstallModalOpen(true)}
          >
            <Plus size={18} />
            Install New App
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {apps.map(app => (
          <AppCard key={app.name} app={app} />
        ))}
        
        {/* Placeholder for "Add New" */}
        <div 
          className="border-2 border-dashed border-slate-200 rounded-[2.5rem] p-8 flex flex-col items-center justify-center text-center group hover:border-indigo-300 transition-all cursor-pointer"
          onClick={() => setInstallModalOpen(true)}
        >
          <div className="p-4 bg-slate-50 rounded-2xl mb-4 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
            <Plus size={32} />
          </div>
          <h3 className="text-lg font-bold text-slate-900">Custom Extension</h3>
          <p className="text-slate-500 text-sm mt-1">Develop your own app and drop it into the <code>apps/</code> folder.</p>
        </div>
      </div>

      {/* Installation Modal */}
      {installModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-300">
          <div className="bg-white rounded-[2.5rem] w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[95vh] animate-in zoom-in-95 duration-300">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
                  <Plus size={20} />
                </div>
                <h2 className="text-xl font-black text-slate-900">Install New Application</h2>
              </div>
              <button 
                onClick={() => setInstallModalOpen(false)}
                className="p-2 hover:bg-slate-200 rounded-full transition-colors"
              >
                <X size={20} className="text-slate-400" />
              </button>
            </div>
            
            <div className="flex bg-slate-100 p-1 m-6 rounded-xl">
              <button 
                onClick={() => setInstallMode('yaml')}
                className={`flex-1 py-2 rounded-lg font-bold text-sm transition-all ${installMode === 'yaml' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
              >
                YAML Code
              </button>
              <button 
                onClick={() => setInstallMode('json')}
                className={`flex-1 py-2 rounded-lg font-bold text-sm transition-all ${installMode === 'json' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
              >
                JSON Code
              </button>
              <button 
                onClick={() => setInstallMode('upload')}
                className={`flex-1 py-2 rounded-lg font-bold text-sm transition-all ${installMode === 'upload' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
              >
                File Upload
              </button>
            </div>

            <div className="px-6 pb-6 flex-1 overflow-y-auto">
              {installMode === 'upload' ? (
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-200 rounded-3xl p-12 flex flex-col items-center justify-center text-center hover:border-indigo-300 transition-all cursor-pointer bg-slate-50 group"
                >
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    className="hidden" 
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    accept=".zip,.yaml,.yml,.json"
                  />
                  <div className="p-6 bg-white rounded-2xl mb-4 group-hover:scale-110 transition-transform shadow-sm">
                    <Upload size={40} className="text-indigo-600" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">
                    {selectedFile ? selectedFile.name : 'Choose a file...'}
                  </h3>
                  <p className="text-slate-500 text-sm mt-1 max-w-xs">
                    Support for .zip (Python apps), .yaml, or .json definitions.
                  </p>
                </div>
              ) : (
                <div className="relative">
                  <textarea
                    value={installMode === 'yaml' ? yamlContent : jsonContent}
                    onChange={(e) => installMode === 'yaml' ? setYamlContent(e.target.value) : setJsonContent(e.target.value)}
                    className="w-full h-80 p-4 bg-slate-900 text-indigo-300 font-mono text-sm rounded-2xl border-0 focus:ring-2 focus:ring-indigo-500 resize-none"
                    spellCheck={false}
                  />
                  <div className="absolute top-4 right-4 text-slate-500">
                    <Code size={16} />
                  </div>
                </div>
              )}

              {error && (
                <div className="mt-4 p-4 bg-red-50 text-red-600 rounded-xl flex items-center gap-3 text-sm font-bold border border-red-100">
                  <AlertCircle size={18} />
                  {error}
                </div>
              )}
            </div>

            <div className="p-6 border-t border-slate-100 flex justify-end gap-3 bg-slate-50">
              <button 
                onClick={() => setInstallModalOpen(false)}
                className="px-6 py-3 text-slate-500 font-bold hover:text-slate-700 transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={handleInstall}
                disabled={installing || (installMode === 'upload' && !selectedFile)}
                className="flex items-center gap-2 px-8 py-3 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 disabled:opacity-50"
              >
                {installing ? <RefreshCw className="animate-spin" size={18} /> : <CheckCircle2 size={18} />}
                {installing ? 'Installing...' : 'Install App'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function AppCard({ app }: { app: AppManifest }) {
  // @ts-ignore
  const Icon = Icons[app.icon] || Icons.Package
  const isActive = app.is_active !== false
  
  return (
    <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-sm overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all group">
      <div className="p-8">
        <div className="flex items-start justify-between mb-6">
          <div className="p-4 bg-indigo-50 text-indigo-600 rounded-2xl group-hover:scale-110 transition-transform">
            <Icon size={28} />
          </div>
          <div className="flex flex-col items-end">
            <span className={`px-3 py-1 ${isActive ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-slate-50 text-slate-400 border-slate-100'} text-[10px] font-black uppercase tracking-widest rounded-full flex items-center gap-1 border`}>
              {isActive ? <CheckCircle2 size={10} /> : <Icons.Circle size={10} />}
              {isActive ? 'Active' : 'Inactive'}
            </span>
            <span className="text-xs font-bold text-slate-400 mt-2">v{app.version}</span>
          </div>
        </div>
        
        <h3 className="text-xl font-black text-slate-900 mb-2">{app.label}</h3>
        <p className="text-slate-500 text-sm leading-relaxed mb-6 line-clamp-2">
          {app.description || 'No description provided for this application.'}
        </p>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-bold">
            <span className="text-slate-400 uppercase tracking-wider">Models</span>
            <span className="text-slate-900 bg-slate-100 px-2 py-0.5 rounded-md">{app.models.length}</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {app.models.slice(0, 3).map(m => (
              <span key={m} className="px-2 py-0.5 bg-slate-50 text-slate-500 text-[10px] font-bold rounded-md border border-slate-100">
                {m}
              </span>
            ))}
            {app.models.length > 3 && (
              <span className="px-2 py-0.5 bg-slate-50 text-slate-400 text-[10px] font-bold rounded-md">
                +{app.models.length - 3} more
              </span>
            )}
          </div>
        </div>
      </div>
      
      <div className="px-8 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
        <button className="text-indigo-600 text-sm font-black hover:text-indigo-700 transition-colors">
          Configure
        </button>
        <button className="p-2 text-slate-300 hover:text-red-500 transition-colors">
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  )
}

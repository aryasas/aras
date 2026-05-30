import { useState, useEffect, useRef } from 'react'
import { Plus, RefreshCw, CheckCircle2, Trash2, X, AlertCircle, Upload, Code } from 'lucide-react'
import api from '../lib/api'
import { MetadataService } from '../aras-core/services/MetadataService'
import { useUIStore } from '../store/uiStore'
import * as Icons from 'lucide-react'

interface AppManifest {
  name: string
  parent_name?: string
  label: string
  description: string
  icon: string
  version: string
  models: string[]
  required?: boolean
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
  const setPageTitle = useUIStore(state => state.setPageTitle)

  useEffect(() => {
    setPageTitle('App Manager', 'Install, configure, and manage framework extensions.', 'SYSTEM / EXTENSIONS')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

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

  const handleUninstall = async (app: AppManifest) => {
    if (app.required) return
    if (!window.confirm(`Uninstall ${app.label || app.name}?`)) return
    try {
      await api.delete(`/admin/apps/${app.name}`).catch(() => api.delete(`/admin/uninstall/${app.name}`))
      fetchApps()
    } catch (error: any) {
      alert(error.message || 'Uninstall failed')
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

  const rootApps = apps.filter(app => !app.parent_name)
  const subModules = apps.filter(app => app.parent_name)

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-end mb-8 gap-3">
        <button 
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 px-6 py-3 bg-[var(--app-panel)] border border-[var(--app-border)] text-[var(--app-text)] rounded-[var(--app-radius-lg)] font-bold hover:bg-[var(--app-panel-soft)] transition-all shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={syncing ? 'animate-spin' : ''} size={18} />
          {syncing ? 'Syncing...' : 'Sync Registry'}
        </button>
        <button 
          className="flex items-center gap-2 px-6 py-3 bg-[var(--app-accent)] text-white rounded-[var(--app-radius-lg)] font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200"
          onClick={() => setInstallModalOpen(true)}
        >
          <Plus size={18} />
          Install New App
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {rootApps.map(app => (
          <AppCard
            key={app.name}
            app={app}
            subModules={subModules.filter(sub => sub.parent_name === app.name)}
            onUninstall={handleUninstall}
          />
        ))}
        
        {/* Placeholder for "Add New" */}
        <div 
          className="border-2 border-dashed border-[var(--app-border)] rounded-[2.5rem] p-8 flex flex-col items-center justify-center text-center group hover:border-indigo-300 transition-all cursor-pointer"
          onClick={() => setInstallModalOpen(true)}
        >
          <div className="p-4 bg-[var(--app-panel-soft)] rounded-[var(--app-radius-lg)] mb-4 group-hover:bg-[var(--app-accent-glow)] group-hover:text-[var(--app-accent)] transition-colors">
            <Plus size={32} />
          </div>
          <h3 className="text-lg font-bold text-[var(--app-text)]">Custom Extension</h3>
          <p className="text-[var(--app-muted)] text-sm mt-1">Develop your own app and drop it into the <code>apps/</code> folder.</p>
        </div>
      </div>

      {/* Installation Modal */}
      {installModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-300">
          <div className="bg-[var(--app-panel)] rounded-[2.5rem] w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[95vh] animate-in zoom-in-95 duration-300">
            <div className="p-6 border-b border-[var(--app-border)] flex items-center justify-between bg-[var(--app-panel-soft)]">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[var(--app-accent-glow)] text-[var(--app-accent)] rounded-[var(--app-radius)]">
                  <Plus size={20} />
                </div>
                <h2 className="text-xl font-black text-[var(--app-text)]">Install New Application</h2>
              </div>
              <button 
                onClick={() => setInstallModalOpen(false)}
                className="p-2 hover:bg-slate-200 rounded-full transition-colors"
              >
                <X size={20} className="text-[var(--app-muted)]" />
              </button>
            </div>
            
            <div className="flex bg-[var(--app-panel-soft)] p-1 m-6 rounded-[var(--app-radius)]">
              <button 
                onClick={() => setInstallMode('yaml')}
                className={`flex-1 py-2 rounded-[var(--app-radius)] font-bold text-sm transition-all ${installMode === 'yaml' ? 'bg-[var(--app-panel)] text-[var(--app-accent)] shadow-sm' : 'text-[var(--app-muted)] hover:text-[var(--app-text)]'}`}
              >
                YAML Code
              </button>
              <button 
                onClick={() => setInstallMode('json')}
                className={`flex-1 py-2 rounded-[var(--app-radius)] font-bold text-sm transition-all ${installMode === 'json' ? 'bg-[var(--app-panel)] text-[var(--app-accent)] shadow-sm' : 'text-[var(--app-muted)] hover:text-[var(--app-text)]'}`}
              >
                JSON Code
              </button>
              <button 
                onClick={() => setInstallMode('upload')}
                className={`flex-1 py-2 rounded-[var(--app-radius)] font-bold text-sm transition-all ${installMode === 'upload' ? 'bg-[var(--app-panel)] text-[var(--app-accent)] shadow-sm' : 'text-[var(--app-muted)] hover:text-[var(--app-text)]'}`}
              >
                File Upload
              </button>
            </div>

            <div className="px-6 pb-6 flex-1 overflow-y-auto">
              {installMode === 'upload' ? (
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-[var(--app-border)] rounded-[var(--app-radius-lg)] p-12 flex flex-col items-center justify-center text-center hover:border-indigo-300 transition-all cursor-pointer bg-[var(--app-panel-soft)] group"
                >
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    className="hidden" 
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    accept=".zip,.yaml,.yml,.json"
                  />
                  <div className="p-6 bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] mb-4 group-hover:scale-110 transition-transform shadow-sm">
                    <Upload size={40} className="text-[var(--app-accent)]" />
                  </div>
                  <h3 className="text-lg font-bold text-[var(--app-text)]">
                    {selectedFile ? selectedFile.name : 'Choose a file...'}
                  </h3>
                  <p className="text-[var(--app-muted)] text-sm mt-1 max-w-xs">
                    Support for .zip (Python apps), .yaml, or .json definitions.
                  </p>
                </div>
              ) : (
                <div className="relative">
                  <textarea
                    value={installMode === 'yaml' ? yamlContent : jsonContent}
                    onChange={(e) => installMode === 'yaml' ? setYamlContent(e.target.value) : setJsonContent(e.target.value)}
                    className="w-full h-80 p-4 bg-slate-900 text-indigo-300 font-mono text-sm rounded-[var(--app-radius-lg)] border-0 focus:ring-2 focus:ring-indigo-500 resize-none"
                    spellCheck={false}
                  />
                  <div className="absolute top-4 right-4 text-[var(--app-muted)]">
                    <Code size={16} />
                  </div>
                </div>
              )}

              {error && (
                <div className="mt-4 p-4 bg-red-50 text-red-600 rounded-[var(--app-radius)] flex items-center gap-3 text-sm font-bold border border-red-100">
                  <AlertCircle size={18} />
                  {error}
                </div>
              )}
            </div>

            <div className="p-6 border-t border-[var(--app-border)] flex justify-end gap-3 bg-[var(--app-panel-soft)]">
              <button 
                onClick={() => setInstallModalOpen(false)}
                className="px-6 py-3 text-[var(--app-muted)] font-bold hover:text-[var(--app-text)] transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={handleInstall}
                disabled={installing || (installMode === 'upload' && !selectedFile)}
                className="flex items-center gap-2 px-8 py-3 bg-[var(--app-accent)] text-white rounded-[var(--app-radius-lg)] font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 disabled:opacity-50"
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

function AppCard({ app, subModules, onUninstall }: { app: AppManifest; subModules: AppManifest[]; onUninstall: (app: AppManifest) => void }) {
  // @ts-ignore
  const Icon = Icons[app.icon] || Icons.Package
  const isActive = app.is_active !== false
  
  return (
    <div className="bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-sm overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all group">
      <div className="p-8">
        <div className="flex items-start justify-between mb-6">
          <div className="p-4 bg-[var(--app-accent-glow)] text-[var(--app-accent)] rounded-[var(--app-radius-lg)] group-hover:scale-110 transition-transform">
            <Icon size={28} />
          </div>
          <div className="flex flex-col items-end">
            <div className="flex flex-wrap justify-end gap-1">
              <span className={`px-3 py-1 ${isActive ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-[var(--app-panel-soft)] text-[var(--app-muted)] border-[var(--app-border)]'} text-[10px] font-black uppercase tracking-widest rounded-full flex items-center gap-1 border`}>
                {isActive ? <CheckCircle2 size={10} /> : <Icons.Circle size={10} />}
                {isActive ? 'Active' : 'Inactive'}
              </span>
              {app.required ? (
                <span className="rounded-full border border-[var(--app-border)] bg-[var(--app-panel-soft)] px-3 py-1 text-[10px] font-black uppercase tracking-widest text-[var(--app-muted)]">
                  Required
                </span>
              ) : null}
            </div>
            <span className="text-xs font-bold text-[var(--app-muted)] mt-2">v{app.version}</span>
          </div>
        </div>
        
        <h3 className="text-xl font-black text-[var(--app-text)] mb-2 flex items-center gap-2">
          {app.label}
        </h3>
        <p className="text-[var(--app-muted)] text-sm leading-relaxed mb-6 line-clamp-2">
          {app.description || 'No description provided for this application.'}
        </p>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-bold">
            <span className="text-[var(--app-muted)] uppercase tracking-wider">Models</span>
            <span className="text-[var(--app-text)] bg-[var(--app-panel-soft)] px-2 py-0.5 rounded-md">{app.models.length}</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {app.models.slice(0, 3).map(m => (
              <span key={m} className="px-2 py-0.5 bg-[var(--app-panel-soft)] text-[var(--app-muted)] text-[10px] font-bold rounded-md border border-[var(--app-border)]">
                {m}
              </span>
            ))}
            {app.models.length > 3 && (
              <span className="px-2 py-0.5 bg-[var(--app-panel-soft)] text-[var(--app-muted)] text-[10px] font-bold rounded-md">
                +{app.models.length - 3} more
              </span>
            )}
          </div>
          {subModules.length > 0 && (
            <div className="pt-3 border-t border-[var(--app-border)]">
              <div className="text-xs font-bold text-[var(--app-muted)] uppercase tracking-wider mb-2">Sub-modules</div>
              <div className="flex flex-wrap gap-1">
                {subModules.map(sub => (
                  <span key={sub.name} className="px-2 py-1 bg-[var(--app-accent-glow)] text-[var(--app-accent)] text-[10px] font-bold rounded-md border border-indigo-100">
                    {sub.label || sub.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      
      <div className="px-8 py-4 bg-[var(--app-panel-soft)] border-t border-[var(--app-border)] flex items-center justify-between">
        <button className="text-[var(--app-accent)] text-sm font-black hover:text-indigo-700 transition-colors">
          Configure
        </button>
        <button
          className="p-2 text-slate-300 transition-colors hover:text-red-500 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:text-slate-300"
          disabled={Boolean(app.required)}
          title={app.required ? 'Required apps cannot be uninstalled' : 'Uninstall app'}
          onClick={() => onUninstall(app)}
        >
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  )
}

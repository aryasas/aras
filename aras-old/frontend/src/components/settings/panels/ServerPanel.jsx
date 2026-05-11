import React, { useState, useEffect } from 'react'

export default function ServerPanel({ server_info }) {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    fetch('/admin/api/settings/server/config')
      .then(res => res.json())
      .then(data => {
        setConfig(data)
        setLoading(false)
      })
  }, [])

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      const res = await fetch('/admin/api/settings/server/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      })
      const result = await res.json()
      if (result.success) {
        setMessage({ type: 'success', text: 'Server configuration saved. Please restart the server to apply changes.' })
      } else {
        setMessage({ type: 'error', text: result.message || 'Failed to save configuration.' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'An error occurred while saving.' })
    }
    setSaving(false)
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setConfig(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (type === 'number' ? parseInt(value) : value)
    }))
  }

  if (loading) return <div className="p-10 text-center text-aras-primary/50 italic">Loading server configuration...</div>

  return (
    <div className="animate-fade-in space-y-8">
      <div>
        <h3 className="text-3xl font-studio-serif font-bold text-aras-primary mb-2">Server Management</h3>
        <p className="text-aras-primary/50 text-sm italic">Monitor status and configure production WSGI settings.</p>
      </div>

      {message && (
        <div className={`p-4 text-xs font-bold uppercase tracking-widest ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {message.text}
        </div>
      )}

      {/* MONITORING CARD */}
      <div className="bg-white border border-aras-primary/10 p-8 shadow-sm">
        <h4 className="text-[10px] font-bold text-aras-primary/30 uppercase tracking-[0.2em] border-b border-aras-primary/5 pb-3 mb-6">Status & Runtime</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
           <StatusItem label="Environment" value={server_info?.env} accent />
           <StatusItem label="Python" value={server_info?.python_version} mono />
           <StatusItem label="Debug Mode" value={server_info?.debug ? 'ENABLED' : 'DISABLED'} warning={server_info?.debug} />
           <StatusItem label="Host" value={server_info?.host} mono />
           <StatusItem label="Server Time" value={server_info?.server_time} mono />
           <StatusItem label="Uptime" value={server_info?.uptime} />
        </div>
      </div>

      {/* WSGI CONFIG FORM */}
      <form onSubmit={handleSave} className="bg-white border border-aras-primary/10 p-8 shadow-sm space-y-8">
        <div className="flex items-center justify-between border-b border-aras-primary/5 pb-3">
          <h4 className="text-[10px] font-bold text-aras-primary/30 uppercase tracking-[0.2em]">WSGI Configuration</h4>
          <span className="text-[9px] text-aras-primary/40 italic">Stored in instance/server.json</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6">
          <FormField label="WSGI Server">
            <select name="wsgi_server" value={config.wsgi_server} onChange={handleChange} className="aras-input">
              <option value="gunicorn">Gunicorn (Production)</option>
              <option value="uwsgi">uWSGI</option>
              <option value="flask">Flask (Development)</option>
            </select>
          </FormField>

          <FormField label="Log Level">
            <select name="loglevel" value={config.loglevel} onChange={handleChange} className="aras-input">
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="critical">Critical</option>
            </select>
          </FormField>

          <FormField label="Bind Host">
            <input type="text" name="host" value={config.host} onChange={handleChange} className="aras-input font-mono" placeholder="0.0.0.0" />
          </FormField>

          <FormField label="Port">
            <input type="number" name="port" value={config.port} onChange={handleChange} className="aras-input font-mono" min="1" max="65535" />
          </FormField>

          <FormField label="Workers" help="Recommended: (2 × CPU) + 1">
            <input type="number" name="workers" value={config.workers} onChange={handleChange} className="aras-input font-mono" min="1" max="32" />
          </FormField>

          <FormField label="Threads">
            <input type="number" name="threads" value={config.threads} onChange={handleChange} className="aras-input font-mono" min="1" max="32" />
          </FormField>

          <FormField label="Worker Class">
            <select name="worker_class" value={config.worker_class} onChange={handleChange} className="aras-input">
              <option value="sync">Sync</option>
              <option value="gthread">Gthread</option>
              <option value="gevent">Gevent</option>
              <option value="eventlet">Eventlet</option>
            </select>
          </FormField>

          <FormField label="Timeout (seconds)">
            <input type="number" name="timeout" value={config.timeout} onChange={handleChange} className="aras-input font-mono" min="1" />
          </FormField>
        </div>

        <div className="pt-6 border-top border-aras-primary/5 flex justify-end">
          <button 
            type="submit" 
            disabled={saving}
            className="bg-aras-primary text-white px-8 py-3 text-[10px] font-bold uppercase tracking-[0.2em] hover:bg-aras-primary/90 transition-all disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </form>
    </div>
  )
}

function StatusItem({ label, value, accent, mono, warning }) {
  return (
    <div>
      <label className="text-[9px] font-bold text-aras-primary/30 uppercase tracking-[0.2em] mb-1 block">{label}</label>
      <div className={`text-sm font-bold ${accent ? 'text-aras-accent' : warning ? 'text-red-500' : 'text-aras-primary'} ${mono ? 'font-mono' : ''}`}>
        {value || '—'}
      </div>
    </div>
  )
}

function FormField({ label, help, children }) {
  return (
    <div className="space-y-2">
      <label className="text-[10px] font-bold text-aras-primary/60 uppercase tracking-wider block">{label}</label>
      {children}
      {help && <p className="text-[9px] text-aras-primary/30 italic">{help}</p>}
    </div>
  )
}

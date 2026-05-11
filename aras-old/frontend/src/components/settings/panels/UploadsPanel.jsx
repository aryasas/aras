import React, { useState, useEffect } from 'react'

export default function UploadsPanel() {
  const [config, setConfig] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    // Re-use server config API as it likely contains upload paths
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
        setMessage({ type: 'success', text: 'Upload paths saved.' })
      } else {
        setMessage({ type: 'error', text: result.message || 'Failed to save.' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'An error occurred.' })
    }
    setSaving(false)
  }

  const handleChange = (e) => {
    setConfig({ ...config, [e.target.name]: e.target.value })
  }

  if (loading) return <div className="p-10 text-center text-aras-primary/50 italic">Loading upload settings...</div>

  const uploadKeys = [
    { name: 'UPLOAD_FOLDER', label: 'Base Upload Folder', help: 'Absolute path or relative to project root.' },
    { name: 'UPLOAD_IMAGE_FOLDER', label: 'Images Folder' },
    { name: 'UPLOAD_DOC_FOLDER', label: 'Documents Folder' },
    { name: 'UPLOAD_PDF_FOLDER', label: 'PDFs Folder' },
  ]

  return (
    <div className="animate-fade-in space-y-8">
      <div>
        <h3 className="text-3xl font-studio-serif font-bold text-aras-primary mb-2">Upload Configuration</h3>
        <p className="text-aras-primary/50 text-sm italic">Define storage locations for different asset types.</p>
      </div>

      {message && (
        <div className={`p-4 text-xs font-bold uppercase tracking-widest ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {message.text}
        </div>
      )}

      <form onSubmit={handleSave} className="bg-white border border-aras-primary/10 p-8 shadow-sm space-y-6">
        {uploadKeys.map(key => (
          <div key={key.name} className="space-y-2">
            <label className="text-[10px] font-bold text-aras-primary/60 uppercase tracking-wider block">{key.label}</label>
            <input 
              type="text" 
              name={key.name}
              value={config[key.name] || ''}
              onChange={handleChange}
              className="w-full bg-aras-primary/5 border border-aras-primary/10 px-4 py-3 text-xs font-mono text-aras-primary focus:border-aras-accent outline-none"
              placeholder="/var/www/uploads/..."
            />
            {key.help && <p className="text-[9px] text-aras-primary/30 italic">{key.help}</p>}
          </div>
        ))}

        <div className="pt-6 border-t border-aras-primary/5 flex justify-end">
          <button 
            type="submit" 
            disabled={saving}
            className="bg-aras-primary text-white px-8 py-3 text-[10px] font-bold uppercase tracking-[0.2em] hover:bg-aras-primary/90 transition-all disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Upload Paths'}
          </button>
        </div>
      </form>
    </div>
  )
}

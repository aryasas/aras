import React, { useState, useEffect } from 'react'

export default function SystemPanel() {
  const [settings, setSettings] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(null)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    fetch('/api/admin/system-settings/?per_page=100')
      .then(res => res.json())
      .then(res => {
        setSettings(res.data)
        setLoading(false)
      })
  }, [])

  const handleToggle = async (key, currentValue) => {
    const newValue = !currentValue
    setSaving(key)
    try {
      const res = await fetch('/admin/api/settings/system/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: newValue })
      })
      const result = await res.json()
      if (result.success) {
        setSettings(prev => prev.map(s => s.key === key ? { ...s, value: newValue } : s))
      }
    } catch (err) {
      console.error(err)
    }
    setSaving(null)
  }

  const handleInputChange = async (key, value) => {
     setSaving(key)
     try {
       const res = await fetch('/admin/api/settings/system/save', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ [key]: value })
       })
       const result = await res.json()
       if (result.success) {
         setSettings(prev => prev.map(s => s.key === key ? { ...s, value: value } : s))
       }
     } catch (err) {
       console.error(err)
     }
     setSaving(null)
  }

  if (loading) return <div className="p-10 text-center text-aras-primary/50 italic">Loading system configuration...</div>

  const sections = {}
  settings.forEach(s => {
    const sec = s.section || 'General'
    if (!sections[sec]) sections[sec] = []
    sections[sec].push(s)
  })

  return (
    <div className="animate-fade-in space-y-8">
      <div>
        <h3 className="text-3xl font-studio-serif font-bold text-aras-primary mb-2">System Configuration</h3>
        <p className="text-aras-primary/50 text-sm italic">High-level framework toggles and feature flags.</p>
      </div>

      {Object.entries(sections).map(([name, items]) => (
        <div key={name} className="bg-white border border-aras-primary/10 p-8 shadow-sm">
          <h4 className="text-[10px] font-bold text-aras-primary/30 uppercase tracking-[0.2em] border-b border-aras-primary/5 pb-3 mb-6">
            {name.replace(/_/g, ' ')}
          </h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {items.map(item => (
              <div key={item.key} className="flex flex-col justify-between p-4 bg-aras-primary/5 border border-aras-primary/5 group hover:border-aras-primary/20 transition-all">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1 pr-4">
                    <label className="text-[11px] font-bold text-aras-primary block mb-1 uppercase tracking-wider">{item.label || item.key}</label>
                    {item.help_text && <p className="text-[10px] text-aras-primary/40 italic leading-relaxed">{item.help_text}</p>}
                  </div>
                  
                  {item.value_type === 'boolean' && (
                    <button
                      onClick={() => handleToggle(item.key, item.value === true || item.value === 'true' || item.value === '1' || item.value === 1)}
                      disabled={saving === item.key}
                      className={`relative inline-flex h-5 w-10 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        (item.value === true || item.value === 'true' || item.value === '1' || item.value === 1) ? 'bg-aras-accent' : 'bg-gray-200'
                      }`}
                    >
                      <span className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        (item.value === true || item.value === 'true' || item.value === '1' || item.value === 1) ? 'translate-x-5' : 'translate-x-0'
                      }`} />
                    </button>
                  )}
                </div>

                {item.value_type !== 'boolean' && (
                  <div className="relative">
                    <input 
                      type="text"
                      defaultValue={item.value}
                      onBlur={(e) => handleInputChange(item.key, e.target.value)}
                      className="w-full bg-white border border-aras-primary/10 px-3 py-2 text-xs font-mono text-aras-primary focus:border-aras-accent outline-none transition-all"
                      placeholder="Enter value..."
                    />
                    {saving === item.key && <div className="absolute right-2 top-2 text-[8px] uppercase font-bold text-aras-accent animate-pulse">Saving...</div>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

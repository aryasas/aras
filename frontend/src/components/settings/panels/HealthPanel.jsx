import React, { useState, useEffect } from 'react'

export default function HealthPanel() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/admin/api/settings/health')
      .then(res => res.json())
      .then(res => {
        setData(res)
        setLoading(false)
      })
  }, [])

  if (loading) return <div className="p-10 text-center text-aras-primary/50 italic">Running diagnostic checks...</div>

  const hasErrors = data?.errors?.length > 0

  return (
    <div className="animate-fade-in space-y-8">
      <div>
        <h3 className="text-3xl font-studio-serif font-bold text-aras-primary mb-2">Framework Health</h3>
        <p className="text-aras-primary/50 text-sm italic">Automated integrity checks and resource status monitoring.</p>
      </div>

      <div className="bg-white border border-aras-primary/10 shadow-sm overflow-hidden">
        <div className="p-8 border-b border-aras-primary/5 flex justify-between items-center">
          <div className="flex items-center gap-4">
             <div className={`w-3 h-3 rounded-full animate-pulse ${hasErrors ? 'bg-red-500' : 'bg-green-500'}`}></div>
             <div>
                <h4 className="text-sm font-bold text-aras-primary uppercase tracking-widest">
                  {hasErrors ? `${data.errors.length} Issues Detected` : 'All Systems Operational'}
                </h4>
                <p className="text-[10px] text-aras-primary/40 italic">Last checked: {data?.checked_at || 'Never'}</p>
             </div>
          </div>
          <button 
            onClick={() => { setLoading(true); window.location.reload(); }}
            className="text-[9px] font-bold uppercase tracking-[0.2em] px-4 py-2 border border-aras-primary/10 hover:bg-aras-primary hover:text-white transition-all"
          >
            Run Diagnostic
          </button>
        </div>

        <div className="p-8 space-y-8">
           {hasErrors && (
             <div>
                <h5 className="text-[10px] font-bold text-red-500 uppercase tracking-[0.2em] mb-4">Critical Issues</h5>
                <div className="space-y-3">
                  {data.errors.map((err, i) => (
                    <div key={i} className="p-4 bg-red-50 border-l-2 border-red-500 flex justify-between items-start">
                       <div>
                          <code className="text-[10px] font-bold text-red-700 block mb-1">{err.resource}</code>
                          <p className="text-xs text-red-600 italic">{err.error}</p>
                       </div>
                    </div>
                  ))}
                </div>
             </div>
           )}

           <div>
              <h5 className="text-[10px] font-bold text-aras-primary/30 uppercase tracking-[0.2em] mb-4">Passing Checks ({data?.ok?.length || 0})</h5>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {data?.ok?.map((res, i) => (
                  <div key={i} className="flex items-center gap-2 p-2 bg-aras-primary/5 border border-aras-primary/5">
                     <i className="fa fa-check text-green-500 text-[8px]"></i>
                     <code className="text-[10px] text-aras-primary/60 truncate">{res}</code>
                  </div>
                ))}
              </div>
           </div>
        </div>
      </div>
    </div>
  )
}

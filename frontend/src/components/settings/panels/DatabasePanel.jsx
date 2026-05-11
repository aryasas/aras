import React, { useState, useEffect } from 'react'

export default function DatabasePanel() {
  const [tables, setTables] = useState([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')

  useEffect(() => {
    fetch(`/admin/api/settings/db/tables${q ? '?q=' + q : ''}`)
      .then(res => res.json())
      .then(res => {
        setTables(res.data)
        setLoading(false)
      })
  }, [q])

  if (loading && !q) return <div className="p-10 text-center text-aras-primary/50 italic">Inspecting database...</div>

  return (
    <div className="animate-fade-in space-y-8">
      <div>
        <h3 className="text-3xl font-studio-serif font-bold text-aras-primary mb-2">Database Inspector</h3>
        <p className="text-aras-primary/50 text-sm italic">Direct view of physical database tables and their schema structure.</p>
      </div>

      <div className="bg-white border border-aras-primary/10 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-aras-primary/5 bg-aras-primary/5 flex justify-between items-center">
          <div className="relative w-64">
             <i className="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-aras-primary/20 text-[10px]"></i>
             <input 
               type="text" 
               placeholder="Search tables..."
               value={q}
               onChange={(e) => setQ(e.target.value)}
               className="w-full pl-8 pr-4 py-1.5 text-[10px] uppercase font-bold tracking-widest bg-white border border-aras-primary/10 focus:border-aras-accent outline-none"
             />
          </div>
          <span className="text-[10px] font-bold text-aras-primary/30 uppercase tracking-[0.2em]">{tables.length} Tables found</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-aras-primary/5 border-b border-aras-primary/10">
                <th className="px-6 py-3 text-[10px] font-bold text-aras-primary/40 uppercase tracking-[0.2em]">Table Name</th>
                <th className="px-6 py-3 text-[10px] font-bold text-aras-primary/40 uppercase tracking-[0.2em]">Structure</th>
                <th className="px-6 py-3 text-[10px] font-bold text-aras-primary/40 uppercase tracking-[0.2em] text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-aras-primary/5">
              {tables.map(table => (
                <tr key={table.id} className="hover:bg-aras-primary/5 transition-all group">
                  <td className="px-6 py-4">
                    <div className="text-xs font-bold font-mono text-aras-primary">{table.name}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-[10px] font-mono text-aras-primary/40 truncate max-w-md italic">
                      {table.columns}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-[9px] font-bold uppercase tracking-widest text-aras-accent hover:text-aras-primary transition-all opacity-0 group-hover:opacity-100">
                      View Schema
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

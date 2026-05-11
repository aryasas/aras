import React, { useState, useEffect } from 'react'

export default function TrashPage() {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [inspectingGroup, setInspectingGroup] = useState(null)
  const [snapshot, setSnapshot] = useState(null)

  useEffect(() => {
    fetchGroups()
  }, [])

  const fetchGroups = async () => {
    setLoading(true)
    try {
      const response = await fetch('/admin/api/trash/groups') // I might need to create this
      const data = await response.json()
      setGroups(data.groups || [])
    } catch (err) {
      console.error('Failed to fetch trash groups:', err)
    } finally {
      setLoading(false)
    }
  }

  const inspectGroup = async (groupId) => {
    try {
      const data = await fetch(`/admin/trash/${groupId}/inspect/`).then(r => r.json())
      setInspectingGroup({ id: groupId, docs: data.docs })
    } catch (err) {
      alert('Failed to inspect group')
    }
  }

  const viewSnapshot = async (docId) => {
    try {
      const data = await fetch(`/admin/trash/doc/${docId}/`).then(r => r.json())
      setSnapshot(data)
    } catch (err) {
      alert('Failed to load snapshot')
    }
  }

  const restoreGroup = async (groupId) => {
    if (!confirm('Restore this group of records?')) return
    try {
      const response = await fetch(`/admin/trash/${groupId}/restore/`, { method: 'POST' })
      if (response.ok) {
        fetchGroups()
      }
    } catch (err) {
      alert('Restore failed')
    }
  }

  const deletePermanently = async (groupId) => {
    if (!confirm('Permanently delete this group? This cannot be undone.')) return
    try {
      const response = await fetch(`/admin/trash/${groupId}/permanent-delete/`, { method: 'POST' })
      if (response.ok) {
        fetchGroups()
      }
    } catch (err) {
      alert('Delete failed')
    }
  }

  return (
    <div className="space-y-6 animate-fade-in pb-20">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-studio-serif font-bold text-aras-primary tracking-tight flex items-center gap-3">
             <i className="fa fa-trash text-red-500 opacity-50"></i> Trash
          </h2>
          <p className="text-[11px] text-[#9aacb8] font-studio-serif italic">Deleted documents — restore or permanently delete.</p>
        </div>
        <div className="flex gap-2">
           <button className="px-4 py-2 border border-[#dde3e7] text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest rounded hover:bg-[#faf8f3]">
              Restore All
           </button>
           <button className="px-4 py-2 border border-red-200 text-[10px] font-bold text-red-500 uppercase tracking-widest rounded hover:bg-red-50">
              Empty Trash
           </button>
        </div>
      </div>

      <div className="bg-white border border-[#dde3e7] rounded-md shadow-sm overflow-hidden">
        <table className="w-full text-[13px]">
          <thead className="bg-[#faf8f3] border-b border-[#dde3e7]">
            <tr>
              <th className="px-6 py-4 text-left text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest">Document</th>
              <th className="px-6 py-4 text-left text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest">Type</th>
              <th className="px-6 py-4 text-center text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest">Records</th>
              <th className="px-6 py-4 text-left text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest">Deleted At</th>
              <th className="px-6 py-4 text-right text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#f4f2ee]">
            {groups.map((g, i) => (
              <tr key={i} className="hover:bg-[#faf8f3]/30 transition-colors">
                <td className="px-6 py-4">
                  {g.root ? (
                    <button onClick={() => viewSnapshot(g.root.id)} className="text-aras-accent hover:underline font-bold font-studio-serif">
                      {g.root.doc_type} #{g.root.doc_id}
                    </button>
                  ) : '—'}
                </td>
                <td className="px-6 py-4">
                   <span className="px-2 py-0.5 bg-[#f4f2ee] text-[10px] font-bold text-[#9aacb8] rounded uppercase tracking-wider border border-[#dde3e7]">
                      {g.root?.doc_type || '—'}
                   </span>
                </td>
                <td className="px-6 py-4 text-center font-bold text-aras-primary">{g.doc_count}</td>
                <td className="px-6 py-4 text-[#9aacb8]">{g.deleted_at}</td>
                <td className="px-6 py-4 text-right space-x-2">
                   <button 
                    onClick={() => inspectGroup(g.group_id)}
                    className="p-2 text-aras-accent hover:bg-aras-accent/5 rounded transition-colors"
                    title="Inspect"
                   >
                      <i className="fa fa-search-plus"></i>
                   </button>
                   <button 
                    onClick={() => restoreGroup(g.group_id)}
                    className="p-2 text-green-600 hover:bg-green-50 rounded transition-colors"
                    title="Restore"
                   >
                      <i className="fa fa-undo"></i>
                   </button>
                   <button 
                    onClick={() => deletePermanently(g.group_id)}
                    className="p-2 text-red-500 hover:bg-red-50 rounded transition-colors"
                    title="Delete Permanently"
                   >
                      <i className="fa fa-times"></i>
                   </button>
                </td>
              </tr>
            ))}
            {!loading && groups.length === 0 && (
              <tr>
                <td colSpan="5" className="px-6 py-20 text-center">
                   <div className="w-16 h-16 bg-[#faf8f3] rounded-full flex items-center justify-center text-[#dde3e7] mx-auto mb-4">
                      <i className="fa fa-trash-o text-3xl"></i>
                   </div>
                   <p className="text-[#9aacb8] font-studio-serif italic">Trash is empty.</p>
                </td>
              </tr>
            )}
            {loading && (
               <tr>
                  <td colSpan="5" className="px-6 py-20 text-center">
                     <div className="w-8 h-8 border-2 border-aras-accent border-t-transparent rounded-full animate-spin mx-auto"></div>
                  </td>
               </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* INSPECT MODAL */}
      {inspectingGroup && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-aras-primary/20 backdrop-blur-sm animate-fade-in">
           <div className="bg-white border border-[#dde3e7] rounded-md shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[80vh]">
              <div className="px-6 py-4 bg-[#faf8f3] border-b border-[#dde3e7] flex items-center justify-between">
                 <h3 className="text-[12px] font-bold text-aras-primary uppercase tracking-[0.1em]">Group Contents</h3>
                 <button onClick={() => setInspectingGroup(null)} className="text-[#9aacb8] hover:text-aras-primary transition-colors">
                    <i className="fa fa-times"></i>
                 </button>
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                 <ul className="space-y-3">
                    {inspectingGroup.docs.map(d => (
                      <li key={d.id} className="flex items-center gap-3 text-sm p-3 bg-[#faf8f3] rounded border border-[#dde3e7]">
                         <i className="fa fa-file-text-o text-[#9aacb8]"></i>
                         <div className="flex-1">
                            <span className="font-bold text-aras-primary">{d.doc_type}</span>
                            <span className="text-[#9aacb8] ml-2">#{d.doc_id}</span>
                         </div>
                         <button onClick={() => viewSnapshot(d.id)} className="text-[10px] font-bold text-aras-accent uppercase hover:underline">View Snapshot</button>
                      </li>
                    ))}
                 </ul>
              </div>
              <div className="px-6 py-4 bg-[#faf8f3] border-t border-[#dde3e7] flex justify-end gap-2">
                 <button 
                  onClick={() => restoreGroup(inspectingGroup.id)}
                  className="px-6 py-2 bg-aras-accent text-white text-[11px] font-bold uppercase tracking-widest rounded shadow-sm hover:bg-aras-accent/90"
                 >
                    Restore All
                 </button>
              </div>
           </div>
        </div>
      )}

      {/* SNAPSHOT MODAL */}
      {snapshot && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-6 bg-aras-primary/40 backdrop-blur-md animate-fade-in">
           <div className="bg-white border border-[#dde3e7] rounded-md shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[85vh]">
              <div className="px-6 py-4 bg-[#faf8f3] border-b border-[#dde3e7] flex items-center justify-between">
                 <h3 className="text-[12px] font-bold text-aras-primary uppercase tracking-[0.1em]">Document Snapshot</h3>
                 <button onClick={() => setSnapshot(null)} className="text-[#9aacb8] hover:text-aras-primary transition-colors">
                    <i className="fa fa-times"></i>
                 </button>
              </div>
              <div className="flex-1 overflow-y-auto p-8">
                 <div className="mb-6 pb-6 border-b border-[#f4f2ee]">
                    <div className="text-[9px] font-bold text-[#9aacb8] uppercase tracking-widest mb-1">Type & ID</div>
                    <div className="text-xl font-studio-serif font-bold text-aras-primary">{snapshot.doc_type} #{snapshot.doc_id}</div>
                    <div className="text-[11px] text-[#9aacb8] mt-2">Deleted at: {snapshot.deleted_at}</div>
                 </div>
                 
                 <div className="grid grid-cols-1 gap-4 font-mono text-xs">
                    {Object.entries(snapshot.data || {}).map(([k, v]) => (
                       <div key={k} className="flex border-b border-[#f4f2ee] pb-2">
                          <span className="w-32 flex-shrink-0 text-[#9aacb8]">{k}</span>
                          <span className="text-aras-primary break-all">{String(v)}</span>
                       </div>
                    ))}
                 </div>
              </div>
              <div className="px-6 py-4 bg-[#faf8f3] border-t border-[#dde3e7] flex justify-end">
                 <button 
                  onClick={() => setSnapshot(null)}
                  className="px-6 py-2 border border-[#dde3e7] text-aras-primary text-[11px] font-bold uppercase tracking-widest rounded"
                 >
                    Close
                 </button>
              </div>
           </div>
        </div>
      )}
    </div>
  )
}

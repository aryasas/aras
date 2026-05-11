import React, { useState } from 'react'
import ArasSearchableSelect from './ArasSearchableSelect'

/**
 * ArasChildTable - Dynamic inline grid for relational data (e.g. Invoice Items).
 * Features: Inline display, Row Edit Modal, and Actions.
 */
export default function ArasChildTable({ title, columns = [], data = [], onChange }) {
  const rows = data || []
  const [editingIndex, setEditingIndex] = useState(null)
  const [editBuffer, setEditBuffer] = useState(null)

  const openEditModal = (index, row) => {
    setEditingIndex(index)
    setEditBuffer({ ...row })
  }

  const addRow = () => {
    const newRow = {}
    columns.forEach(col => { newRow[col.name] = '' })
    const updated = [...rows, newRow]
    onChange?.(updated)
    // Automatically open edit modal for new row
    openEditModal(rows.length, newRow)
  }

  const removeRow = (index) => {
    const updated = rows.filter((_, i) => i !== index)
    onChange?.(updated)
  }

  const updateCell = (index, field, value) => {
    const updated = rows.map((row, i) => i === index ? { ...row, [field]: value } : row)
    onChange?.(updated)
  }

  const saveEditModal = () => {
    const updated = rows.map((row, i) => i === editingIndex ? editBuffer : row)
    onChange?.(updated)
    setEditingIndex(null)
    setEditBuffer(null)
  }

  const updateBuffer = (field, value) => {
    setEditBuffer(prev => ({ ...prev, [field]: value }))
  }

  const isSelect = (col) => col.type === 'select' || col.type === 'relation'

  return (
    <div className="mt-12 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-[16px] font-studio-serif font-bold text-aras-primary">{title}</h3>
        <button 
          type="button"
          onClick={addRow}
          className="px-4 py-2 bg-[#f4f2ee] border border-[#dde3e7] text-[10px] font-bold text-aras-primary uppercase tracking-widest rounded-md hover:bg-[#eef0f2] transition-all flex items-center gap-2"
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M12 4v16m8-8H4"/></svg>
          Add Entry
        </button>
      </div>

      <div className="overflow-x-auto border border-[#dde3e7] rounded-md bg-white shadow-sm">
        <table className="w-full text-left border-collapse min-w-[800px]">
          <thead>
            <tr className="bg-[#faf8f3] border-b border-[#dde3e7]">
              <th className="px-6 py-4 text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest w-12">#</th>
              {columns.map(col => (
                <th key={col.name} className="px-6 py-4 text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest">
                  {col.label || col.name}
                </th>
              ))}
              <th className="px-6 py-4 text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest w-24 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#eef0f2]">
            {rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 2} className="px-6 py-12 text-center text-[#9aacb8] font-studio-serif italic">
                  No records found in this ledger section.
                </td>
              </tr>
            ) : (
              rows.map((row, idx) => (
                <tr key={idx} className="hover:bg-[#faf8f3]/50 transition-colors group">
                  <td className="px-6 py-4 text-[11px] font-mono text-[#9aacb8]">{idx + 1}</td>
                  {columns.map(col => (
                    <td key={col.name} className="px-4 py-2">
                      {isSelect(col) ? (
                        <ArasSearchableSelect
                          value={row[col.name]}
                          onChange={(val) => updateCell(idx, col.name, val)}
                          options={col.fk_options || []}
                          addUrl={col.rel_add_url}
                          placeholder={`Select ${col.label?.toLowerCase() ?? col.name}…`}
                        />
                      ) : (
                        <input 
                          type={col.type === 'number' ? 'number' : (col.type === 'date' ? 'date' : (col.type === 'datetime' ? 'datetime-local' : 'text'))}
                          value={row[col.name] ?? ''}
                          onChange={(e) => updateCell(idx, col.name, e.target.value)}
                          placeholder={`Enter ${col.label?.toLowerCase() ?? col.name}…`}
                          className="w-full bg-transparent border-none focus:ring-1 focus:ring-aras-accent rounded px-2 py-1.5 text-[13px] font-studio-sans text-aras-primary placeholder:text-[#dde3e7] transition-all"
                        />
                      )}
                    </td>
                  ))}
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button 
                        type="button"
                        onClick={() => openEditModal(idx, row)}
                        className="text-[#9aacb8] hover:text-aras-accent transition-colors"
                        title="Edit Details"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>
                      </button>
                      <button 
                        type="button"
                        onClick={() => removeRow(idx)}
                        className="text-[#9aacb8] hover:text-aras-error transition-colors"
                        title="Remove Row"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* EDIT MODAL */}
      {editingIndex !== null && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-[#0f1b2d]/40 backdrop-blur-sm animate-fade-in">
          <div className="bg-white border border-[#dde3e7] rounded-md shadow-2xl w-full max-w-2xl overflow-hidden animate-slide-up">
            <div className="h-1 bg-aras-accent w-full"></div>
            <div className="p-8">
              <div className="flex items-center justify-between mb-8">
                <div>
                  <span className="text-[10px] font-bold text-[#c9a568] uppercase tracking-widest block mb-1">Detailed Editor</span>
                  <h4 className="text-[20px] font-studio-serif font-bold text-aras-primary">Edit Row #{editingIndex + 1}</h4>
                </div>
                <button onClick={() => setEditingIndex(null)} className="text-[#9aacb8] hover:text-aras-primary transition-colors">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
                {columns.map(col => (
                  <div key={col.name} className="flex flex-col gap-2">
                    <label className="text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest">{col.label || col.name}</label>
                    {isSelect(col) ? (
                      <ArasSearchableSelect
                        value={editBuffer[col.name]}
                        onChange={(val) => updateBuffer(col.name, val)}
                        options={col.fk_options || []}
                        addUrl={col.rel_add_url}
                        placeholder={`Select ${col.label?.toLowerCase() ?? col.name}…`}
                        className="w-full"
                      />
                    ) : (
                      <input
                        type={col.type === 'number' ? 'number' : (col.type === 'date' ? 'date' : (col.type === 'datetime' ? 'datetime-local' : 'text'))}
                        value={editBuffer[col.name] ?? ''}
                        onChange={(e) => updateBuffer(col.name, e.target.value)}
                        placeholder={`Enter ${col.label?.toLowerCase() ?? col.name}…`}
                        className="w-full bg-[#fcfcfb] border border-[#dde3e7] rounded-md px-4 py-2.5 text-[14px] text-aras-primary font-studio-sans focus:outline-none focus:border-aras-accent focus:ring-1 focus:ring-aras-accent transition-all shadow-inner aras-engraved"
                      />
                    )}
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-end gap-4 border-t border-[#eef0f2] pt-8">
                <button 
                  type="button"
                  onClick={() => setEditingIndex(null)}
                  className="px-6 py-2.5 text-[11px] font-bold text-[#9aacb8] uppercase tracking-widest hover:text-aras-primary transition-colors"
                >
                  Cancel
                </button>
                <button 
                  type="button"
                  onClick={saveEditModal}
                  className="px-8 py-2.5 bg-aras-primary text-white text-[11px] font-bold uppercase tracking-widest rounded-md shadow-lg hover:bg-[#1a2d46] transition-all"
                >
                  Update Entry
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <div className="mt-4 p-4 bg-[#faf8f3] border border-[#dde3e7] border-dashed rounded-md flex justify-end gap-12">
          <div className="text-right">
            <span className="block text-[9px] font-bold text-[#9aacb8] uppercase tracking-widest">Total Rows</span>
            <span className="text-[14px] font-studio-serif font-bold text-aras-primary">{rows.length} Items</span>
          </div>
      </div>
    </div>
  )
}

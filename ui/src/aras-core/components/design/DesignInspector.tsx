import React, { useState } from 'react'
import { useUIStore } from '../../../store/uiStore'
import type { CustomElementDef } from '../../../store/uiStore'
import { X, Settings2, Save, Type, Square, Minus, LayoutTemplate, Trash2 } from 'lucide-react'
import api from '../../../lib/api'
import { useAras } from '../../hooks/useAras'
import { useLocation } from 'react-router-dom'

export const DesignInspector: React.FC = () => {
  const { designMode, activeElementId, setActiveDesignElement, designData, updateElementStyle, toggleDesignMode, addCustomElement, removeCustomElement } = useUIStore()
  const { notify } = useAras()
  const location = useLocation()
  const [activeTab, setActiveTab] = useState<'styles' | 'add'>('styles')

  if (!designMode) return null

  const handleSave = async () => {
    try {
      const templateName = location.pathname
      const checkRes = await api.get(`/dev/dev_template_annotations?template_name=${templateName}`)
      const payload: any = {
        template_name: templateName,
        sections: [], // Legacy compat
        author: 'live-designer'
      }
      
      payload.sections = [{ id: '__designData__', data: designData }]

      if (checkRes.data.items?.length > 0) {
        await api.patch(`/dev/dev_template_annotations/${checkRes.data.items[0].id}`, payload)
      } else {
        await api.post('/dev/dev_template_annotations', payload)
      }
      notify('Page design saved', 'success')
    } catch (err) {
      notify('Failed to save design', 'error')
    }
  }

  // To support dropping from palette, we need to listen for 'application/json' in DesignContainer.
  // We'll just patch DesignContainer handleDrop in a separate call if needed, or we can pre-create it here.
  const handleDragStartPrecreate = (e: React.DragEvent, type: CustomElementDef['type']) => {
    const newId = `custom-${type}-${Date.now()}`
    addCustomElement({
      id: newId,
      type,
      parentId: 'root', // Will be re-assigned by the container drop, but we don't have container drop changing parentId yet.
      content: type === 'text' ? 'New Text Block' : type === 'button' ? 'New Button' : ''
    })
    e.dataTransfer.setData('text/plain', newId)
  }

  const handleDelete = () => {
    if (activeElementId) {
      removeCustomElement(activeElementId)
      setActiveDesignElement(null)
    }
  }

  return (
    <div className="w-80 flex-shrink-0 bg-white border-l border-slate-200 h-full flex flex-col shadow-2xl z-50 sticky top-0">
      <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
        <div className="flex items-center gap-2">
          <Settings2 size={18} className="text-pink-600" />
          <h3 className="font-black text-sm text-slate-900 uppercase tracking-widest">Design Mode</h3>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleSave} className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded" title="Save Layout">
            <Save size={16} />
          </button>
          <button onClick={toggleDesignMode} className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded">
            <X size={16} />
          </button>
        </div>
      </div>

      <div className="flex border-b border-slate-200">
        <button 
          onClick={() => setActiveTab('styles')} 
          className={`flex-1 py-2.5 text-xs font-black uppercase tracking-widest transition-colors ${activeTab === 'styles' ? 'text-pink-600 border-b-2 border-pink-600 bg-pink-50/50' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600'}`}
        >
          Properties
        </button>
        <button 
          onClick={() => setActiveTab('add')} 
          className={`flex-1 py-2.5 text-xs font-black uppercase tracking-widest transition-colors ${activeTab === 'add' ? 'text-pink-600 border-b-2 border-pink-600 bg-pink-50/50' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600'}`}
        >
          Add Elements
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'add' && (
          <div className="space-y-4 animate-in fade-in zoom-in-95 duration-200">
            <p className="text-xs text-slate-500 mb-4">Drag elements into any dashed container on the page.</p>
            
            <div className="grid grid-cols-2 gap-3">
              <div draggable onDragStart={(e) => handleDragStartPrecreate(e, 'text')} className="flex flex-col items-center justify-center gap-2 p-4 bg-slate-50 border border-slate-200 rounded-xl cursor-grab hover:border-pink-300 hover:text-pink-600 transition-colors group">
                <Type size={20} className="text-slate-400 group-hover:text-pink-500" />
                <span className="text-[10px] font-bold">Text Block</span>
              </div>
              <div draggable onDragStart={(e) => handleDragStartPrecreate(e, 'button')} className="flex flex-col items-center justify-center gap-2 p-4 bg-slate-50 border border-slate-200 rounded-xl cursor-grab hover:border-pink-300 hover:text-pink-600 transition-colors group">
                <Square size={20} className="text-slate-400 group-hover:text-pink-500" />
                <span className="text-[10px] font-bold">Button</span>
              </div>
              <div draggable onDragStart={(e) => handleDragStartPrecreate(e, 'divider')} className="flex flex-col items-center justify-center gap-2 p-4 bg-slate-50 border border-slate-200 rounded-xl cursor-grab hover:border-pink-300 hover:text-pink-600 transition-colors group">
                <Minus size={20} className="text-slate-400 group-hover:text-pink-500" />
                <span className="text-[10px] font-bold">Divider</span>
              </div>
              <div draggable onDragStart={(e) => handleDragStartPrecreate(e, 'container')} className="flex flex-col items-center justify-center gap-2 p-4 bg-slate-50 border border-slate-200 rounded-xl cursor-grab hover:border-pink-300 hover:text-pink-600 transition-colors group">
                <LayoutTemplate size={20} className="text-slate-400 group-hover:text-pink-500" />
                <span className="text-[10px] font-bold">Container</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'styles' && !activeElementId && (
          <div className="text-center text-slate-400 mt-10">
            <div className="inline-block p-4 bg-slate-50 rounded-full mb-4 border border-dashed border-slate-200">
              <Settings2 size={24} />
            </div>
            <p className="font-bold text-sm">Select an element<br/>on the page to edit.</p>
          </div>
        )}

        {activeTab === 'styles' && activeElementId && (
          <div className="space-y-6 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <span className="text-[10px] font-black uppercase text-pink-600 tracking-widest bg-pink-50 px-2 py-1 rounded">
                Editing: {activeElementId}
              </span>
              {activeElementId.startsWith('custom-') && (
                <button onClick={handleDelete} className="p-1.5 text-rose-500 hover:bg-rose-50 rounded" title="Delete Element">
                  <Trash2 size={14} />
                </button>
              )}
            </div>

            {(() => {
              const styles = designData.styles[activeElementId] || {}
              const updateStyle = (key: string, value: string) => updateElementStyle(activeElementId, { [key]: value })

              const InputField = ({ label, field, placeholder }: { label: string, field: string, placeholder: string }) => (
                <div className="mb-4">
                  <label className="block text-[10px] font-black uppercase text-slate-500 mb-1.5 tracking-widest">{label}</label>
                  <input
                    type="text"
                    value={styles[field] || ''}
                    onChange={(e) => updateStyle(field, e.target.value)}
                    placeholder={placeholder}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 focus:ring-2 focus:ring-pink-500 transition-all outline-none"
                  />
                </div>
              )

              return (
                <>
                  <div>
                    <h4 className="text-xs font-bold text-slate-800 mb-3">Layout & Spacing</h4>
                    <InputField label="Margin Top" field="marginTop" placeholder="e.g., 2rem, 32px" />
                    <InputField label="Margin Bottom" field="marginBottom" placeholder="e.g., 2rem, 32px" />
                    <InputField label="Padding Top" field="paddingTop" placeholder="e.g., 1rem, 16px" />
                    <InputField label="Padding Bottom" field="paddingBottom" placeholder="e.g., 1rem, 16px" />
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-slate-800 mb-3 border-t border-slate-100 pt-4">Appearance</h4>
                    <div className="mb-4">
                      <label className="block text-[10px] font-black uppercase text-slate-500 mb-1.5 tracking-widest">Text Align</label>
                      <select 
                        value={styles.textAlign || ''} 
                        onChange={(e) => updateStyle('textAlign', e.target.value)}
                        className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 focus:ring-2 focus:ring-pink-500 outline-none"
                      >
                        <option value="">Default</option>
                        <option value="left">Left</option>
                        <option value="center">Center</option>
                        <option value="right">Right</option>
                        <option value="justify">Justify</option>
                      </select>
                    </div>
                    <InputField label="Background Color" field="backgroundColor" placeholder="e.g., #ffffff, var(--app-bg)" />
                    <InputField label="Text Color" field="textColor" placeholder="e.g., #333333, var(--app-text)" />
                    <InputField label="Border" field="border" placeholder="e.g., 1px solid #e2e8f0" />
                    <InputField label="Border Radius" field="borderRadius" placeholder="e.g., 0.5rem, 8px" />
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-slate-800 mb-3 border-t border-slate-100 pt-4">Advanced</h4>
                    <InputField label="Custom CSS Classes" field="customClasses" placeholder="e.g., shadow-lg hover:bg-slate-50" />
                  </div>
                </>
              )
            })()}
          </div>
        )}
      </div>
    </div>
  )
}

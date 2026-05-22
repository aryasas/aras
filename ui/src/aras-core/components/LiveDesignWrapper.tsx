import React, { useState, useEffect } from 'react'
import { GripVertical, Edit3, Save, Eye, EyeOff, Layout } from 'lucide-react'
import { useUIStore } from '../../store/uiStore'
import api from '../../lib/api'
import { useAras } from '../hooks/useAras'
import type { TemplateSection } from '../../views/TemplateBuilder'

interface LiveDesignWrapperProps {
  templateName: string
  children: (orderedSections: TemplateSection[]) => React.ReactNode
}

export const LiveDesignWrapper: React.FC<LiveDesignWrapperProps> = ({ templateName, children }) => {
  const { templateBuilderEnabled } = useUIStore()
  const { notify } = useAras()
  const [sections, setSections] = useState<TemplateSection[]>([])
  const [loading, setLoading] = useState(true)
  const [dragId, setDragId] = useState<string | null>(null)
  const [dragOverId, setDragOverId] = useState<string | null>(null)
  const [editingCommentId, setEditingCommentId] = useState<string | null>(null)

  useEffect(() => {
    const fetchTemplate = async () => {
      try {
        const res = await api.get(`/dev/dev_template_annotations?template_name=${templateName}`)
        if (res.data.items?.length > 0) {
          setSections(res.data.items[0].sections.sort((a: any, b: any) => a.order - b.order))
        }
      } catch (err) {
        console.warn('LiveDesign: No template found for', templateName)
      } finally {
        setLoading(false)
      }
    }
    fetchTemplate()
  }, [templateName])

  const handleSave = async () => {
    try {
      const checkRes = await api.get(`/dev/dev_template_annotations?template_name=${templateName}`)
      const payload = {
        template_name: templateName,
        sections: sections,
        author: 'live-designer'
      }
      
      if (checkRes.data.items?.length > 0) {
        await api.patch(`/dev/dev_template_annotations/${checkRes.data.items[0].id}`, payload)
      } else {
        await api.post('/dev/dev_template_annotations', payload)
      }
      notify('Design saved to registry', 'success')
    } catch (err) {
      notify('Failed to save design', 'error')
    }
  }

  const handleToggleVisibility = (id: string) => {
    setSections(prev => prev.map(s => s.id === id ? { ...s, visible: !s.visible } : s))
  }

  const handleCommentChange = (id: string, comment: string) => {
    setSections(prev => prev.map(s => s.id === id ? { ...s, comment } : s))
  }

  const onDragStart = (id: string) => setDragId(id)
  const onDragOver = (e: React.DragEvent, id: string) => {
    e.preventDefault()
    setDragOverId(id)
  }
  const onDrop = (id: string) => {
    if (!dragId || dragId === id) return
    const fromIdx = sections.findIndex(s => s.id === dragId)
    const toIdx = sections.findIndex(s => s.id === id)
    const reordered = [...sections]
    const [moved] = reordered.splice(fromIdx, 1)
    reordered.splice(toIdx, 0, moved)
    setSections(reordered.map((s, i) => ({ ...s, order: i })))
    setDragId(null)
    setDragOverId(null)
  }

  if (!templateBuilderEnabled && sections.length === 0) {
    return <>{children([])}</>
  }

  // Map out sections in non-builder mode, but still apply custom styles!
  if (!templateBuilderEnabled) {
    return (
      <div className="flex-1 flex flex-col items-stretch w-full min-w-0">
        {sections.map((section) => {
          if (!section.visible) return null;
          return (
            <div
              key={section.id}
              className={`w-full ${section.styles?.customClasses || ''}`}
              style={{
                marginTop: section.styles?.marginTop,
                marginBottom: section.styles?.marginBottom,
                paddingTop: section.styles?.paddingTop,
                paddingBottom: section.styles?.paddingBottom,
                textAlign: section.styles?.textAlign as any,
                backgroundColor: section.styles?.backgroundColor,
                color: section.styles?.textColor,
                border: section.styles?.border,
                borderRadius: section.styles?.borderRadius,
              }}
            >
              {children([section])}
            </div>
          )
        })}
      </div>
    )
  }

  if (loading) {
    return <div className="p-8 text-center text-pink-500 animate-pulse font-black uppercase tracking-widest text-[10px]">Loading {templateName} Template...</div>
  }

  if (sections.length === 0) {
    return (
      <div className="relative border-2 border-dashed border-pink-500/10 rounded-2xl p-4">
        <div className="absolute -top-3 left-4 z-50 flex items-center gap-2 bg-pink-600 text-white px-3 py-1 rounded-full shadow-lg text-[9px] font-black uppercase tracking-widest">
          <span>Design: {templateName} (Blank)</span>
          <button onClick={() => setSections([
            { id: 'toolbar', name: 'Toolbar', visible: true, comment: '', order: 0, styles: {} },
            { id: 'filter-bar', name: 'Filter Bar', visible: true, comment: '', order: 1, styles: {} },
            { id: 'table-header', name: 'Data Table', visible: true, comment: '', order: 2, styles: {} },
            { id: 'pagination', name: 'Pagination', visible: true, comment: '', order: 3, styles: {} },
          ])} className="ml-2 bg-white/20 hover:bg-white/40 p-1 rounded transition-colors" title="Initialize">
            <Edit3 size={10} />
          </button>
        </div>
        {children([])}
      </div>
    )
  }

  return (
    <div className="relative group/canvas flex flex-col h-full w-full">
      <div className="absolute -top-3 left-4 z-50 flex items-center gap-2 bg-pink-600 text-white px-3 py-1 rounded-full shadow-lg text-[9px] font-black uppercase tracking-widest pointer-events-none">
        <Layout size={10} />
        <span>Design: {templateName}</span>
        <button onClick={handleSave} className="ml-2 bg-white/20 hover:bg-white/40 p-1 rounded transition-colors pointer-events-auto" title="Save changes">
          <Save size={10} />
        </button>
      </div>

      <div className="flex-1 flex flex-col items-stretch gap-2 min-w-0">
        {sections.map((section) => (
          <div
            key={section.id}
            draggable
            onDragStart={() => onDragStart(section.id)}
            onDragOver={(e) => onDragOver(e, section.id)}
            onDrop={() => onDrop(section.id)}
            className={`
              relative group/item transition-all duration-300 w-full
              ${!section.visible ? 'opacity-30 grayscale' : ''}
              ${dragId === section.id ? 'opacity-10 scale-[0.98]' : ''}
              ${dragOverId === section.id ? 'border-t-2 border-pink-500 pt-1' : ''}
              ${section.styles?.customClasses || ''}
            `}
            style={{
              marginTop: section.styles?.marginTop,
              marginBottom: section.styles?.marginBottom,
              paddingTop: section.styles?.paddingTop,
              paddingBottom: section.styles?.paddingBottom,
              textAlign: section.styles?.textAlign as any,
              backgroundColor: section.styles?.backgroundColor,
              color: section.styles?.textColor,
              border: section.styles?.border,
              borderRadius: section.styles?.borderRadius,
            }}
          >
            {/* Design Controls Overlay (Horizontal) */}
            <div className="absolute -top-6 left-0 right-0 h-6 flex items-center justify-center gap-1 opacity-0 group-hover/item:opacity-100 transition-opacity z-50 pointer-events-none">
              <div className="p-0.5 bg-pink-500 text-white rounded cursor-grab active:cursor-grabbing shadow-md pointer-events-auto">
                <GripVertical size={10} />
              </div>
               <button 
                  onClick={() => handleToggleVisibility(section.id)}
                  className={`p-0.5 rounded shadow-md pointer-events-auto ${section.visible ? 'bg-white text-slate-400 hover:text-indigo-600' : 'bg-indigo-600 text-white'}`}
               >
                  {section.visible ? <Eye size={10} /> : <EyeOff size={10} />}
               </button>
               <button 
                  onClick={() => setEditingCommentId(editingCommentId === section.id ? null : section.id)}
                  className={`p-0.5 rounded shadow-md pointer-events-auto ${section.comment ? 'bg-pink-600 text-white' : 'bg-white text-slate-400 hover:text-pink-600'}`}
               >
                  <Edit3 size={10} />
               </button>
            </div>

            {/* Comment Bubble (Tooltip style) */}
            {(editingCommentId === section.id || (section.comment && templateBuilderEnabled)) && (
              <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-6 z-[60] animate-in fade-in zoom-in-95 w-48">
                 <div className="bg-pink-600 text-white p-2 rounded-xl shadow-xl text-[10px] font-medium relative text-center">
                    {editingCommentId === section.id ? (
                       <textarea 
                          autoFocus
                          value={section.comment}
                          onChange={(e) => handleCommentChange(section.id, e.target.value)}
                          onBlur={() => setEditingCommentId(null)}
                          placeholder="Tell AI..."
                          className="w-full bg-transparent border-none outline-none text-white placeholder:text-pink-200 resize-none h-12"
                       />
                    ) : (
                       <p>{section.comment}</p>
                    )}
                    <div className="absolute left-1/2 -translate-x-1/2 -bottom-1 w-2 h-2 bg-pink-600 rotate-45 rounded-sm"></div>
                 </div>
              </div>
            )}

            <div className={`
               transition-all w-full h-full
               ${templateBuilderEnabled ? 'border border-dashed border-pink-500/10 hover:border-pink-500/40 rounded-lg p-0.5' : ''}
            `}>
               {children([section])}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

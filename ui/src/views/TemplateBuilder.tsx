import { useState, useEffect, useRef } from 'react'
import ReactDOM from 'react-dom'
import { GripVertical, Eye, EyeOff, Layout, Download, Upload, Plus, Trash2, Copy, ChevronUp, ChevronDown, Save, X, Settings2 } from 'lucide-react'
import { useUIStore } from '../store/uiStore'
import { useAras } from '../aras-core/hooks/useAras'
import api from '../lib/api'

export interface TemplateSectionStyles {
  marginTop?: string
  marginBottom?: string
  paddingTop?: string
  paddingBottom?: string
  textAlign?: 'left' | 'center' | 'right' | 'justify' | ''
  backgroundColor?: string
  textColor?: string
  customClasses?: string
  border?: string
  borderRadius?: string
}

export interface TemplateSection {
  id: string
  name: string
  comment: string   // AI annotation
  visible: boolean
  order: number
  styles?: TemplateSectionStyles
}

const TEMPLATE_PRESETS: Record<string, Omit<TemplateSection, 'order'>[]> = {
  Home: [
    { id: 'hero', name: 'Hero Banner', comment: '', visible: true },
    { id: 'quick-actions', name: 'Quick Actions', comment: '', visible: true },
    { id: 'recent-activity', name: 'Recent Activity', comment: '', visible: true },
    { id: 'stats', name: 'Stats Cards', comment: '', visible: true },
  ],
  DynamicForm: [
    { id: 'form-header', name: 'Form Header', comment: '', visible: true },
    { id: 'fields-area', name: 'Fields Area', comment: '', visible: true },
    { id: 'child-tables', name: 'Child Tables', comment: '', visible: true },
    { id: 'action-bar', name: 'Action Bar', comment: '', visible: true },
  ],
  ListView: [
    { id: 'toolbar', name: 'Toolbar', comment: '', visible: true },
    { id: 'filter-bar', name: 'Filter Bar', comment: '', visible: true },
    { id: 'table-header', name: 'Table Header', comment: '', visible: true },
    { id: 'table-rows', name: 'Table Rows', comment: '', visible: true },
    { id: 'pagination', name: 'Pagination', comment: '', visible: true },
  ],
  DevTools: [
    { id: 'tab-bar', name: 'Tab Bar', comment: '', visible: true },
    { id: 'overview-panel', name: 'Overview Panel', comment: '', visible: true },
    { id: 'handoff-panel', name: 'Handoff Panel', comment: '', visible: true },
  ],
  AppManager: [
    { id: 'app-grid', name: 'App Grid', comment: '', visible: true },
    { id: 'app-detail', name: 'App Detail', comment: '', visible: true },
  ],
  ReportCenter: [
    { id: 'filter-section', name: 'Filter Section', comment: '', visible: true },
    { id: 'chart-area', name: 'Chart Area', comment: '', visible: true },
    { id: 'table-section', name: 'Data Table', comment: '', visible: true },
  ],
}

export default function TemplateBuilder({ forcedTemplate, isPanel }: { forcedTemplate?: string, isPanel?: boolean }) {
  const [sections, setSections] = useState<TemplateSection[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string>(forcedTemplate || 'Home')
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; sectionId: string } | null>(null)
  const [dragOverId, setDragOverId] = useState<string | null>(null)
  const [dragId, setDragId] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const { templateBuilderEnabled, toggleTemplateBuilder, setPageTitle } = useUIStore()
  const { notify } = useAras()
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setPageTitle('Template Builder', 'Visual layout editor with AI section annotations and detailed styling.', 'DEV / TOOLS')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  // Load from backend if exists, else preset
  const loadTemplate = async (name: string) => {
    try {
      const res = await api.get(`/dev/dev_template_annotations?template_name=${name}`)
      if (res.data.items && res.data.items.length > 0) {
        const data = res.data.items[0]
        setSections(data.sections.sort((a: any, b: any) => a.order - b.order))
      } else {
        const preset = TEMPLATE_PRESETS[name] ?? []
        setSections(preset.map((s, i) => ({ ...s, order: i })))
      }
    } catch (err) {
      const preset = TEMPLATE_PRESETS[name] ?? []
      setSections(preset.map((s, i) => ({ ...s, order: i })))
    }
  }

  useEffect(() => {
    if (templateBuilderEnabled) {
      loadTemplate(selectedTemplate)
      setActiveSectionId(null)
    }
  }, [selectedTemplate, templateBuilderEnabled])

  const handleSaveToBackend = async () => {
    setSaving(true)
    try {
      // Find if exists
      const checkRes = await api.get(`/dev/dev_template_annotations?template_name=${selectedTemplate}`)
      const payload = {
        template_name: selectedTemplate,
        sections: sections,
        author: 'system'
      }
      
      if (checkRes.data.items && checkRes.data.items.length > 0) {
        const id = checkRes.data.items[0].id
        await api.patch(`/dev/dev_template_annotations/${id}`, payload)
      } else {
        await api.post('/dev/dev_template_annotations', payload)
      }
      notify('Template saved to registry', 'success')
    } catch (err) {
      notify('Failed to save template', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleExport = () => {
    const data = {
      template: selectedTemplate,
      exported_at: new Date().toISOString(),
      sections: sections.map(s => ({
        id: s.id,
        name: s.name,
        visible: s.visible,
        order: s.order,
        ai_comment: s.comment,
        styles: s.styles
      }))
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `template_annotations_${selectedTemplate.toLowerCase()}_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      if (data.sections) {
        setSections(data.sections.map((s: any) => ({
          id: s.id,
          name: s.name,
          visible: s.visible,
          order: s.order,
          comment: s.ai_comment || '',
          styles: s.styles || {}
        })))
        notify('Imported successfully', 'success')
      }
    } catch (err) {
      notify('Failed to parse JSON', 'error')
    }
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const addSection = (afterId?: string) => {
    const newSection: TemplateSection = {
      id: `section-${Date.now()}`,
      name: 'New Section',
      comment: '',
      visible: true,
      order: sections.length,
      styles: {}
    }
    if (afterId) {
      const idx = sections.findIndex(s => s.id === afterId)
      const newSections = [...sections]
      newSections.splice(idx + 1, 0, newSection)
      setSections(newSections.map((s, i) => ({ ...s, order: i })))
    } else {
      setSections([...sections, newSection].map((s, i) => ({ ...s, order: i })))
    }
    setActiveSectionId(newSection.id)
  }

  const deleteSection = (id: string) => {
    if (activeSectionId === id) setActiveSectionId(null)
    setSections(sections.filter(s => s.id !== id).map((s, i) => ({ ...s, order: i })))
  }

  const duplicateSection = (id: string) => {
    const section = sections.find(s => s.id === id)
    if (!section) return
    const newSection = { ...section, id: `${section.id}-copy-${Date.now()}` }
    const idx = sections.findIndex(s => s.id === id)
    const newSections = [...sections]
    newSections.splice(idx + 1, 0, newSection)
    setSections(newSections.map((s, i) => ({ ...s, order: i })))
    setActiveSectionId(newSection.id)
  }

  const moveSection = (id: string, to: 'top' | 'bottom') => {
    const section = sections.find(s => s.id === id)
    if (!section) return
    const others = sections.filter(s => s.id !== id)
    if (to === 'top') {
      setSections([section, ...others].map((s, i) => ({ ...s, order: i })))
    } else {
      setSections([...others, section].map((s, i) => ({ ...s, order: i })))
    }
  }

  // Drag and Drop
  const onDragStart = (e: React.DragEvent, id: string) => {
    e.dataTransfer.effectAllowed = 'move'
    setDragId(id)
  }

  const onDragOver = (e: React.DragEvent, id: string) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverId(id)
  }

  const onDrop = (_e: React.DragEvent, id: string) => {
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

  useEffect(() => {
    const handleGlobalClick = () => setContextMenu(null)
    const handleEsc = (e: KeyboardEvent) => { if (e.key === 'Escape') setContextMenu(null) }
    window.addEventListener('mousedown', handleGlobalClick)
    window.addEventListener('keydown', handleEsc)
    return () => {
      window.removeEventListener('mousedown', handleGlobalClick)
      window.removeEventListener('keydown', handleEsc)
    }
  }, [])

  if (!templateBuilderEnabled) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center animate-in fade-in zoom-in duration-500">
        <div className="p-8 bg-slate-50 rounded-[3rem] border border-slate-200 shadow-sm flex flex-col items-center">
          <div className="p-6 bg-white shadow-xl shadow-indigo-100 rounded-3xl text-slate-300 mb-6">
            <Layout size={64} />
          </div>
          <h2 className="text-3xl font-black text-slate-900 mb-2">Template Builder</h2>
          <p className="text-slate-500 max-w-md mb-8 font-medium">
            Enable Template Builder to start editing layout sections visually and adding AI annotations.
          </p>
          <button
            onClick={toggleTemplateBuilder}
            className="px-8 py-4 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 transition-all shadow-xl shadow-indigo-200 active:scale-95"
          >
            Enable Template Builder
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex flex-col h-full bg-slate-50/50 relative overflow-hidden ${isPanel ? '' : '-m-8'}`}>
      {/* Toolbar */}
      <div className="sticky top-0 z-20 bg-white/80 backdrop-blur-xl border-b border-slate-200 px-8 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-6">
          {!forcedTemplate && (
            <div className="flex items-center gap-3">
              <div 
                onClick={toggleTemplateBuilder}
                className={`w-10 h-6 rounded-full p-1 cursor-pointer transition-colors duration-300 flex items-center ${templateBuilderEnabled ? 'bg-indigo-600' : 'bg-slate-300'}`}
              >
                <div className={`w-4 h-4 bg-white rounded-full shadow-sm transition-transform duration-300 ${templateBuilderEnabled ? 'translate-x-4' : 'translate-x-0'}`}></div>
              </div>
              <span className="text-sm font-black text-slate-900">Builder Active</span>
            </div>
          )}

          {!forcedTemplate && <div className="h-6 w-px bg-slate-200"></div>}

          {forcedTemplate ? (
            <span className="text-sm font-black text-slate-900 uppercase tracking-widest">{forcedTemplate} Template</span>
          ) : (
            <select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              className="bg-slate-100 border-none rounded-xl px-4 py-2 font-bold text-sm text-slate-700 focus:ring-2 focus:ring-indigo-500 transition-all"
            >
              {Object.keys(TEMPLATE_PRESETS).map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => addSection()}
            className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl transition-all"
            title="Add Section"
          >
            <Plus size={20} />
          </button>
          <button
            onClick={handleExport}
            className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl transition-all"
            title="Export JSON"
          >
            <Download size={20} />
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl transition-all"
            title="Import JSON"
          >
            <Upload size={20} />
          </button>
          <input type="file" ref={fileInputRef} className="hidden" accept=".json" onChange={handleImport} />
          
          <div className="h-6 w-px bg-slate-200 mx-1"></div>
          
          <button
            onClick={handleSaveToBackend}
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 disabled:opacity-50"
          >
            <Save size={18} className={saving ? 'animate-spin' : ''} />
            {saving ? 'Saving...' : 'Save Registry'}
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Canvas */}
        <div className="flex-1 p-8 overflow-y-auto space-y-4 pb-32" onClick={() => setActiveSectionId(null)}>
          {sections.map((section) => (
            <div
              key={section.id}
              draggable
              onClick={(e) => { e.stopPropagation(); setActiveSectionId(section.id); }}
              onDragStart={(e) => onDragStart(e, section.id)}
              onDragOver={(e) => onDragOver(e, section.id)}
              onDrop={(e) => onDrop(e, section.id)}
              onContextMenu={(e) => {
                e.preventDefault()
                setContextMenu({ x: e.clientX, y: e.clientY, sectionId: section.id })
                setActiveSectionId(section.id)
              }}
              className={`
                bg-white border-2 rounded-3xl p-6 transition-all duration-300 cursor-pointer
                ${section.visible ? 'opacity-100' : 'opacity-40 grayscale'}
                ${dragId === section.id ? 'scale-95 border-indigo-200 opacity-40 shadow-inner' : ''}
                ${dragOverId === section.id ? 'border-indigo-400 bg-indigo-50/30' : ''}
                ${activeSectionId === section.id ? 'border-indigo-500 shadow-md ring-4 ring-indigo-500/10' : 'shadow-sm border-slate-100 hover:border-slate-200 hover:shadow-md'}
              `}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4">
                  <div className="cursor-grab active:cursor-grabbing text-slate-300 hover:text-slate-500 transition-colors">
                    <GripVertical size={20} />
                  </div>
                  
                  {editingId === section.id ? (
                    <input
                      autoFocus
                      value={section.name}
                      onChange={(e) => setSections(sections.map(s => s.id === section.id ? { ...s, name: e.target.value } : s))}
                      onBlur={() => setEditingId(null)}
                      onKeyDown={(e) => e.key === 'Enter' && setEditingId(null)}
                      className="bg-slate-50 border-none font-black text-lg text-slate-900 rounded-lg px-2 py-0"
                    />
                  ) : (
                    <h3 
                      onDoubleClick={() => setEditingId(section.id)}
                      className="font-black text-lg text-slate-900 cursor-text select-none"
                    >
                      {section.name}
                    </h3>
                  )}

                  <div className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${section.visible ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                    {section.visible ? 'Visible' : 'Hidden'}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => { e.stopPropagation(); setSections(sections.map(s => s.id === section.id ? { ...s, visible: !s.visible } : s)) }}
                    className={`p-2 rounded-xl transition-all ${section.visible ? 'text-indigo-600 bg-indigo-50' : 'text-slate-400 bg-slate-100'}`}
                  >
                    {section.visible ? <Eye size={18} /> : <EyeOff size={18} />}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteSection(section.id) }}
                    className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              <textarea
                value={section.comment}
                onChange={(e) => setSections(sections.map(s => s.id === section.id ? { ...s, comment: e.target.value } : s))}
                placeholder="// Describe what AI should change in this section..."
                className="w-full min-h-[80px] bg-slate-50 border border-slate-100 rounded-2xl p-4 text-xs font-mono text-slate-700 focus:ring-2 focus:ring-indigo-500 transition-all resize-y"
              />
            </div>
          ))}

          {sections.length === 0 && (
            <div className="text-center py-20 bg-white rounded-[2.5rem] border border-dashed border-slate-200">
              <Layout size={40} className="mx-auto text-slate-200 mb-4" />
              <p className="text-slate-400 font-bold">No sections in this template.</p>
              <button onClick={() => addSection()} className="mt-4 text-indigo-600 font-black text-sm hover:underline">+ Add First Section</button>
            </div>
          )}
        </div>

        {/* Inspector Sidebar */}
        {activeSectionId && (
          <div className="w-80 bg-white border-l border-slate-200 p-6 overflow-y-auto shadow-xl z-10">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-black text-lg text-slate-900 flex items-center gap-2">
                <Settings2 size={20} className="text-indigo-500" /> Properties
              </h3>
              <button onClick={() => setActiveSectionId(null)} className="text-slate-400 hover:text-slate-600 p-1">
                <X size={18} />
              </button>
            </div>

            {(() => {
              const sec = sections.find(s => s.id === activeSectionId)
              if (!sec) return null
              const updateStyle = (key: keyof TemplateSectionStyles, value: string) => {
                setSections(sections.map(s => s.id === sec.id ? { 
                  ...s, 
                  styles: { ...(s.styles || {}), [key]: value } 
                } : s))
              }
              const styles = sec.styles || {}

              const InputField = ({ label, field, placeholder }: { label: string, field: keyof TemplateSectionStyles, placeholder: string }) => (
                <div className="mb-4">
                  <label className="block text-[11px] font-black uppercase text-slate-500 mb-1.5 tracking-widest">{label}</label>
                  <input
                    type="text"
                    value={styles[field] || ''}
                    onChange={(e) => updateStyle(field, e.target.value)}
                    placeholder={placeholder}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 focus:ring-2 focus:ring-indigo-500 transition-all"
                  />
                </div>
              )

              return (
                <div className="space-y-6">
                  <div>
                    <h4 className="text-sm font-bold text-slate-700 mb-3 border-b pb-2">Layout & Spacing</h4>
                    <InputField label="Margin Top" field="marginTop" placeholder="e.g., 2rem, 32px" />
                    <InputField label="Margin Bottom" field="marginBottom" placeholder="e.g., 2rem, 32px" />
                    <InputField label="Padding Top" field="paddingTop" placeholder="e.g., 1rem, 16px" />
                    <InputField label="Padding Bottom" field="paddingBottom" placeholder="e.g., 1rem, 16px" />
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-slate-700 mb-3 border-b pb-2">Appearance</h4>
                    <div className="mb-4">
                      <label className="block text-[11px] font-black uppercase text-slate-500 mb-1.5 tracking-widest">Text Align</label>
                      <select 
                        value={styles.textAlign || ''} 
                        onChange={(e) => updateStyle('textAlign', e.target.value)}
                        className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 focus:ring-2 focus:ring-indigo-500"
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
                    <h4 className="text-sm font-bold text-slate-700 mb-3 border-b pb-2">Advanced</h4>
                    <InputField label="Custom CSS Classes" field="customClasses" placeholder="e.g., shadow-lg hover:bg-slate-50" />
                  </div>
                </div>
              )
            })()}
          </div>
        )}
      </div>

      {/* Context Menu Portal */}
      {contextMenu && <ContextMenu 
        x={contextMenu.x} 
        y={contextMenu.y} 
        onClose={() => setContextMenu(null)}
        actions={{
          addAbove: () => {
            const idx = sections.findIndex(s => s.id === contextMenu.sectionId)
            const newSections = [...sections]
            newSections.splice(idx, 0, { id: `section-${Date.now()}`, name: 'New Section', comment: '', visible: true, order: 0, styles: {} })
            setSections(newSections.map((s, i) => ({ ...s, order: i })))
          },
          addBelow: () => addSection(contextMenu.sectionId),
          duplicate: () => duplicateSection(contextMenu.sectionId),
          toTop: () => moveSection(contextMenu.sectionId, 'top'),
          toBottom: () => moveSection(contextMenu.sectionId, 'bottom'),
          clearComment: () => setSections(sections.map(s => s.id === contextMenu.sectionId ? { ...s, comment: '' } : s)),
          delete: () => deleteSection(contextMenu.sectionId)
        }}
      />}
    </div>
  )
}

function ContextMenu({ x, y, onClose, actions }: { x: number, y: number, onClose: () => void, actions: any }) {
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (menuRef.current) {
      const { innerWidth, innerHeight } = window
      const { offsetWidth, offsetHeight } = menuRef.current
      if (x + offsetWidth > innerWidth) x -= offsetWidth
      if (y + offsetHeight > innerHeight) y -= offsetHeight
    }
  }, [x, y])

  const Item = ({ icon: Icon, label, onClick, danger }: any) => (
    <div 
      onClick={() => { onClick(); onClose(); }}
      className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer text-sm font-bold transition-colors ${danger ? 'text-red-600 hover:bg-red-50' : 'text-slate-700 hover:bg-slate-100'}`}
    >
      <Icon size={16} />
      <span>{label}</span>
    </div>
  )

  return ReactDOM.createPortal(
    <div 
      ref={menuRef}
      style={{ top: y, left: x }}
      className="fixed z-[9999] w-64 bg-white border border-slate-200 shadow-2xl rounded-2xl overflow-hidden py-2 animate-in fade-in zoom-in duration-150"
      onMouseDown={(e) => e.stopPropagation()}
    >
      <Item icon={ChevronUp} label="Add Section Above" onClick={actions.addAbove} />
      <Item icon={ChevronDown} label="Add Section Below" onClick={actions.addBelow} />
      <Item icon={Copy} label="Duplicate" onClick={actions.duplicate} />
      <div className="h-px bg-slate-100 my-1 mx-2"></div>
      <Item icon={ChevronUp} label="Move to Top" onClick={actions.toTop} />
      <Item icon={ChevronDown} label="Move to Bottom" onClick={actions.toBottom} />
      <div className="h-px bg-slate-100 my-1 mx-2"></div>
      <Item icon={X} label="Clear Comment" onClick={actions.clearComment} />
      <div className="h-px bg-slate-100 my-1 mx-2"></div>
      <Item icon={Trash2} label="Delete" onClick={actions.delete} danger />
    </div>,
    document.body
  )
}

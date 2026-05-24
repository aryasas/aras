import { Editor, Frame, useEditor, type SerializedNodes } from '@craftjs/core'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAras } from '../aras-core/hooks/useAras'
import Box from './template-studio/components/Box'
import Sidebar from './template-studio/components/Sidebar'
import Header from './template-studio/components/Header'
import Island from './template-studio/components/Island'
import FieldGrid from './template-studio/components/FieldGrid'
import Field from './template-studio/components/Field'
import ButtonEl from './template-studio/components/ButtonEl'
import SummaryRow from './template-studio/components/SummaryRow'
import Text from './template-studio/components/Text'
import Palette from './template-studio/panels/Palette'
import Inspector from './template-studio/panels/Inspector'
import Topbar from './template-studio/panels/Topbar'
import Outline from './template-studio/panels/Outline'
import { DEFAULT_TEMPLATE_NAME, cloneDefaultTree } from './template-studio/lib/defaultTree'
import { flushNotes, loadTree, saveTree, type TemplateNotePayload } from './template-studio/lib/api'
import { BREAKPOINT_WIDTHS, BreakpointContext, type Breakpoint } from './template-studio/lib/breakpoints'
import './template-studio/lib/styles.css'

export interface TemplateSection {
  id: string
  name: string
  visible: boolean
  comment: string
  order: number
  styles?: {
    marginTop?: string
    marginBottom?: string
    paddingTop?: string
    paddingBottom?: string
    textAlign?: string
    backgroundColor?: string
    textColor?: string
    border?: string
    borderRadius?: string
    customClasses?: string
  }
}

const resolver = {
  Box,
  Sidebar,
  Header,
  Island,
  FieldGrid,
  Field,
  ButtonEl,
  SummaryRow,
  Text,
}

function inferNodeLabel(node: SerializedNodes[string]) {
  const props = node.props as Record<string, unknown>
  return String(
    props.label
    ?? props.title
    ?? props.text
    ?? props.brand
    ?? props.userName
    ?? node.displayName,
  )
}

function collectNotes(
  tree: SerializedNodes,
  breakpoint: Breakpoint,
): TemplateNotePayload[] {
  return Object.entries(tree).flatMap(([id, node]) => {
    if (id === 'ROOT') return []
    const note = String(node.custom?.note ?? '').trim()
    if (!note) return []

    return [{
      node_id: id,
      node_kind: node.displayName,
      node_label: inferNodeLabel(node),
      breakpoint,
      comment: note,
      status: (node.custom?.noteStatus as TemplateNotePayload['status']) || 'pending',
    }]
  })
}

function EditorStateBridge({
  onChange,
}: {
  onChange: (tree: SerializedNodes) => void
}) {
  const { serialized } = useEditor((_, query) => ({
    serialized: query.serialize(),
  }))

  useEffect(() => {
    onChange(JSON.parse(serialized) as SerializedNodes)
  }, [onChange, serialized])

  return null
}

export default function TemplateBuilder() {
  const { notify } = useAras()
  const [searchParams] = useSearchParams()
  const fromRoute = searchParams.get('from') || DEFAULT_TEMPLATE_NAME
  const [templateName, setTemplateName] = useState(fromRoute)
  const [activeBreakpoint, setActiveBreakpoint] = useState<Breakpoint>('desktop')
  const [zoom, setZoom] = useState(100)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [frameData, setFrameData] = useState<SerializedNodes>(cloneDefaultTree())
  const [serializedNodes, setSerializedNodes] = useState<SerializedNodes>(cloneDefaultTree())
  const [editorKey, setEditorKey] = useState(0)

  useEffect(() => {
    let cancelled = false

    const run = async () => {
      setLoading(true)
      const tree = await loadTree(fromRoute)
      if (cancelled) return
      setFrameData(tree)
      setSerializedNodes(tree)
      setEditorKey((current) => current + 1)
      setLoading(false)
    }

    run()

    return () => {
      cancelled = true
    }
  }, [fromRoute])

  const handleTreeChange = useCallback((tree: SerializedNodes) => {
    setSerializedNodes(tree)
  }, [])

  const handleSave = useCallback(async () => {
    setSaving(true)
    await saveTree(templateName, serializedNodes)
    await flushNotes(templateName, collectNotes(serializedNodes, activeBreakpoint))
    setSaving(false)
    notify('Template snapshot saved', 'success')
  }, [activeBreakpoint, notify, serializedNodes, templateName])

  const canvasWidth = useMemo(() => BREAKPOINT_WIDTHS[activeBreakpoint], [activeBreakpoint])

  return (
    <div className="template-studio-root flex h-full min-h-[calc(100vh-120px)] flex-col gap-4 p-4">
      <BreakpointContext.Provider value={{ activeBreakpoint, setActiveBreakpoint }}>
        <Editor resolver={resolver}>
          <EditorStateBridge onChange={handleTreeChange} />
          <Topbar
            templateName={templateName}
            onTemplateNameChange={setTemplateName}
            zoom={zoom}
            onZoomChange={setZoom}
            onSave={handleSave}
            saving={saving}
          />

          <div className="grid min-h-0 flex-1 grid-cols-[300px_minmax(0,1fr)_360px] gap-4">
            <div className="flex min-h-0 flex-col gap-4">
              <section className="template-studio-panel overflow-hidden rounded-[26px]">
                <Palette />
              </section>
              <section className="template-studio-panel min-h-0 flex-1 overflow-hidden rounded-[26px]">
                <Outline />
              </section>
            </div>

            <section className="template-studio-panel min-h-0 overflow-hidden rounded-[30px] p-4">
              <div className="template-studio-dot-grid template-studio-hide-scroll flex h-full min-h-[700px] items-start justify-center overflow-auto rounded-[24px] border border-[rgba(226,232,240,0.9)] p-6">
                {loading ? (
                  <div className="flex h-full min-h-[640px] w-full items-center justify-center text-sm font-semibold text-[var(--ts-surface-500)]">
                    Loading template tree…
                  </div>
                ) : (
                  <div
                    className="template-studio-canvas shrink-0"
                    style={{
                      width: `${canvasWidth}px`,
                      transform: `scale(${zoom / 100})`,
                    }}
                  >
                    <Frame key={editorKey} data={frameData} />
                  </div>
                )}
              </div>
            </section>

            <section className="template-studio-panel min-h-0 overflow-y-auto rounded-[26px]">
              <Inspector />
            </section>
          </div>
        </Editor>
      </BreakpointContext.Provider>
    </div>
  )
}

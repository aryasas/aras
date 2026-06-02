// claude-opus-4-7
import { useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { DynamicForm } from '../aras-core/components/DynamicForm'
import ListView from '../aras-core/components/ListView'
import { useUIStore } from '../store/uiStore'

export default function DynamicView() {
  const params = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const setFullWidth = useUIStore((s) => s.setFullWidth)

  const splat = params['*'] || ''
  const { app, model, segment1, id: paramId, resource: resourceParam } = params

  let segments: string[] = []
  if (segment1) {
    segments = [segment1, ...splat.split('/').filter(Boolean)].filter(Boolean) as string[]
  } else if (app && model) {
    segments = [app, model]
    if (paramId) segments.push(paramId)
  } else if (resourceParam) {
    // Derive segments from pathname to preserve app prefix (e.g. /dev/style-overrides → dev/style_overrides)
    const pathSegments = location.pathname.replace(/^\//, '').split('/').filter(Boolean)
    segments = pathSegments.map(s => s.replace(/-/g, '_'))
  }

  let resource = ""
  let id: string | undefined = undefined

  if (segments.length === 0) {
    return (
      <div className="arc arc-card p-10 text-center border-dashed">
        <div className="arc-id"><b>error</b>/invalid-path</div>
        <p className="arc-dim text-[13px] mt-2">Invalid resource path.</p>
      </div>
    )
  }

  const lastSegment = segments[segments.length - 1]
  const isId = !isNaN(Number(lastSegment)) || lastSegment === 'new'
  if (isId) {
    id = lastSegment
    resource = segments.slice(0, -1).join('/')
  } else {
    resource = segments.join('/')
  }

  // Use actual URL path as base so nav back works for both dev/:resource and dev/table/:app/:model
  const listPath = id ? location.pathname.replace(/\/[^/]+$/, '') : location.pathname
  const basePath = listPath
  const isListMode = !id

  useEffect(() => {
    if (!isListMode) return
    setFullWidth(true)
    return () => setFullWidth(false)
  }, [isListMode, setFullWidth])

  if (id) {
    return (
      <DynamicForm
        resource={resource}
        id={id}
        initialData={location.state?.initialData}
        onSave={() => navigate(basePath)}
        onCancel={() => navigate(basePath)}
        onDelete={() => navigate(basePath)}
        onNavigate={(newId: string | number) => navigate(`${basePath}/${newId}`)}
      />
    )
  }

  return (
    <div className="arc h-full flex flex-col">
      <ListView
        resource={resource}
        onRowClick={(rowId) => navigate(`${basePath}/${rowId}`)}
        onAdd={() => navigate(`${basePath}/new`)}
      />
    </div>
  )
}

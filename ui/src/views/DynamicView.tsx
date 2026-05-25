// claude-opus-4-7
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { DynamicForm } from '../aras-core/components/DynamicForm'
import ListView from '../aras-core/components/ListView'

export default function DynamicView() {
  const params = useParams()
  const navigate = useNavigate()
  const location = useLocation()

  const splat = params['*'] || ''
  const { app, model, segment1, id: paramId } = params

  let segments: string[] = []
  if (segment1) {
    segments = [segment1, ...splat.split('/').filter(Boolean)].filter(Boolean) as string[]
  } else if (app && model) {
    segments = [app, model]
    if (paramId) segments.push(paramId)
  }

  if (segments.length < 2) {
    return (
      <div className="arc arc-card p-10 text-center border-dashed">
        <div className="arc-id"><b>error</b>/invalid-path</div>
        <p className="arc-dim text-[13px] mt-2">Invalid resource path.</p>
      </div>
    )
  }

  let resource = ""
  let id: string | undefined = undefined
  const lastSegment = segments[segments.length - 1]
  const isId = !isNaN(Number(lastSegment)) || lastSegment === 'new'
  if (isId) {
    id = lastSegment
    resource = segments.slice(0, -1).join('/')
  } else {
    resource = segments.join('/')
  }

  const basePath = `/${resource}`

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

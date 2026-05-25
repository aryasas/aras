import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { DynamicForm } from '../aras-core/components/DynamicForm'
import ListView from '../aras-core/components/ListView'

export default function DynamicView() {
  const params = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  
  // Resolve resource path and ID from segments
  const splat = params['*'] || ''
  const { app, model, segment1, id: paramId } = params

  let segments: string[] = []

  if (segment1) {
    // Catch-all style: /erp/accounting/accounts
    segments = [segment1, ...splat.split('/').filter(Boolean)].filter(Boolean) as string[]
  } else if (app && model) {
    // Explicit style: /dev/table/dev/template-annotations
    segments = [app, model]
    if (paramId) segments.push(paramId)
  }
  
  if (segments.length < 2) {
    return <div className="p-12 text-center text-[var(--app-muted)] bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] border border-dashed border-[var(--app-border)]">Invalid resource path.</div>
  }

  let resource = ""
  let id: string | undefined = undefined

  // Logic: if the last segment is numeric or 'new', it's an ID.
  const lastSegment = segments[segments.length - 1]
  const isId = !isNaN(Number(lastSegment)) || lastSegment === 'new'

  if (isId) {
    id = lastSegment
    resource = segments.slice(0, -1).join('/')
  } else {
    resource = segments.join('/')
  }

  // Ensure absolute path for navigation
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
    <div className="h-full flex flex-col">
       <ListView 
          resource={resource} 
          onRowClick={(rowId) => navigate(`${basePath}/${rowId}`)}
          onAdd={() => navigate(`${basePath}/new`)}
       />
    </div>
  )
}

import { useParams, useNavigate } from 'react-router-dom'
import { DynamicForm } from '../aras-core/components/DynamicForm'
import ListView from '../aras-core/components/ListView'

export default function DynamicView() {
  const params = useParams()
  const navigate = useNavigate()
  
  // Resolve resource path and ID from segments
  // allSegments = [segment1, ...splat]
  const splat = params['*'] || ''
  const segments = [params.segment1, ...splat.split('/').filter(Boolean)].filter(Boolean) as string[]
  
  if (segments.length < 2) {
    return <div className="p-12 text-center text-slate-400 bg-white rounded-3xl border border-dashed border-slate-200">Invalid resource path.</div>
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
        onSave={() => navigate(basePath)}
        onCancel={() => navigate(basePath)}
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

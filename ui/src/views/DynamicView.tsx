import { useParams, useNavigate } from 'react-router-dom'
import { DynamicForm } from '../aras-core/components/DynamicForm'
import ListView from '../aras-core/components/ListView'

export default function DynamicView() {
  const { app, model, id } = useParams()
  const navigate = useNavigate()
  
  if (!app || !model) {
    return <div className="p-12 text-center text-slate-400 bg-white rounded-3xl border border-dashed border-slate-200">Invalid resource path.</div>
  }

  const resource = `${app}/${model}`

  if (id) {
    return (
      <DynamicForm 
        resource={resource} 
        id={id} 
        onSave={() => navigate(`/${app}/${model}`)}
        onCancel={() => navigate(`/${app}/${model}`)}
      />
    )
  }

  return (
    <div className="h-full flex flex-col">
       <ListView 
          resource={resource} 
          onRowClick={(rowId) => navigate(`/${app}/${model}/${rowId}`)}
          onAdd={() => navigate(`/${app}/${model}/new`)}
       />
    </div>
  )
}

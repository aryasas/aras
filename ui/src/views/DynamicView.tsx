import { useParams } from 'react-router-dom'
import DynamicTable from '../aras-core/components/DynamicTable'

export default function DynamicView() {
  const { app, model } = useParams()
  
  if (!app || !model) {
    return <div className="p-12 text-center text-slate-400 bg-white rounded-3xl border border-dashed border-slate-200">Invalid resource path.</div>
  }

  return <DynamicTable resource={`${app}/${model}`} />
}

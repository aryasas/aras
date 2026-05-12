import ListView from '../aras-core/components/ListView'

const AuditLogs = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">System Audit Trail</h1>
        <p className="text-slate-500">Track changes to every record across the entire platform.</p>
      </div>
      
      <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden h-[calc(100vh-250px)]">
         <ListView 
           resource="registry/aras_activity_logs" 
           onRowClick={(id) => console.log('Audit log clicked', id)}
         />
      </div>
    </div>
  )
}

export default AuditLogs

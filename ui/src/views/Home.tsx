import { DashboardView } from '../aras-core/components/DashboardView'

export default function HomeView() {
  return (
    <>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Dashboard Overview</h1>
          <p className="text-slate-500 mt-1">Real-time performance and analytics for your system.</p>
        </div>
      </div>

      <DashboardView />
    </>
  )
}

import * as LucideIcons from 'lucide-react'

export default function HomeView() {
  return (
    <>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Dashboard Overview</h1>
          <p className="text-slate-500 mt-1">Real-time performance and analytics for your system.</p>
        </div>
        <button className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 flex items-center gap-2">
          <LucideIcons.Plus size={18} />
          <span>Create New</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard title="Total Revenue" value="$128,430" change="+12.5%" icon={<LucideIcons.DollarSign size={20} />} />
        <StatCard title="Active Orders" value="432" change="+3.2%" icon={<LucideIcons.ShoppingCart size={20} />} />
        <StatCard title="New Customers" value="48" change="-1.5%" negative icon={<LucideIcons.UserPlus size={20} />} />
      </div>

      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-8 border-b border-slate-100 flex items-center justify-between bg-slate-50/20">
          <div>
            <h2 className="font-bold text-xl text-slate-900">Platform Analytics</h2>
            <p className="text-slate-400 text-sm font-medium uppercase tracking-widest mt-1">Live Feed</p>
          </div>
          <button className="px-4 py-2 text-indigo-600 text-sm font-bold bg-indigo-50 rounded-xl hover:bg-indigo-100 transition-colors">Export Report</button>
        </div>
        <div className="p-12 text-center text-slate-400 flex flex-col items-center">
          <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mb-4">
             <LucideIcons.LayoutDashboard size={32} className="text-slate-200" />
          </div>
          <p className="max-w-md">Your custom dashboard widgets and metrics will appear here. The system has automatically discovered your installed modules.</p>
        </div>
      </div>
    </>
  )
}

function StatCard({ title, value, change, negative = false, icon }: { title: string, value: string, change: string, negative?: boolean, icon: any }) {
  return (
    <div className="bg-white p-7 rounded-3xl border border-slate-200 shadow-sm hover:shadow-xl hover:shadow-slate-200/50 transition-all group">
      <div className="flex items-start justify-between mb-4">
        <div className="p-3 bg-slate-50 rounded-2xl group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors text-slate-400">
          {icon}
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${negative ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`}>
          {change}
        </span>
      </div>
      <p className="text-slate-500 text-sm font-medium mb-1 uppercase tracking-wide">{title}</p>
      <h3 className="text-3xl font-black text-slate-900 tracking-tight">{value}</h3>
    </div>
  )
}

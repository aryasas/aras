import { Link } from 'react-router-dom'
import { LayoutDashboard, Rows3, Settings2, ArrowRight } from 'lucide-react'

const dashboardSections = [
  {
    title: 'Dashboard Widgets',
    description: 'Configure available widget records, data sources, display type, sizing, and widget JSON options.',
    path: '/registry/aras_widgets',
    icon: <Settings2 size={22} />,
  },
  {
    title: 'User Dashboard Layout',
    description: 'Manage persisted per-user dashboard layout records and widget ordering.',
    path: '/registry/aras_dashboard_layouts',
    icon: <Rows3 size={22} />,
  },
]

export default function DashboardSettings() {
  return (
    <div className="p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-black text-[var(--app-text)] tracking-tight flex items-center gap-3">
            <LayoutDashboard className="text-[var(--app-accent)]" />
            Dashboard Settings
          </h1>
          <p className="text-[var(--app-muted)] mt-1 font-medium">Manage dashboard widgets and per-user dashboard layout.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {dashboardSections.map((section) => (
          <Link
            key={section.title}
            to={section.path}
            className="bg-[var(--app-panel)] p-6 rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-sm hover:shadow-xl hover:shadow-slate-200/50 transition-all group"
          >
            <div className="flex items-start gap-4">
              <div className="p-4 bg-[var(--app-accent-glow)] rounded-[var(--app-radius-lg)] text-[var(--app-accent)] group-hover:bg-[var(--app-accent)] group-hover:text-white transition-colors">
                {section.icon}
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-black text-[var(--app-text)] mb-2">{section.title}</h2>
                <p className="text-sm leading-relaxed text-[var(--app-muted)]">{section.description}</p>
                <div className="mt-5 inline-flex items-center gap-2 text-sm font-black text-[var(--app-accent)]">
                  Open
                  <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

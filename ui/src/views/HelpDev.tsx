import { Terminal, Database, GitBranch, Code2, Layers, RefreshCw, Shield, Cpu, ChevronRight, ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'

interface Section {
  icon: React.ReactNode
  color: string
  title: string
  items: { label: string; desc: string; code?: string }[]
}

const sections: Section[] = [
  {
    icon: <Layers size={20} />,
    color: 'indigo',
    title: 'Framework Architecture',
    items: [
      { label: 'Level 1 — Aras', desc: 'Root singleton. All framework primitives live here (Model, App, View, Schema, Manager, Router).' },
      { label: 'Level 2 — App', desc: 'Declare app_name, app_label, icon, models[], menu_groups[]. Sub-apps set parent_name.', code: 'class MyApp(Aras.App):\n    app_name = "myapp"\n    app_type = "app"  # "framework"|"app"|"module"\n    models = [MyModel]' },
      { label: 'Level 3 — Model', desc: 'SQLAlchemy 2.0 mapped_column. Table name must be {app_name}_{table}.', code: 'class MyModel(Aras.Model):\n    __tablename__ = "myapp_items"\n    __features__ = ["audit"]' },
      { label: 'Level 4 — View', desc: 'UI metadata only — title, icon, fields, layout. Never put these on the Model.', code: 'class MyView(Aras.View):\n    model = MyModel\n    title = "My Items"' },
    ]
  },
  {
    icon: <Database size={20} />,
    color: 'emerald',
    title: 'Registry & Sync',
    items: [
      { label: 'python manage.py sync', desc: 'Creates/migrates tables, upserts aras_apps → aras_resources → aras_fields. Run after any model/app change.' },
      { label: 'app_type column', desc: '"framework" = Aras core (dev, auth). "app" = business app. "module" = sub-app with parent_name set.' },
      { label: 'Force Sync from UI', desc: 'DevTools → Force Metadata Sync button — calls POST /dev/sync, clears frontend cache.' },
      { label: 'menu_groups', desc: 'Controls topbar menu layout per app. If empty, all non-child models appear flat.', code: 'menu_groups = [\n  {"label": "Registry", "icon": "Database",\n   "models": ["aras_apps", "aras_fields"]}\n]' },
    ]
  },
  {
    icon: <Code2 size={20} />,
    color: 'blue',
    title: 'API Patterns',
    items: [
      { label: 'Auto CRUD', desc: 'RouterFactory generates GET/POST/PATCH/DELETE + bulk-delete + query + export for every registered model.' },
      { label: 'Custom Action', desc: 'Decorate a Model method with @model_action. Appears as button in DynamicForm.', code: '@model_action(label="Post", icon="Check")\ndef post(self, db, user_id):\n    ...' },
      { label: 'Scoping', desc: '__scoped_by__ = [["org_id","erp_config_organizations"]] - filters all list queries to current organization.' },
      { label: 'Dev Endpoints', desc: 'GET /dev/inspect/routes — full route map. GET /dev/inspect/models — memory registry. GET /dev/inspect/env — sanitized env.' },
    ]
  },
  {
    icon: <GitBranch size={20} />,
    color: 'purple',
    title: 'Multi-Agent Workflow',
    items: [
      { label: 'mha', desc: 'Claude writes docs/handoff.md spec only — no code. Run: python tools/multi_agent.py' },
      { label: 'mha be / mha fe', desc: 'Backend-only or frontend-only agent run.' },
      { label: 'rhf', desc: 'Claude reviews handoff.md, writes verdict APPROVED or NEEDS-FIX, then runs --submit-review to persist to DB.' },
      { label: 'Handoff Runs tab', desc: 'DevTools → Handoff Runs — full history of all agent runs with token usage, files written, prompts.' },
    ]
  },
  {
    icon: <Shield size={20} />,
    color: 'rose',
    title: 'Auth & Permissions',
    items: [
      { label: 'require_admin', desc: 'FastAPI dependency. Applied to all /dev/* and management endpoints.' },
      { label: 'require_auth', desc: 'Applied to all app CRUD endpoints. Checks JWT in Authorization header.' },
      { label: 'RBAC', desc: 'Settings -> RBAC Manager - roles and per-resource permissions. Scoped by organization for SaaS.' },
      { label: 'Default creds', desc: 'admin / admin — change in production via Settings → Users.' },
    ]
  },
  {
    icon: <RefreshCw size={20} />,
    color: 'amber',
    title: 'Dev Shortcuts',
    items: [
      { label: 'cmp', desc: 'Inspect project — review code, UI, function coverage, and flag refactor opportunities.' },
      { label: 'ggc', desc: 'Print git commit command text (does not execute).' },
      { label: 'updd', desc: 'Update docs/feature.md and docs/aras.md with what was added/changed.' },
      { label: 'mhl', desc: 'Log a manual (non-agent) change to docs + DB handoff table.' },
    ]
  },
]

const colorMap: Record<string, { bg: string; text: string; badge: string }> = {
  indigo: { bg: 'bg-indigo-50', text: 'text-indigo-600', badge: 'bg-indigo-100 text-indigo-700' },
  emerald: { bg: 'bg-emerald-50', text: 'text-emerald-600', badge: 'bg-emerald-100 text-emerald-700' },
  blue:    { bg: 'bg-blue-50',    text: 'text-blue-600',    badge: 'bg-blue-100 text-blue-700' },
  purple:  { bg: 'bg-purple-50',  text: 'text-purple-600',  badge: 'bg-purple-100 text-purple-700' },
  rose:    { bg: 'bg-rose-50',    text: 'text-rose-600',    badge: 'bg-rose-100 text-rose-700' },
  amber:   { bg: 'bg-amber-50',   text: 'text-amber-600',   badge: 'bg-amber-100 text-amber-700' },
}

export default function HelpDev() {
  return (
    <div className="p-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-start justify-between mb-10">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-slate-900 text-white rounded-2xl">
              <Terminal size={24} />
            </div>
            <h1 className="text-3xl font-black text-slate-900 tracking-tight">Developer Reference</h1>
          </div>
          <p className="text-slate-500 font-medium ml-16">Aras framework — architecture, patterns, CLI commands, and agent workflows.</p>
        </div>
        <div className="flex gap-3">
          <Link to="/dev" className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl text-sm font-bold text-slate-700 transition-all">
            <Cpu size={14} /> DevTools
          </Link>
          <Link to="/help" className="flex items-center gap-2 px-4 py-2 bg-indigo-50 hover:bg-indigo-100 rounded-xl text-sm font-bold text-indigo-700 transition-all">
            User Guide <ChevronRight size={14} />
          </Link>
        </div>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-10">
        {[
          { label: 'Routes Inspector', path: '/dev/routes', icon: <ExternalLink size={14} /> },
          { label: 'Health Check', path: '/dev/health', icon: <ExternalLink size={14} /> },
          { label: 'App Registry', path: '/dev/table/registry/aras_apps', icon: <ExternalLink size={14} /> },
          { label: 'Handoff Runs', path: '/dev', icon: <GitBranch size={14} /> },
        ].map(l => (
          <Link key={l.path} to={l.path}
            className="flex items-center justify-between px-4 py-3 bg-white border border-slate-200 rounded-2xl text-sm font-bold text-slate-700 hover:border-indigo-300 hover:text-indigo-600 transition-all"
          >
            {l.label} {l.icon}
          </Link>
        ))}
      </div>

      {/* Sections */}
      <div className="space-y-8">
        {sections.map(sec => {
          const c = colorMap[sec.color]
          return (
            <div key={sec.title} className="bg-white rounded-[2rem] border border-slate-200 shadow-sm overflow-hidden">
              <div className={`flex items-center gap-3 px-8 py-5 border-b border-slate-100 ${c.bg}`}>
                <div className={`${c.text}`}>{sec.icon}</div>
                <h2 className="text-lg font-black text-slate-900">{sec.title}</h2>
              </div>
              <div className="divide-y divide-slate-50">
                {sec.items.map(item => (
                  <div key={item.label} className="px-8 py-5">
                    <div className="flex items-start gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 rounded-lg text-xs font-black ${c.badge}`}>{item.label}</span>
                        </div>
                        <p className="text-slate-600 text-sm">{item.desc}</p>
                        {item.code && (
                          <pre className="mt-3 bg-slate-950 text-slate-200 rounded-xl px-4 py-3 text-xs font-mono overflow-x-auto whitespace-pre">{item.code}</pre>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

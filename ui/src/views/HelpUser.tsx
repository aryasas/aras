import { HelpCircle, Search, FileText, BarChart2, Settings, Users, ChevronRight, Terminal } from 'lucide-react'
import { Link } from 'react-router-dom'

interface Topic {
  q: string
  a: string
}

interface Section {
  icon: React.ReactNode
  color: string
  title: string
  topics: Topic[]
}

const sections: Section[] = [
  {
    icon: <Search size={20} />,
    color: 'indigo',
    title: 'Navigation & Search',
    topics: [
      { q: 'How do I find a record?', a: 'Use the search bar at the top of any list view, or press Ctrl+K (Cmd+K on Mac) to open the Command Palette and search across all modules.' },
      { q: 'How do I switch modules?', a: 'Click the app name in the top bar to open the module menu. Sub-modules appear nested below their parent app.' },
      { q: 'What is the Dashboard?', a: 'The Dashboard shows key metrics and quick-access widgets for your most-used data. It is personalized per user.' },
    ]
  },
  {
    icon: <FileText size={20} />,
    color: 'emerald',
    title: 'Records & Forms',
    topics: [
      { q: 'How do I create a new record?', a: 'Open any list view and click the "+ New" button in the top-right. Fill in the form and click Save.' },
      { q: 'How do I edit a record?', a: 'Click any row in the list to open its form. Make your changes and click Save. Changes are tracked in the Audit Trail.' },
      { q: 'How do I delete records?', a: 'Select one or more rows using the checkbox column, then click the Delete button that appears in the toolbar.' },
      { q: 'What are child tables?', a: 'Some records (e.g. Invoice Lines on an Invoice) appear as embedded tables inside the parent form. Add rows with the + button inside the child table.' },
    ]
  },
  {
    icon: <BarChart2 size={20} />,
    color: 'blue',
    title: 'Reports',
    topics: [
      { q: 'Where are the reports?', a: 'Click "Report Center" in the left sidebar. Reports are grouped by module (Finance, Stock, CRM, etc.).' },
      { q: 'Can I export data?', a: 'Yes — open any list view, optionally filter, then click the Export button (spreadsheet icon) to download as CSV/Excel.' },
      { q: 'How do I filter a list?', a: 'Use the search bar at the top of the list for a quick text search. More advanced filters can be applied via the Filter panel.' },
    ]
  },
  {
    icon: <Settings size={20} />,
    color: 'purple',
    title: 'Settings & Configuration',
    topics: [
      { q: 'Where do I change my password?', a: 'Click your user avatar in the top-right, select Profile, and use the Change Password section.' },
      { q: 'How do I configure the system?', a: 'Go to Settings in the left sidebar. Admins can manage organization info, chart of accounts, currencies, and system-wide settings.' },
      { q: 'How do I manage users?', a: 'Settings → RBAC Manager to create roles and assign permissions. Add users in the Users section under Developer Tools → Registry.' },
    ]
  },
  {
    icon: <Users size={20} />,
    color: 'rose',
    title: 'ERP Modules',
    topics: [
      { q: 'What modules are available?', a: 'Accounting, inflow/outflow transactions, Stock, CRM, Point of Transaction, and Config (organization, chart of accounts, currencies, warehouses).' },
      { q: 'How do I post a transaction?', a: 'Open the record (e.g. Inflow Invoice), complete all required fields, then click the "Post" action button. This creates the journal entry.' },
      { q: 'What is Draft vs Posted?', a: 'Draft records can be edited freely. Once Posted, a record is locked and creates accounting entries. Use the workflow status badge to see current state.' },
      { q: 'How do I manage inventory?', a: 'Stock module -> Stock Movements for manual adjustments. Delivery Notes and Outflow Receipts automatically update stock when posted.' },
    ]
  },
]

const colorMap: Record<string, { bg: string; text: string; dot: string }> = {
  indigo: { bg: 'bg-[var(--app-accent-glow)]', text: 'text-[var(--app-accent)]', dot: 'bg-indigo-400' },
  emerald: { bg: 'bg-emerald-50', text: 'text-emerald-600', dot: 'bg-emerald-400' },
  blue:    { bg: 'bg-blue-50',    text: 'text-blue-600',    dot: 'bg-blue-400' },
  purple:  { bg: 'bg-purple-50',  text: 'text-purple-600',  dot: 'bg-purple-400' },
  rose:    { bg: 'bg-rose-50',    text: 'text-rose-600',    dot: 'bg-rose-400' },
}

export default function HelpUser() {
  return (
    <div className="p-8 max-w-5xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-start justify-between mb-10">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-[var(--app-accent)] text-white rounded-[var(--app-radius-lg)]">
              <HelpCircle size={24} />
            </div>
            <h1 className="text-3xl font-black text-[var(--app-text)] tracking-tight">Help Center</h1>
          </div>
          <p className="text-[var(--app-muted)] font-medium ml-16">Answers to common questions about using the system.</p>
        </div>
        <Link
          to="/dev/help"
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-[var(--app-radius)] text-sm font-bold hover:bg-slate-800 transition-all"
        >
          <Terminal size={14} /> Developer Reference <ChevronRight size={14} />
        </Link>
      </div>

      {/* Quick tips banner */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-500 rounded-[2rem] p-8 mb-10 text-white">
        <h2 className="text-xl font-black mb-4">Quick Tips</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { tip: 'Press Ctrl+K', desc: 'Open Command Palette to jump anywhere' },
            { tip: 'Click any row', desc: 'Opens the record detail form' },
            { tip: 'Checkbox + Delete', desc: 'Bulk delete selected records' },
          ].map(t => (
            <div key={t.tip} className="bg-[var(--app-panel)]/10 rounded-[var(--app-radius-lg)] p-4">
              <div className="font-black text-sm mb-1">{t.tip}</div>
              <div className="text-indigo-100 text-sm">{t.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* FAQ sections */}
      <div className="space-y-8">
        {sections.map(sec => {
          const c = colorMap[sec.color]
          return (
            <div key={sec.title} className="bg-[var(--app-panel)] rounded-[2rem] border border-[var(--app-border)] shadow-sm overflow-hidden">
              <div className={`flex items-center gap-3 px-8 py-5 border-b border-[var(--app-border)] ${c.bg}`}>
                <div className={c.text}>{sec.icon}</div>
                <h2 className="text-lg font-black text-[var(--app-text)]">{sec.title}</h2>
              </div>
              <div className="divide-y divide-slate-50">
                {sec.topics.map(topic => (
                  <div key={topic.q} className="px-8 py-5">
                    <div className="flex gap-3">
                      <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${c.dot}`} />
                      <div>
                        <p className="font-bold text-[var(--app-text)] mb-1">{topic.q}</p>
                        <p className="text-slate-600 text-sm leading-relaxed">{topic.a}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      <p className="text-center text-[var(--app-muted)] text-sm mt-10">
        Can't find what you need? Contact your system administrator.
      </p>
    </div>
  )
}

import { useState } from 'react'
import { ExternalLink, Search } from 'lucide-react'

type MockEntry = { path: string; title: string; group: 'App Prototypes' | 'Components' }

const MOCK_ENTRIES: MockEntry[] = [
  { path: 'aras-studio/', title: 'Aras Studio', group: 'App Prototypes' },
  { path: 'erp-unified/', title: 'ERP Unified', group: 'App Prototypes' },
  { path: 'erp-modern/', title: 'ERP Modern', group: 'App Prototypes' },
  { path: 'erp-modern-app/', title: 'ERP Modern App', group: 'App Prototypes' },
  { path: 'erp-web/', title: 'ERP Web', group: 'App Prototypes' },
  { path: 'erp-generic/', title: 'ERP Generic', group: 'App Prototypes' },
  { path: 'erp-editorial/', title: 'ERP Editorial', group: 'App Prototypes' },
  { path: 'erp-mobile/', title: 'ERP Mobile', group: 'App Prototypes' },
  { path: 'erp-expo-web/', title: 'ERP Expo (Web)', group: 'App Prototypes' },
  { path: 'erp-expo-native/', title: 'ERP Expo (Native)', group: 'App Prototypes' },
  { path: 'real-layout/', title: 'Real Layout', group: 'App Prototypes' },
  { path: 'implementation-prototype/', title: 'Implementation Prototype', group: 'App Prototypes' },
  { path: 'mock-by-gemini/', title: 'Mock by Gemini', group: 'App Prototypes' },
  { path: 'datatable.html', title: 'Data Table', group: 'Components' },
  { path: 'datatable-light.html', title: 'Data Table (Light)', group: 'Components' },
  { path: 'form.html', title: 'Form', group: 'Components' },
  { path: 'form-light.html', title: 'Form (Light)', group: 'Components' },
  { path: 'formview-proposal.html', title: 'Form View Proposal', group: 'Components' },
  { path: 'listview-proposal.html', title: 'List View Proposal', group: 'Components' },
]

export default function MockGallery() {
  const [q, setQ] = useState('')
  const filtered = MOCK_ENTRIES.filter(
    (entry) => entry.title.toLowerCase().includes(q.toLowerCase()) || entry.path.toLowerCase().includes(q.toLowerCase()),
  )
  const groups = ['App Prototypes', 'Components'] as const

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-black text-[var(--text)]">Mock Gallery</h2>
          <p className="mt-1 text-sm text-[var(--text-3)]">Static UI prototypes served from <code className="text-[var(--text-2)]">/mocks/</code>. Click a card to open full-size.</p>
        </div>
        <div className="relative">
          <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
          <input
            value={q}
            onChange={(event) => setQ(event.target.value)}
            placeholder="Filter mocks…"
            className="w-56 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] py-2 pl-9 pr-3 text-sm text-[var(--text)] outline-none focus:border-[var(--accent)]"
          />
        </div>
      </div>

      {groups.map((group) => {
        const items = filtered.filter((entry) => entry.group === group)
        if (items.length === 0) return null
        return (
          <section key={group}>
            <h3 className="mb-3 text-xs font-black uppercase tracking-[0.18em] text-[var(--text-3)]">{group}<span className="ml-2 text-[var(--text-3)]/60">{items.length}</span></h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {items.map((entry) => <MockCard key={entry.path} entry={entry} />)}
            </div>
          </section>
        )
      })}

      {filtered.length === 0 && (
        <div className="rounded-[var(--radius-lg)] border border-dashed border-[var(--line)] py-16 text-center text-sm text-[var(--text-3)]">
          No mocks match “{q}”.
        </div>
      )}
    </div>
  )
}

function MockCard({ entry }: { entry: MockEntry }) {
  const url = `/mocks/${entry.path}`
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex flex-col overflow-hidden rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] shadow-sm transition-all hover:-translate-y-0.5 hover:border-[var(--accent)] hover:shadow-lg"
    >
      <div className="relative h-44 overflow-hidden border-b border-[var(--line)] bg-[var(--surface-2)]">
        <iframe
          src={url}
          title={entry.title}
          loading="lazy"
          tabIndex={-1}
          aria-hidden
          className="origin-top-left border-0"
          style={{ width: 1280, height: 800, transform: 'scale(0.32)', pointerEvents: 'none' }}
        />
        <span className="absolute inset-0" />
        <span className="absolute right-2 top-2 flex items-center gap-1 rounded-[var(--radius)] bg-[var(--surface)]/90 px-2 py-1 text-[10px] font-black uppercase tracking-wider text-[var(--text-2)] opacity-0 backdrop-blur transition-opacity group-hover:opacity-100">
          <ExternalLink size={11} /> Open
        </span>
      </div>
      <div className="flex items-center justify-between gap-2 p-3">
        <span className="truncate text-sm font-black text-[var(--text)]">{entry.title}</span>
        <code className="shrink-0 truncate text-[11px] font-medium text-[var(--text-3)]">{entry.path}</code>
      </div>
    </a>
  )
}

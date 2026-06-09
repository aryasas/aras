import { Code2, ExternalLink } from 'lucide-react'
import { getApiDocsUrl } from '../../lib/apiDocs'

export default function ApiHelpTab() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-wrap gap-3">
        <a
          href={getApiDocsUrl()}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 rounded-[var(--radius-lg)] bg-[var(--accent)] px-5 py-2.5 text-sm font-bold text-white shadow-lg shadow-indigo-200/50 transition-all hover:opacity-90"
        >
          <ExternalLink size={14} />
          Open Swagger UI (/docs)
        </a>
        <a
          href="/api/v1/dev/inspect/routes"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] px-5 py-2.5 text-sm font-bold text-[var(--text)] transition-all hover:bg-[var(--surface-2)]"
        >
          <ExternalLink size={14} />
          Inspect Routes JSON
        </a>
      </div>

      <div>
        <h3 className="mb-3 text-base font-black text-[var(--text)]">CRUD API Patterns</h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { method: 'GET', path: '/api/v1/{resource}', desc: 'List records. Supports ?page, ?limit, ?search, ?sort, ?order, ?filter_*.' },
            { method: 'POST', path: '/api/v1/{resource}', desc: 'Create a new record. Body is JSON matching the model schema.' },
            { method: 'GET', path: '/api/v1/{resource}/{id}', desc: 'Fetch a single record by primary key.' },
            { method: 'PATCH', path: '/api/v1/{resource}/{id}', desc: 'Partially update a record. Only send changed fields.' },
            { method: 'DELETE', path: '/api/v1/{resource}/{id}', desc: 'Delete a single record.' },
            { method: 'GET', path: '/api/v1/{resource}/export', desc: 'Export records as CSV or Excel.' },
            { method: 'POST', path: '/api/v1/{resource}/query', desc: 'Advanced filter query with complex conditions.' },
            { method: 'POST', path: '/api/v1/{resource}/bulk-delete', desc: 'Delete multiple records by list of IDs.' },
          ].map(({ method, path, desc }) => (
            <div key={path} className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] p-4">
              <div className="mb-2 flex items-center gap-2">
                <span className={`rounded px-2 py-0.5 font-mono text-xs font-black ${method === 'GET' ? 'bg-blue-50 text-blue-700' : method === 'POST' ? 'bg-emerald-50 text-emerald-700' : method === 'PATCH' ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'}`}>{method}</span>
                <code className="font-mono text-xs text-[var(--text-2)]">{path}</code>
              </div>
              <p className="text-xs leading-relaxed text-[var(--text-3)]">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-base font-black text-[var(--text)]">Dev Endpoints</h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { path: '/api/v1/dev/info', desc: 'Framework version, engine type, discovered apps.' },
            { path: '/api/v1/dev/stats', desc: 'Row counts for framework and system tables.' },
            { path: '/api/v1/dev/inspect/models', desc: 'Full schema detail for all registered models.' },
            { path: '/api/v1/dev/inspect/env', desc: 'Active environment config (redacts secrets).' },
            { path: '/api/v1/dev/inspect/routes', desc: 'All registered API routes with methods and tags.' },
          ].map(({ path, desc }) => (
            <a
              key={path}
              href={path}
              target="_blank"
              rel="noopener noreferrer"
              className="group rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] p-4 transition-all hover:border-[var(--accent)] hover:shadow-sm"
            >
              <div className="mb-2 flex items-center justify-between">
                <code className="font-mono text-xs font-bold text-[var(--accent)]">{path}</code>
                <ExternalLink size={11} className="text-[var(--text-3)] transition-colors group-hover:text-[var(--accent)]" />
              </div>
              <p className="text-xs leading-relaxed text-[var(--text-3)]">{desc}</p>
            </a>
          ))}
        </div>
      </div>

      <div className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-5">
        <div className="flex items-center gap-2 text-[var(--text)]">
          <Code2 size={18} />
          <h3 className="text-base font-black">Notes</h3>
        </div>
        <p className="mt-2 text-sm text-[var(--text-3)]">Use Test Lab for request execution, Route Debugger for route discovery, and Swagger for schema-level browsing.</p>
      </div>
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { Database, RefreshCw, Play, CheckCircle2, AlertCircle, MinusCircle } from 'lucide-react'

import { seedApi, type SeedCatalogEntry, type SeedRunResult } from '../lib/api'
import { useUIStore } from '../store/uiStore'
import { useAuthStore } from '../store/authStore'
import { useAras } from '../aras-core/hooks/useAras'

type ResultMap = Record<string, SeedRunResult>

const statusTone: Record<SeedRunResult['status'], string> = {
  ran: 'text-emerald-700 bg-emerald-50 border-emerald-200',
  skipped: 'text-amber-700 bg-amber-50 border-amber-200',
  error: 'text-rose-700 bg-rose-50 border-rose-200',
}

const statusIcon = {
  ran: CheckCircle2,
  skipped: MinusCircle,
  error: AlertCircle,
}

export default function SeedManager() {
  const setPageTitle = useUIStore((state) => state.setPageTitle)
  const activeOrgId = useAuthStore((state) => state.activeOrgId)
  const { confirm, notify } = useAras()

  const [catalog, setCatalog] = useState<SeedCatalogEntry[]>([])
  const [selected, setSelected] = useState<Record<string, boolean>>({})
  const [results, setResults] = useState<ResultMap>({})
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const orgId = activeOrgId && activeOrgId > 0 ? activeOrgId : null

  const applyDefaultSelection = (entries: SeedCatalogEntry[]) => {
    const next: Record<string, boolean> = {}
    for (const app of entries) {
      for (const seed of app.seeds) {
        next[seed.key] = !seed.optional
      }
    }
    setSelected(next)
  }

  const loadCatalog = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await seedApi.list()
      setCatalog(data)
      applyDefaultSelection(data)
    } catch (err: any) {
      const message = err?.response?.data?.detail || err?.message || 'Failed to load seed catalog.'
      setError(message)
      setCatalog([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setPageTitle('Data Seeder', 'Select baseline and optional seed data for the current organization.', 'ADMIN')
    void loadCatalog()
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  const selectedKeys = useMemo(
    () =>
      catalog.flatMap((app) =>
        app.seeds.filter((seed) => selected[seed.key]).map((seed) => seed.key),
      ),
    [catalog, selected],
  )

  const toggleSeed = (key: string) => {
    setSelected((current) => ({ ...current, [key]: !current[key] }))
  }

  const runSeeds = async () => {
    if (!orgId) {
      notify('Select an organization before running seeds.', 'error')
      return
    }
    if (selectedKeys.length === 0) {
      notify('Select at least one seed.', 'error')
      return
    }
    const confirmed = await confirm({
      title: 'Run selected seeds?',
      message: `This will write data for organization ${orgId}.`,
      confirmText: 'Run seeds',
    })
    if (!confirmed) return

    setRunning(true)
    try {
      const response = await seedApi.run(selectedKeys, orgId)
      const mapped = Object.fromEntries(response.map((item) => [item.key, item])) as ResultMap
      setResults(mapped)
      const failures = response.filter((item) => item.status === 'error').length
      notify(
        failures ? `Completed with ${failures} error${failures === 1 ? '' : 's'}.` : 'Selected seeds completed.',
        failures ? 'warning' : 'success',
      )
    } catch (err: any) {
      notify(err?.response?.data?.detail || err?.message || 'Failed to run seeds.', 'error')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="arc flex flex-col gap-5">
      <div className="arc-card arc-dotgrid flex items-center gap-5 p-6" style={{ background: 'var(--bg-2)' }}>
        <div
          className="grid h-14 w-14 place-items-center rounded-[var(--radius-lg)]"
          style={{
            background: 'color-mix(in oklch, var(--accent) 18%, var(--surface))',
            color: 'var(--accent)',
            border: '1px solid color-mix(in oklch, var(--accent) 35%, var(--line))',
          }}
        >
          <Database size={26} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="arc-id"><b>admin</b>/seeder</div>
          <h1 className="mt-0.5 text-[20px] font-semibold tracking-tight text-[var(--text)]">Data Seeder</h1>
          <div className="arc-dim mt-0.5 text-[12px]">
            {catalog.length} apps with declarative seeds · org {orgId ?? 'not selected'}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="arc-btn" onClick={() => void loadCatalog()} disabled={loading || running}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
          <button className="arc-btn primary" onClick={() => void runSeeds()} disabled={loading || running || !selectedKeys.length || !orgId}>
            <Play size={14} /> {running ? 'Running...' : 'Seed selected'}
          </button>
        </div>
      </div>

      {error ? (
        <section className="arc-card border border-[var(--line)] p-5">
          <div className="text-sm font-semibold text-rose-700">{error}</div>
        </section>
      ) : null}

      {loading ? (
        <section className="arc-card p-6">
          <div className="flex items-center gap-3 text-sm text-[var(--text-3)]">
            <RefreshCw size={16} className="animate-spin" />
            Loading seed catalog...
          </div>
        </section>
      ) : null}

      {!loading && !error && catalog.length === 0 ? (
        <section className="arc-card p-8 text-center">
          <div className="text-sm font-semibold text-[var(--text)]">No seed entries found.</div>
          <div className="mt-1 text-sm text-[var(--text-3)]">Apps need declarative `seeds` entries to appear here.</div>
        </section>
      ) : null}

      {!loading && !error && catalog.length > 0 ? (
        <div className="flex flex-col gap-4">
          {catalog.map((app) => (
            <section key={app.app_name} className="arc-card overflow-hidden border border-[var(--line)] bg-[var(--surface)]">
              <div className="flex items-center justify-between gap-3 border-b border-[var(--line)] px-4 py-3" style={{ background: 'var(--surface-2)' }}>
                <div>
                  <div className="text-[14px] font-semibold text-[var(--text)]">{app.app_label}</div>
                  <div className="arc-id arc-dim2">{app.app_name}</div>
                </div>
                <span className="arc-id arc-dim2">{app.seeds.length} seeds</span>
              </div>
              <div className="flex flex-col">
                {app.seeds.map((seed) => {
                  const result = results[seed.key]
                  const StatusIcon = result ? statusIcon[result.status] : null
                  return (
                    <label key={seed.key} className="flex items-start gap-3 border-t border-[var(--line)] px-4 py-3 first:border-t-0">
                      <input
                        type="checkbox"
                        className="mt-1 h-4 w-4 accent-[var(--accent)]"
                        checked={Boolean(selected[seed.key])}
                        disabled={!seed.optional || running}
                        onChange={() => toggleSeed(seed.key)}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-[13px] font-medium text-[var(--text)]">{seed.label}</span>
                          <span
                            className="rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]"
                            style={{
                              borderColor: seed.optional ? 'var(--line)' : 'color-mix(in oklch, var(--accent) 35%, var(--line))',
                              color: seed.optional ? 'var(--text-3)' : 'var(--accent)',
                              background: seed.optional ? 'var(--surface)' : 'color-mix(in oklch, var(--accent) 10%, var(--surface))',
                            }}
                          >
                            {seed.optional ? 'Optional' : 'Required'}
                          </span>
                        </div>
                        <div className="arc-id arc-dim2 mt-1">{seed.key}</div>
                        {result && StatusIcon ? (
                          <div className={`mt-2 inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${statusTone[result.status]}`}>
                            <StatusIcon size={13} />
                            {result.status} · {result.message}
                          </div>
                        ) : null}
                      </div>
                    </label>
                  )
                })}
              </div>
            </section>
          ))}
        </div>
      ) : null}
    </div>
  )
}

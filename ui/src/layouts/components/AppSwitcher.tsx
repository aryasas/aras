import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronDown, Search } from 'lucide-react'
import type { SidebarApp } from '../types'
import { resolveIcon } from '../../lib/iconUtils'
import { isVisibleMenuItem } from '../../lib/menuUtils'
import { useVocabulary } from '../../context/VocabularyContext'

interface AppSwitcherProps {
  sidebarData: SidebarApp[]
}

export function AppSwitcher({ sidebarData }: AppSwitcherProps) {
  const location = useLocation()
  const vocabulary = useVocabulary()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const ref = useRef<HTMLDivElement>(null)

  const apps = useMemo(() => {
    const roots = sidebarData.filter(isVisibleMenuItem)
    return roots.flatMap((app) => {
      const appPath = app.path || `/${app.name}`
      const root = { ...app, path: appPath, label: vocabulary.get(app.label) }
      const children = app.sub_apps
        ?.filter(isVisibleMenuItem)
        .map((sub) => ({
          ...sub,
          path: sub.path || `/${sub.name}`,
          label: vocabulary.get(sub.label),
          parentLabel: vocabulary.get(app.label),
        })) || []
      return [root, ...children]
    })
  }, [sidebarData, vocabulary])

  const activeApp = useMemo(() => {
    return apps
      .filter((app) => location.pathname === app.path || location.pathname.startsWith(`${app.path}/`))
      .sort((a, b) => (b.path?.length || 0) - (a.path?.length || 0))[0]
  }, [apps, location.pathname])

  const filteredApps = apps.filter((app) => {
    const term = query.trim().toLowerCase()
    if (!term) return true
    return `${app.label} ${app.name}`.toLowerCase().includes(term)
  })

  const ActiveIcon = resolveIcon(activeApp?.icon || 'LayoutGrid')

  useEffect(() => {
    const onDown = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [])

  return (
    <div className="relative shrink-0" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex h-11 max-w-[260px] items-center gap-2 rounded-[calc(var(--aras-radius)*0.68)] border border-[var(--aras-border)] bg-[var(--aras-panel-soft)]/75 px-3 text-left shadow-inner transition-all hover:bg-[var(--aras-panel)]"
      >
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-[var(--aras-panel)] text-[var(--aras-accent)] shadow-sm ring-1 ring-[var(--aras-border)]">
          <ActiveIcon size={17} />
        </span>
        <span className="hidden min-w-0 sm:block">
          <span className="block text-[10px] font-black uppercase tracking-[0.14em] text-[var(--aras-muted)]">Workspace</span>
          <span className="block truncate text-sm font-extrabold text-[var(--aras-text)]">
            {activeApp?.label || 'Home'}
          </span>
        </span>
        <ChevronDown size={15} className={`shrink-0 text-[var(--aras-muted)] transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute left-0 top-full z-50 mt-2 w-[320px] overflow-hidden rounded-[calc(var(--aras-radius)*0.82)] border border-[var(--aras-border)] bg-[var(--aras-panel)] shadow-[0_22px_55px_-22px_rgba(15,23,42,0.38)]">
          <div className="border-b border-[var(--aras-border)] bg-[var(--aras-panel-soft)]/60 p-2">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--aras-muted)]" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Find app or module..."
                className="h-10 w-full rounded-xl border border-[var(--aras-border)] bg-[var(--aras-panel)] pl-9 pr-3 text-sm font-semibold text-[var(--aras-text)] outline-none placeholder:text-[var(--aras-muted)] focus:border-[var(--aras-accent)]"
              />
            </div>
          </div>
          <div className="max-h-[360px] overflow-y-auto p-2">
            {filteredApps.map((app) => {
              const Icon = resolveIcon(app.icon || 'Box')
              const active = activeApp?.name === app.name
              return (
                <Link
                  key={`${app.name}-${app.path}`}
                  to={app.path || `/${app.name}`}
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all hover:bg-[var(--aras-panel-soft)]"
                  style={active ? { backgroundColor: 'color-mix(in srgb, var(--aras-accent) 10%, transparent)' } : undefined}
                >
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[var(--aras-panel-soft)] text-[var(--aras-accent)]">
                    <Icon size={18} />
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-extrabold text-[var(--aras-text)]">{app.label}</span>
                    <span className="block text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--aras-muted)]">
                      {'parentLabel' in app ? (app.parentLabel as string) : 'App'}
                    </span>
                  </span>
                </Link>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

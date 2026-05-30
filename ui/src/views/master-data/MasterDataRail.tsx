import { Database } from 'lucide-react'
import { useEffect, useState } from 'react'
import { masterDataApi, type MasterDataEntity, type MasterDataSchema } from '../../lib/api'
import { resolveIcon } from '../../lib/iconUtils'
import { useAras } from '../../aras-core/hooks/useAras'

interface MasterDataRailProps {
  selectedEntity: string | null
  onSelect: (entity: MasterDataEntity) => void
  onLoaded?: (schema: MasterDataSchema) => void
}

export default function MasterDataRail({ selectedEntity, onSelect, onLoaded }: MasterDataRailProps) {
  const { notify } = useAras()
  const [schema, setSchema] = useState<MasterDataSchema>({ groups: [] })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    masterDataApi.getSchema()
      .then((nextSchema) => {
        if (cancelled) return
        setSchema(nextSchema)
        onLoaded?.(nextSchema)
      })
      .catch((err) => {
        if (cancelled) return
        notify(err.message || 'Failed to load master data schema', 'error')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [notify, onLoaded])

  if (loading) {
    return (
      <div className="flex flex-col gap-2 p-3">
        {Array.from({ length: 8 }).map((_, index) => (
          <div key={index} className="flex items-center gap-3 rounded-[var(--aras-radius)] px-3 py-2">
            <div className="h-8 w-8 animate-pulse rounded-[var(--aras-radius)] bg-[var(--surface-2)]" />
            <div className="min-w-0 flex-1">
              <div className="h-3 w-28 animate-pulse rounded bg-[var(--surface-2)]" />
              <div className="mt-2 h-2 w-16 animate-pulse rounded bg-[var(--surface-2)]" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (schema.groups.length === 0) {
    return (
      <div className="p-5 text-center text-[12px] text-[var(--text-3)]">
        No master data entities are available.
      </div>
    )
  }

  return (
    <nav className="flex flex-col gap-1 p-3" aria-label="Master data entities">
      {schema.groups.map((group) => (
        <div key={group.key} className="mb-2">
          <div className="arc-mono mb-1 px-3 pt-1 text-[10px] uppercase tracking-[0.14em] text-[var(--text-3)]">
            {group.label}
          </div>
          {group.entities.map((entity) => {
            const Icon = entity.icon ? resolveIcon(entity.icon) : Database
            const active = selectedEntity === entity.key
            return (
              <button
                key={entity.key}
                type="button"
                onClick={() => onSelect(entity)}
                className={`flex w-full items-center gap-3 rounded-[var(--aras-radius)] px-3 py-2 text-left transition-colors ${
                  active
                    ? 'border border-[var(--line)] bg-[var(--surface)] text-[var(--text)]'
                    : 'border border-transparent text-[var(--text-2)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]'
                }`}
              >
                <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-[var(--aras-radius)] ${active ? 'bg-[var(--accent)] text-white' : 'bg-[var(--surface-2)] text-[var(--text-3)]'}`}>
                  <Icon size={15} />
                </span>
                <span className="min-w-0">
                  <span className="block truncate text-[13px] font-semibold">{entity.label || entity.key}</span>
                  <span className="arc-mono block truncate text-[10px] uppercase tracking-[0.12em] text-[var(--text-3)]">{entity.key}</span>
                </span>
              </button>
            )
          })}
        </div>
      ))}
    </nav>
  )
}

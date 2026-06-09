import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Database } from 'lucide-react'
import { DynamicForm } from '../../aras-core/components/DynamicForm'
import ListView from '../../aras-core/components/ListView'
import { masterDataApi, type MasterDataEntity, type MasterDataSchema } from '../../lib/api'
import { cleanResourcePath } from '../../lib/resourceUtils'
import { resolveIcon } from '../../lib/iconUtils'
import { useAras } from '../../aras-core/hooks/useAras'

const SINGLETON_SETTINGS_ENTITIES = new Set(['organization'])

function resourceFromEntity(entity: MasterDataEntity) {
  if (entity.resource) return cleanResourcePath(entity.resource)
  if (entity.model_table) return cleanResourcePath(entity.model_table)
  return cleanResourcePath(entity.resource_url.replace(/^\/api\/v1\/?/, ''))
}

// claude-opus-4-8 — Master Data as a tabbed content page inside the Settings Hub shell
// (mirrors the Access Control pattern: the Settings sidebar stays the single left rail;
// entities surface as a grouped horizontal tab strip in the content area).
export default function MasterDataPage() {
  const navigate = useNavigate()
  const { notify } = useAras()
  const [searchParams, setSearchParams] = useSearchParams()
  const [schema, setSchema] = useState<MasterDataSchema>({ groups: [] })
  const [loading, setLoading] = useState(true)
  const [selectedKey, setSelectedKey] = useState<string | null>(searchParams.get('entity'))
  const recordId = searchParams.get('id')

  const entities = useMemo(
    () => schema.groups.flatMap((group) => group.entities).filter((e) => !SINGLETON_SETTINGS_ENTITIES.has(e.key)),
    [schema]
  )

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    masterDataApi.getSchema()
      .then((next) => {
        if (cancelled) return
        const filtered = {
          groups: next.groups
            .map((group) => ({ ...group, entities: group.entities.filter((e) => !SINGLETON_SETTINGS_ENTITIES.has(e.key)) }))
            .filter((group) => group.entities.length > 0),
        }
        setSchema(filtered)
        const current = new URLSearchParams(window.location.search).get('entity')
        const first = filtered.groups[0]?.entities[0]
        if (!current && first) {
          setSelectedKey(first.key)
          setSearchParams({ entity: first.key }, { replace: true })
        }
      })
      .catch((err) => { if (!cancelled) notify(err.message || 'Failed to load master data schema', 'error') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [notify, setSearchParams])

  useEffect(() => {
    const next = searchParams.get('entity')
    if (next && SINGLETON_SETTINGS_ENTITIES.has(next)) {
      navigate('/admin/settings', { replace: true })
      return
    }
    if (next && next !== selectedKey) setSelectedKey(next)
  }, [navigate, searchParams, selectedKey])

  const selectEntity = (entity: MasterDataEntity) => {
    if (entity.key === selectedKey && !recordId) return
    setSelectedKey(entity.key)
    setSearchParams({ entity: entity.key })
  }

  const selectedEntity = useMemo(
    () => entities.find((e) => e.key === selectedKey) || null,
    [entities, selectedKey]
  )
  const resource = selectedEntity ? resourceFromEntity(selectedEntity) : ''

  const returnToList = () => {
    if (selectedEntity) setSearchParams({ entity: selectedEntity.key })
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Grouped, scrollable entity tab strip — the content-area nav, no second sidebar. */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 overflow-x-auto rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-2">
        {loading ? (
          Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-8 w-28 animate-pulse rounded-[var(--aras-radius)] bg-[var(--surface-2)]" />
          ))
        ) : entities.length === 0 ? (
          <div className="px-3 py-1.5 text-[12px] text-[var(--text-3)]">No master data entities are available.</div>
        ) : (
          schema.groups.map((group) => (
            <div key={group.key} className="flex items-center gap-1.5">
              <span className="arc-mono shrink-0 px-1 text-[10px] uppercase tracking-[0.14em] text-[var(--text-3)]">{group.label}</span>
              {group.entities.map((entity) => {
                const Icon = entity.icon ? resolveIcon(entity.icon) : Database
                const active = selectedKey === entity.key
                return (
                  <button
                    key={entity.key}
                    type="button"
                    onClick={() => selectEntity(entity)}
                    className={`inline-flex shrink-0 items-center gap-2 rounded-[var(--aras-radius)] px-3 py-1.5 text-[13px] font-semibold transition-colors ${
                      active ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-2)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]'
                    }`}
                  >
                    <Icon size={14} />
                    {entity.label || entity.key}
                  </button>
                )
              })}
            </div>
          ))
        )}
      </div>

      {selectedEntity && resource ? (
        <div className="h-[calc(100vh-220px)] min-h-[480px] overflow-hidden rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)]">
          {recordId ? (
            <DynamicForm
              key={`${resource}:${recordId}`}
              resource={resource}
              id={recordId}
              onSave={returnToList}
              onCancel={returnToList}
            />
          ) : (
            <ListView
              key={resource}
              resource={resource}
              embedded
              onRowClick={(id) => setSearchParams({ entity: selectedEntity.key, id: String(id) })}
              onAdd={() => setSearchParams({ entity: selectedEntity.key, id: 'new' })}
            />
          )}
        </div>
      ) : !loading && (
        <div className="max-w-[920px] rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-8 text-center text-[13px] text-[var(--text-3)]">
          Select a master data entity to manage records.
        </div>
      )}
    </div>
  )
}

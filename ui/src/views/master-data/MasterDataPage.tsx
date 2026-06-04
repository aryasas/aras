import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Database } from 'lucide-react'
import { DynamicForm } from '../../aras-core/components/DynamicForm'
import ListView from '../../aras-core/components/ListView'
import { useUIStore } from '../../store/uiStore'
import { cleanResourcePath } from '../../lib/resourceUtils'
import type { MasterDataEntity, MasterDataSchema } from '../../lib/api'
import MasterDataRail from './MasterDataRail'

const SINGLETON_SETTINGS_ENTITIES = new Set(['organization'])

function resourceFromEntity(entity: MasterDataEntity) {
  return cleanResourcePath(entity.resource_url.replace(/^\/api\/v1\/?/, ''))
}

export default function MasterDataPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const setPageTitle = useUIStore((state) => state.setPageTitle)
  const [entities, setEntities] = useState<MasterDataEntity[]>([])
  const [selectedKey, setSelectedKey] = useState<string | null>(searchParams.get('entity'))
  const recordId = searchParams.get('id')

  useEffect(() => {
    setPageTitle('Master Data', 'Manage shared and module-owned reference records from one surface.', 'ADMIN / MASTER DATA')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  useEffect(() => {
    const next = searchParams.get('entity')
    if (next && SINGLETON_SETTINGS_ENTITIES.has(next)) {
      navigate('/admin/settings', { replace: true })
      return
    }
    if (next && next !== selectedKey) setSelectedKey(next)
  }, [navigate, searchParams, selectedKey])

  const handleLoaded = useCallback((schema: MasterDataSchema) => {
    const nextEntities = schema.groups
      .flatMap((group) => group.entities)
      .filter((entity) => !SINGLETON_SETTINGS_ENTITIES.has(entity.key))
    setEntities(nextEntities)
    const current = new URLSearchParams(window.location.search).get('entity')
    if (!current && nextEntities[0]) {
      setSelectedKey(nextEntities[0].key)
      setSearchParams({ entity: nextEntities[0].key }, { replace: true })
    }
  }, [setSearchParams])

  const selectEntity = (entity: MasterDataEntity) => {
    if (entity.key === selectedKey && !recordId) return
    setSelectedKey(entity.key)
    setSearchParams({ entity: entity.key })
  }

  const selectedEntity = useMemo(
    () => entities.find((entity) => entity.key === selectedKey) || null,
    [entities, selectedKey]
  )
  const resource = selectedEntity ? resourceFromEntity(selectedEntity) : ''

  const returnToList = () => {
    if (selectedEntity) setSearchParams({ entity: selectedEntity.key })
  }

  return (
    <div className="flex min-h-full bg-[var(--bg)]">
      <aside className="hidden w-72 shrink-0 border-r border-[var(--line)] bg-[var(--bg-2)] md:block">
        <div className="border-b border-[var(--line)] px-5 py-4">
          <div className="arc-id arc-dim2">admin/master-data</div>
          <h1 className="mt-1 text-[16px] font-semibold text-[var(--text)]">Master Data</h1>
        </div>
        <MasterDataRail selectedEntity={selectedKey} onSelect={selectEntity} onLoaded={handleLoaded} />
      </aside>

      <main className="min-w-0 flex-1 overflow-y-auto px-4 py-5 md:px-8">
        <div className="mb-5 md:hidden">
          <MasterDataRail selectedEntity={selectedKey} onSelect={selectEntity} onLoaded={handleLoaded} />
        </div>

        <div className="mb-6 flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-[var(--aras-radius)] bg-[var(--surface-2)] text-[var(--accent)]">
            <Database size={19} />
          </span>
          <div className="min-w-0">
            <h2 className="truncate text-[20px] font-semibold text-[var(--text)]">{selectedEntity?.label || 'Master Data'}</h2>
            <p className="arc-mono mt-0.5 truncate text-[10px] uppercase tracking-[0.14em] text-[var(--text-3)]">
              {selectedEntity ? `entity/${selectedEntity.key}` : 'select an entity'}
            </p>
          </div>
        </div>

        {selectedEntity && resource ? (
          <div className="h-[calc(100vh-150px)] min-h-[520px]">
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
                onRowClick={(id) => setSearchParams({ entity: selectedEntity.key, id: String(id) })}
                onAdd={() => setSearchParams({ entity: selectedEntity.key, id: 'new' })}
              />
            )}
          </div>
        ) : (
          <div className="max-w-[920px] rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-8 text-center text-[13px] text-[var(--text-3)]">
            Select a master data entity to manage records.
          </div>
        )}
      </main>
    </div>
  )
}

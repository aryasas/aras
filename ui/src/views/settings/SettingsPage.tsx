import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Settings } from 'lucide-react'
import SettingsForm from './SettingsForm'
import SettingsNamespaceList from './SettingsNamespaceList'
import type { SettingsNamespace } from '../../lib/api'
import { useUIStore } from '../../store/uiStore'

function namespaceFromSectionKey(sectionKey: string | null) {
  if (!sectionKey || !sectionKey.includes('.')) return null
  return sectionKey.split('.').slice(0, -1).join('.')
}

export default function SettingsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const setPageTitle = useUIStore((state) => state.setPageTitle)
  const [namespaces, setNamespaces] = useState<SettingsNamespace[]>([])
  const [selectedNamespace, setSelectedNamespace] = useState<string | null>(
    searchParams.get('ns') || namespaceFromSectionKey(searchParams.get('section'))
  )
  const [dirty, setDirty] = useState(false)
  const focusedSectionKey = searchParams.get('section')

  const setRouteSelection = useCallback((namespace: string, sectionKey?: string | null, replace = false) => {
    const nextParams = new URLSearchParams(searchParams)
    nextParams.set('ns', namespace)
    if (sectionKey) nextParams.set('section', sectionKey)
    else nextParams.delete('section')
    setSearchParams(nextParams, { replace })
  }, [searchParams, setSearchParams])

  useEffect(() => {
    setPageTitle('Settings', 'Configure framework and app settings from one surface.', 'ADMIN / SETTINGS')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  useEffect(() => {
    const next = searchParams.get('ns') || namespaceFromSectionKey(searchParams.get('section'))
    if (next && next !== selectedNamespace) setSelectedNamespace(next)
  }, [searchParams, selectedNamespace])

  const handleLoaded = useCallback((items: SettingsNamespace[]) => {
    setNamespaces(items)
    const nextSearch = new URLSearchParams(window.location.search)
    const currentSection = nextSearch.get('section')
    const current = nextSearch.get('ns') || namespaceFromSectionKey(currentSection)
    if (!current && items[0]) {
      setSelectedNamespace(items[0].name)
      setRouteSelection(items[0].name, currentSection, true)
    }
  }, [setRouteSelection])

  const selectNamespace = (namespace: string) => {
    if (namespace === selectedNamespace) return
    if (dirty && !window.confirm('Discard unsaved settings changes?')) return
    setSelectedNamespace(namespace)
    setRouteSelection(namespace, null)
  }

  const selected = useMemo(
    () => namespaces.find((item) => item.name === selectedNamespace),
    [namespaces, selectedNamespace]
  )

  return (
    <div className="flex min-h-full bg-[var(--bg)]">
      <aside className="hidden w-72 shrink-0 border-r border-[var(--line)] bg-[var(--bg-2)] md:block">
        <div className="border-b border-[var(--line)] px-5 py-4">
          <div className="arc-id arc-dim2">settings</div>
          <h1 className="mt-1 text-[16px] font-semibold text-[var(--text)]">App Settings</h1>
        </div>
        <SettingsNamespaceList selectedNamespace={selectedNamespace} onSelect={selectNamespace} onLoaded={handleLoaded} />
      </aside>

      <main className="min-w-0 flex-1 overflow-y-auto px-4 py-5 md:px-8">
        <div className="mb-5 md:hidden">
          <SettingsNamespaceList selectedNamespace={selectedNamespace} onSelect={selectNamespace} onLoaded={handleLoaded} />
        </div>

        <div className="mb-6 flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-[var(--aras-radius)] bg-[var(--surface-2)] text-[var(--accent)]">
            <Settings size={19} />
          </span>
          <div className="min-w-0">
            <h2 className="truncate text-[20px] font-semibold text-[var(--text)]">{selected?.label || selectedNamespace || 'Settings'}</h2>
            <p className="arc-mono mt-0.5 truncate text-[10px] uppercase tracking-[0.14em] text-[var(--text-3)]">
              {selectedNamespace ? `namespace/${selectedNamespace}` : 'select a namespace'}
            </p>
          </div>
        </div>

        {selectedNamespace ? (
          <SettingsForm
            key={selectedNamespace}
            namespace={selectedNamespace}
            focusSectionKey={focusedSectionKey}
            onDirtyChange={setDirty}
          />
        ) : (
          <div className="max-w-[920px] rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-8 text-center text-[13px] text-[var(--text-3)]">
            Select an app settings namespace to edit settings.
          </div>
        )}
      </main>
    </div>
  )
}

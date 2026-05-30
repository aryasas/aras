import { useEffect, useMemo, useState, type ComponentType } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { Flag, Settings } from 'lucide-react'
import { configQueryClient, useSection, useSections } from '../../lib/config'
import type { ConfigSectionDetail, ConfigSectionSummary } from '../../lib/config'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'
import { resolveIcon } from '../../lib/iconUtils'
import SectionForm from './SectionForm'
import FeatureFlagsPanel from './FeatureFlagsPanel'
import CompanyForm from './sections/CompanyForm'

type SectionRenderer = ComponentType<{ section: ConfigSectionDetail; onSaved?: () => void }>

const sectionRenderers = new Map<string, SectionRenderer>()

export function registerSectionRenderer(key: string, renderer: SectionRenderer) {
  sectionRenderers.set(key, renderer)
}

registerSectionRenderer('core_config.company', CompanyForm)

function sectionOwner(section: ConfigSectionSummary) {
  return section.app || section.key.split('.')[0] || 'core'
}

function groupLabel(scope: string, owner?: string) {
  if (scope === 'core') return 'General'
  if (scope === 'module') return `Module: ${owner || 'App'}`
  if (scope === 'shared') return 'Shared'
  return 'Feature Flags'
}

function ConfigPageInner() {
  const setPageTitle = useUIStore((state) => state.setPageTitle)
  const user = useAuthStore((state) => state.user)
  const sectionsQuery = useSections()
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [showFeatureFlags, setShowFeatureFlags] = useState(false)

  useEffect(() => {
    setPageTitle('Workspace Settings', 'Manage tenant configuration.', 'WORKSPACE / CONFIG')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  const visibleSections = useMemo(() => {
    return (sectionsQuery.data || []).filter((section) => section.scope !== 'feature')
  }, [sectionsQuery.data])

  useEffect(() => {
    if (!selectedKey && visibleSections.length > 0) {
      const company = visibleSections.find((section) => section.key === 'core_config.company')
      setSelectedKey(company?.key || visibleSections[0].key)
    }
  }, [selectedKey, visibleSections])

  const groupedSections = useMemo(() => {
    const groups: Array<{ id: string; label: string; sections: ConfigSectionSummary[] }> = []
    const byGroup = new Map<string, ConfigSectionSummary[]>()

    visibleSections.forEach((section) => {
      const owner = sectionOwner(section)
      const label = groupLabel(section.scope, owner)
      byGroup.set(label, [...(byGroup.get(label) || []), section])
    })

    Array.from(byGroup.entries()).forEach(([label, sections]) => {
      groups.push({ id: label, label, sections })
    })

    return groups.sort((a, b) => {
      const order = ['General', 'Shared']
      const ai = order.includes(a.label) ? order.indexOf(a.label) : 1
      const bi = order.includes(b.label) ? order.indexOf(b.label) : 1
      return ai - bi || a.label.localeCompare(b.label)
    })
  }, [visibleSections])

  const sectionQuery = useSection(showFeatureFlags ? null : selectedKey)
  const section = sectionQuery.data
  const Renderer = section ? sectionRenderers.get(section.key) || SectionForm : SectionForm
  const canSeeFeatureFlags = Boolean(user?.is_admin)

  return (
    <div className="flex min-h-full bg-[var(--aras-bg-main)]">
      <aside className="hidden w-72 shrink-0 border-r border-[var(--aras-border)] bg-[var(--aras-panel-soft)] p-4 md:block">
        <div className="mb-4 px-2">
          <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--aras-muted)]">Workspace</div>
          <div className="mt-1 text-[15px] font-semibold text-[var(--aras-text)]">Settings</div>
        </div>

        <nav className="flex flex-col gap-5">
          {sectionsQuery.isLoading ? (
            <div className="px-2 py-6 text-[12px] text-[var(--aras-muted)]">Loading sections...</div>
          ) : groupedSections.map((group) => (
            <section key={group.id}>
              <h2 className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--aras-muted)]">{group.label}</h2>
              <div className="flex flex-col gap-1">
                {group.sections.map((item) => {
                  const Icon = resolveIcon(item.icon || 'Settings')
                  const active = !showFeatureFlags && selectedKey === item.key
                  return (
                    <button
                      type="button"
                      key={item.key}
                      onClick={() => {
                        setShowFeatureFlags(false)
                        setSelectedKey(item.key)
                      }}
                      className={`flex items-center gap-2 rounded-[var(--aras-radius)] px-2 py-2 text-left text-[13px] ${active ? 'bg-[var(--aras-panel)] text-[var(--aras-text)] shadow-sm' : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel)] hover:text-[var(--aras-text)]'}`}
                    >
                      <Icon size={15} className="shrink-0" />
                      <span className="truncate">{item.label}</span>
                    </button>
                  )
                })}
              </div>
            </section>
          ))}

          {canSeeFeatureFlags ? (
            <section>
              <h2 className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--aras-muted)]">Feature Flags</h2>
              <button
                type="button"
                onClick={() => setShowFeatureFlags(true)}
                className={`flex w-full items-center gap-2 rounded-[var(--aras-radius)] px-2 py-2 text-left text-[13px] ${showFeatureFlags ? 'bg-[var(--aras-panel)] text-[var(--aras-text)] shadow-sm' : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel)] hover:text-[var(--aras-text)]'}`}
              >
                <Flag size={15} className="shrink-0" />
                <span className="truncate">Feature Flags</span>
              </button>
            </section>
          ) : null}
        </nav>
      </aside>

      <main className="min-w-0 flex-1 px-4 py-6 md:px-8">
        <div className="mb-5 flex gap-2 overflow-x-auto md:hidden">
          {visibleSections.map((item) => (
            <button
              type="button"
              key={item.key}
              onClick={() => {
                setShowFeatureFlags(false)
                setSelectedKey(item.key)
              }}
              className={`shrink-0 rounded-[var(--aras-radius)] border px-3 py-2 text-[12px] font-semibold ${selectedKey === item.key ? 'border-[var(--aras-accent)] text-[var(--aras-accent)]' : 'border-[var(--aras-border)] text-[var(--aras-muted)]'}`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {showFeatureFlags ? (
          <FeatureFlagsPanel />
        ) : sectionQuery.isLoading || sectionsQuery.isLoading ? (
          <div className="mx-auto flex max-w-[880px] items-center gap-2 rounded-[var(--aras-radius-lg)] border border-[var(--aras-border)] bg-[var(--aras-panel)] p-6 text-[13px] text-[var(--aras-muted)]">
            <Settings size={16} />
            Loading settings...
          </div>
        ) : section ? (
          <Renderer section={section} />
        ) : (
          <div className="mx-auto max-w-[880px] rounded-[var(--aras-radius-lg)] border border-[var(--aras-border)] bg-[var(--aras-panel)] p-8 text-center text-[13px] text-[var(--aras-muted)]">
            No configuration sections are available.
          </div>
        )}
      </main>
    </div>
  )
}

export default function ConfigPage() {
  return (
    <QueryClientProvider client={configQueryClient}>
      <ConfigPageInner />
    </QueryClientProvider>
  )
}

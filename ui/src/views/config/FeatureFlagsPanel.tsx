import { useMemo } from 'react'
import { ToggleLeft, ToggleRight } from 'lucide-react'
import { useSections, useSection, setConfig } from '../../lib/config'
import type { ConfigSectionSummary } from '../../lib/config'

function ownerName(section: ConfigSectionSummary) {
  if (section.app) return section.app
  return section.key.split('.')[0] || 'core'
}

function FeatureFlagSection({ section }: { section: ConfigSectionSummary }) {
  const sectionQuery = useSection(section.key)

  if (sectionQuery.isLoading) {
    return <div className="rounded-[var(--aras-radius)] border border-[var(--aras-border)] p-4 text-[12px] text-[var(--aras-muted)]">Loading flags...</div>
  }

  const fields = sectionQuery.data?.fields || []

  return (
    <div className="overflow-hidden rounded-[var(--aras-radius-lg)] border border-[var(--aras-border)] bg-[var(--aras-panel)]">
      <div className="border-b border-[var(--aras-border)] px-4 py-3">
        <div className="text-[13px] font-semibold text-[var(--aras-text)]">{section.label}</div>
        <div className="text-[11px] text-[var(--aras-muted)]">{section.key}</div>
      </div>
      <div className="divide-y divide-[var(--aras-border)]">
        {fields.length === 0 ? (
          <div className="px-4 py-5 text-[12px] text-[var(--aras-muted)]">No flags registered.</div>
        ) : fields.map((field: NonNullable<typeof sectionQuery.data>['fields'][number]) => {
          const enabled = Boolean(field.value ?? field.default)
          return (
            <button
              key={field.key}
              type="button"
              onClick={() => setConfig(`${section.key}.${field.key}`, !enabled)}
              className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left hover:bg-[var(--aras-panel-soft)]"
            >
              <span className="min-w-0">
                <span className="block truncate text-[13px] font-medium text-[var(--aras-text)]">{field.label || field.key}</span>
                {field.help ? <span className="block truncate text-[12px] text-[var(--aras-muted)]">{field.help}</span> : null}
              </span>
              {enabled ? <ToggleRight size={24} className="shrink-0 text-[var(--aras-accent)]" /> : <ToggleLeft size={24} className="shrink-0 text-[var(--aras-muted)]" />}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default function FeatureFlagsPanel() {
  const sectionsQuery = useSections({ scope: 'feature' })
  const grouped = useMemo(() => {
    return (sectionsQuery.data || []).reduce<Record<string, ConfigSectionSummary[]>>((acc, section: ConfigSectionSummary) => {
      const owner = ownerName(section)
      acc[owner] = [...(acc[owner] || []), section]
      return acc
    }, {})
  }, [sectionsQuery.data])

  if (sectionsQuery.isLoading) {
    return <div className="text-[13px] text-[var(--aras-muted)]">Loading feature flags...</div>
  }

  return (
    <div className="mx-auto flex w-full max-w-[880px] flex-col gap-6">
      <div>
        <h1 className="text-[22px] font-semibold text-[var(--aras-text)]">Feature Flags</h1>
        <p className="mt-1 text-[13px] text-[var(--aras-muted)]">Tenant-scoped feature settings grouped by app.</p>
      </div>
      {Object.keys(grouped).length === 0 ? (
        <div className="rounded-[var(--aras-radius-lg)] border border-[var(--aras-border)] bg-[var(--aras-panel)] p-8 text-center text-[13px] text-[var(--aras-muted)]">
          No feature flags are registered.
        </div>
      ) : Object.entries(grouped).map(([owner, sections]) => (
        <section key={owner} className="flex flex-col gap-3">
          <h2 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--aras-muted)]">{owner}</h2>
          {sections.map((section) => <FeatureFlagSection key={section.key} section={section} />)}
        </section>
      ))}
    </div>
  )
}

import { Building2 } from 'lucide-react'
import SimpleCombobox, { type SimpleOption } from '../../aras-core/components/SimpleCombobox'
import { ALL_ORGS, useAuthStore } from '../../store/authStore'

function badgeLabel(unitType?: string, isGroup?: boolean) {
  if (isGroup) return 'Group'
  if (unitType) return unitType
  return ''
}

// claude-opus-4-8
export default function WorkspaceSwitcher() {
  const organizations = useAuthStore((state) => state.organizations)
  const activeOrgId = useAuthStore((state) => state.activeOrgId)
  const setActiveOrg = useAuthStore((state) => state.setActiveOrg)

  if (organizations.length === 0) return null

  const options: SimpleOption[] = [
    { label: 'All Organizations', value: ALL_ORGS },
    ...organizations.map((organization) => {
      const badge = badgeLabel(organization.unit_type, organization.is_group)
      return {
        label: badge ? `${organization.name} · ${badge}` : organization.name,
        value: organization.id,
      }
    }),
  ]

  const activeOrganization = organizations.find((organization) => organization.id === activeOrgId) || null
  const singleBadge = badgeLabel(activeOrganization?.unit_type, activeOrganization?.is_group)
  const badgeByValue = new Map<number, string>(
    organizations.map((organization) => [organization.id, badgeLabel(organization.unit_type, organization.is_group)])
  )

  const renderBadge = (badge: string) => badge ? (
    <span className="rounded-full bg-[var(--surface-2)] px-2 py-0.5 text-[10px] uppercase tracking-[0.08em] text-[var(--text-3)]">
      {badge}
    </span>
  ) : null

  return (
    <div className="z-50 flex items-center gap-2 max-sm:hidden">
      <Building2 size={13} className="text-[var(--text-3)]" />
      {organizations.length === 1 ? (
        <div className="inline-flex items-center gap-2 rounded-full border border-[var(--line)] px-3 py-1 text-[12px] text-[var(--text-2)]">
          <span className="truncate">{activeOrganization?.name || organizations[0].name}</span>
          {renderBadge(singleBadge)}
        </div>
      ) : (
        <SimpleCombobox
          width={220}
          options={options}
          value={activeOrgId ?? ALL_ORGS}
          onChange={(value) => setActiveOrg(Number(value))}
          placeholder="Select Workspace"
          searchable
          searchPlaceholder="Search workspaces..."
          renderValue={(selected) => {
            const badge = badgeByValue.get(Number(selected?.value))
            const label = badge && selected ? selected.label.replace(` · ${badge}`, '') : selected?.label
            return (
              <span className="flex items-center gap-2">
                <span className="truncate">{label || 'Select Workspace'}</span>
                {renderBadge(badge || '')}
              </span>
            )
          }}
          renderOption={(option) => {
            const badge = badgeByValue.get(Number(option.value))
            const label = badge ? option.label.replace(` · ${badge}`, '') : option.label
            return (
              <span className="flex items-center gap-2">
                <span className="truncate">{label}</span>
                {renderBadge(badge || '')}
              </span>
            )
          }}
        />
      )}
    </div>
  )
}

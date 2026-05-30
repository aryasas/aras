import SectionForm from '../SectionForm'
import type { ConfigSectionDetail } from '../../../lib/config'

interface CompanyFormProps {
  section: ConfigSectionDetail
  onSaved?: () => void
}

export default function CompanyForm({ section, onSaved }: CompanyFormProps) {
  const logoField = section.fields.find((field) => field.key === 'logo')
  const nameField = section.fields.find((field) => field.key === 'name')

  return (
    <div className="mx-auto w-full max-w-[880px]">
      <div className="mb-6 flex items-center gap-4 rounded-[var(--aras-radius-lg)] border border-[var(--aras-border)] bg-[var(--aras-panel)] p-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-[var(--aras-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel-soft)]">
          {logoField?.value ? (
            <img src={String(logoField.value)} alt="" className="h-full w-full rounded-[var(--aras-radius)] object-contain" />
          ) : (
            <span className="text-[20px] font-semibold text-[var(--aras-muted)]">{String(nameField?.value || 'W').slice(0, 1)}</span>
          )}
        </div>
        <div className="min-w-0">
          <div className="truncate text-[15px] font-semibold text-[var(--aras-text)]">{String(nameField?.value || 'My Workspace')}</div>
          <div className="mt-1 text-[12px] text-[var(--aras-muted)]">Workspace identity and operating defaults</div>
        </div>
      </div>
      <SectionForm section={section} onSaved={onSaved} />
    </div>
  )
}

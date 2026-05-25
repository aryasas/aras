import { Building2, CheckCircle2, LogOut } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function OrganizationPicker() {
  const organizations = useAuthStore((state) => state.organizations)
  const activeOrgId = useAuthStore((state) => state.activeOrgId)
  const setActiveOrg = useAuthStore((state) => state.setActiveOrg)
  const logout = useAuthStore((state) => state.logout)
  const navigate = useNavigate()

  const handleSelectOrganization = (orgId: number) => {
    setActiveOrg(orgId)
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-[var(--app-panel-soft)] flex items-center justify-center p-4 font-sans">
      <div className="max-w-lg w-full bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] shadow-xl shadow-slate-200 border border-[var(--app-border)] overflow-hidden">
        <div className="p-8 border-b border-[var(--app-border)]">
          <div className="w-14 h-14 bg-[var(--app-accent)] rounded-[var(--app-radius-lg)] flex items-center justify-center shadow-lg shadow-indigo-100 mb-5">
            <Building2 className="text-white" size={26} />
          </div>
          <h1 className="text-2xl font-bold text-[var(--app-text)]">Select Organization</h1>
          <p className="text-[var(--app-muted)] mt-2">Choose the organization workspace for this session.</p>
        </div>

        <div className="p-4 space-y-2">
          {organizations.map((organization) => {
            const isActive = organization.id === activeOrgId

            return (
              <button
                key={organization.id}
                type="button"
                onClick={() => handleSelectOrganization(organization.id)}
                className="w-full flex items-center justify-between gap-4 px-4 py-4 rounded-[var(--app-radius-lg)] border border-[var(--app-border)] bg-[var(--app-panel)] text-left hover:border-indigo-200 hover:bg-[var(--app-accent-glow)]/50 transition-colors"
              >
                <span className="flex items-center gap-3 min-w-0">
                  <span className="h-10 w-10 rounded-[var(--app-radius)] bg-[var(--app-panel-soft)] text-slate-600 flex items-center justify-center shrink-0">
                    <Building2 size={18} />
                  </span>
                  <span className="font-semibold text-[var(--app-text)] truncate">{organization.name}</span>
                </span>
                {isActive && <CheckCircle2 className="text-[var(--app-accent)] shrink-0" size={20} />}
              </button>
            )
          })}
        </div>

        <div className="px-8 pb-8 pt-2">
          <button
            type="button"
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 py-3 text-[var(--app-muted)] hover:text-rose-600 transition-colors text-sm font-semibold"
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </div>
    </div>
  )
}

import { lazy, Suspense, useState } from 'react'
import { Users, Shield, Lock, Building2, SlidersHorizontal } from 'lucide-react'
import ListView from '../aras-core/components/ListView'
import { DynamicForm } from '../aras-core/components/DynamicForm'

const UserOrgAccess = lazy(() => import('./ErpUserAccess'))
const AccessAdvanced = lazy(() => import('./devtools/AccessTab'))

type TabId = 'roles' | 'permissions' | 'users' | 'org-access' | 'advanced'

const CRUD_TABS = [
  { id: 'roles' as const, label: 'Roles', icon: Shield, resource: 'core_roles' },
  { id: 'permissions' as const, label: 'Permissions', icon: Lock, resource: 'core_permissions' },
  { id: 'users' as const, label: 'Users', icon: Users, resource: 'core_users' },
]

// claude-opus-4-8 — canonical Access Control surface (CRUD + org access + diagnostics)
const RBACManager = () => {
  const [activeTab, setActiveTab] = useState<TabId>('roles')
  const [editingId, setEditingId] = useState<string | number | null>(null)

  const crud = CRUD_TABS.find((t) => t.id === activeTab)

  const select = (id: TabId) => { setActiveTab(id); setEditingId(null) }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-1 rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-1 w-fit">
        {CRUD_TABS.map((tab) => (
          <TabButton key={tab.id} active={activeTab === tab.id} onClick={() => select(tab.id)} icon={<tab.icon size={16} />} label={tab.label} />
        ))}
        <TabButton active={activeTab === 'org-access'} onClick={() => select('org-access')} icon={<Building2 size={16} />} label="Org Access" />
        <TabButton active={activeTab === 'advanced'} onClick={() => select('advanced')} icon={<SlidersHorizontal size={16} />} label="Advanced" />
      </div>

      {activeTab === 'org-access' ? (
        <Suspense fallback={<Loading />}><UserOrgAccess /></Suspense>
      ) : activeTab === 'advanced' ? (
        <Suspense fallback={<Loading />}><AccessAdvanced /></Suspense>
      ) : editingId ? (
        <DynamicForm
          resource={crud!.resource}
          id={editingId}
          onSave={() => setEditingId(null)}
          onCancel={() => setEditingId(null)}
        />
      ) : (
        <div className="overflow-hidden rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)]">
          <ListView
            key={activeTab}
            resource={crud!.resource}
            embedded
            onRowClick={(id) => setEditingId(id)}
            onAdd={() => setEditingId('new')}
          />
        </div>
      )}
    </div>
  )
}

// claude-opus-4-8
const TabButton = ({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) => (
  <button
    type="button"
    onClick={onClick}
    className={`inline-flex items-center gap-2 rounded-[var(--aras-radius)] px-4 py-2 text-sm font-semibold transition-colors ${
      active ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-2)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]'
    }`}
  >
    {icon}
    {label}
  </button>
)

const Loading = () => <div className="p-8 text-center text-sm text-[var(--text-3)]">Loading…</div>

export default RBACManager

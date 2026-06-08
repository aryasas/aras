import { useState } from 'react'
import { Lock, Shield, Users } from 'lucide-react'
import ListView from '../../aras-core/components/ListView'
import { DynamicForm } from '../../aras-core/components/DynamicForm'
import ErpUserAccess from '../ErpUserAccess'

type AccessTab = 'roles' | 'permissions' | 'users' | 'org-access'

const RBAC_TABS = [
  { id: 'roles' as const, label: 'Roles', icon: Shield, resource: 'auth_roles' },
  { id: 'permissions' as const, label: 'Permissions', icon: Lock, resource: 'auth_permissions' },
  { id: 'users' as const, label: 'Users', icon: Users, resource: 'auth_users' },
]

// claude-opus-4-8
export default function AccessPanel() {
  const [activeTab, setActiveTab] = useState<AccessTab>('roles')
  const [editingId, setEditingId] = useState<string | number | null>(null)

  const activeResource = RBAC_TABS.find((tab) => tab.id === activeTab)?.resource || ''

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2 rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-1">
        {RBAC_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => { setActiveTab(tab.id); setEditingId(null) }}
            className={`inline-flex items-center gap-2 rounded-[var(--aras-radius)] px-4 py-2 text-sm font-semibold transition-colors ${
              activeTab === tab.id
                ? 'bg-[var(--accent)] text-white'
                : 'text-[var(--text-2)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]'
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => { setActiveTab('org-access'); setEditingId(null) }}
          className={`inline-flex items-center gap-2 rounded-[var(--aras-radius)] px-4 py-2 text-sm font-semibold transition-colors ${
            activeTab === 'org-access'
              ? 'bg-[var(--accent)] text-white'
              : 'text-[var(--text-2)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]'
          }`}
        >
          <Users size={16} />
          Org Access
        </button>
      </div>

      {activeTab === 'org-access' ? (
        <ErpUserAccess />
      ) : editingId ? (
        <DynamicForm
          resource={activeResource}
          id={editingId}
          onSave={() => setEditingId(null)}
          onCancel={() => setEditingId(null)}
        />
      ) : (
        <div className="overflow-hidden rounded-[var(--aras-radius-lg)] border border-[var(--line)] bg-[var(--surface)]">
          <ListView
            key={activeTab}
            resource={activeResource}
            onRowClick={(id) => setEditingId(id)}
            onAdd={() => setEditingId('new')}
          />
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import ListView from '../aras-core/components/ListView'
import { DynamicForm } from '../aras-core/components/DynamicForm'
import { Users, Shield, Lock } from 'lucide-react'

const RBACManager = () => {
  const [activeTab, setActiveTab] = useState<'roles' | 'permissions' | 'users'>('roles')
  const [editingId, setEditingId] = useState<string | number | null>(null)

  const tabs = [
    { id: 'roles', label: 'Roles', icon: Shield, resource: 'auth_roles' },
    { id: 'permissions', label: 'Permissions', icon: Lock, resource: 'auth_permissions' },
    { id: 'users', label: 'Users', icon: Users, resource: 'auth_users' },
  ]

  const activeResource = tabs.find(t => t.id === activeTab)?.resource || ''

  if (editingId) {
    return (
      <DynamicForm 
        resource={activeResource} 
        id={editingId}
        onSave={() => setEditingId(null)}
        onCancel={() => setEditingId(null)}
      />
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-extrabold text-[var(--app-text)] tracking-tight">Access Control Manager</h1>
        <p className="text-[var(--app-muted)]">Manage user roles, granular data permissions, and system access.</p>
      </div>

      <div className="flex items-center gap-2 p-1 bg-[var(--app-panel-soft)] rounded-[var(--app-radius-lg)] w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-[var(--app-radius)] text-sm font-bold transition-all ${
              activeTab === tab.id 
                ? 'bg-[var(--app-panel)] text-[var(--app-accent)] shadow-sm' 
                : 'text-[var(--app-muted)] hover:text-[var(--app-text)] hover:bg-[var(--app-panel)]/50'
            }`}
          >
            <tab.icon size={18} />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] shadow-sm border border-[var(--app-border)] overflow-hidden h-[calc(100vh-280px)]">
        <ListView 
          key={activeTab}
          resource={activeResource} 
          onRowClick={(id) => setEditingId(id)}
          onAdd={() => setEditingId('new')}
        />
      </div>
    </div>
  )
}

export default RBACManager

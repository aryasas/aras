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
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Access Control Manager</h1>
        <p className="text-slate-500">Manage user roles, granular data permissions, and system access.</p>
      </div>

      <div className="flex items-center gap-2 p-1 bg-slate-100 rounded-2xl w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${
              activeTab === tab.id 
                ? 'bg-white text-indigo-600 shadow-sm' 
                : 'text-slate-500 hover:text-slate-700 hover:bg-white/50'
            }`}
          >
            <tab.icon size={18} />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden h-[calc(100vh-280px)]">
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

import { useState } from 'react'
import ListView from '../aras-core/components/ListView'
import { Users, Shield, Lock } from 'lucide-react'

const RBACManager = () => {
  const [activeTab, setActiveTab] = useState<'roles' | 'permissions' | 'users'>('roles')

  const tabs = [
    { id: 'roles', label: 'Roles', icon: Shield, resource: 'registry/auth_roles' },
    { id: 'permissions', label: 'Permissions', icon: Lock, resource: 'registry/auth_permissions' },
    { id: 'users', label: 'Users', icon: Users, resource: 'registry/auth_users' },
  ]

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
          resource={tabs.find(t => t.id === activeTab)?.resource || ''} 
          onRowClick={(id) => console.log(`${activeTab} clicked`, id)}
          onAdd={() => console.log(`Add ${activeTab}`)}
        />
      </div>
    </div>
  )
}

export default RBACManager

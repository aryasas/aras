import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import api from '../lib/api'

type AccessScope = 'ALL' | 'SPECIFIC' | 'NONE'

type UserRow = {
  id: number
  username: string
  email: string
  is_admin: boolean
  scope: AccessScope
  org_ids: number[]
  org_names: string[]
}

type OrgRow = {
  id: number
  name: string
}

const scopeLabels: Record<AccessScope, string> = {
  ALL: 'All Organizations',
  SPECIFIC: 'Specific Organizations',
  NONE: 'No Access',
}

const ErpUserAccess = () => {
  const [users, setUsers] = useState<UserRow[]>([])
  const [orgs, setOrgs] = useState<OrgRow[]>([])
  const [selectedUser, setSelectedUser] = useState<UserRow | null>(null)
  const [panelOpen, setPanelOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [scope, setScope] = useState<AccessScope>('NONE')
  const [selectedOrgIds, setSelectedOrgIds] = useState<number[]>([])

  const fetchData = async () => {
    const [usersRes, orgsRes] = await Promise.all([
      api.get('/erp/config/erp-rbac/users'),
      api.get('/erp/config/erp-rbac/orgs'),
    ])
    setUsers(usersRes.data)
    setOrgs(orgsRes.data)
  }

  useEffect(() => {
    fetchData()
  }, [])

  const openPanel = (user: UserRow) => {
    setSelectedUser(user)
    setScope(user.scope)
    setSelectedOrgIds(user.org_ids)
    setPanelOpen(true)
  }

  const closePanel = () => {
    setPanelOpen(false)
    setSelectedUser(null)
    setScope('NONE')
    setSelectedOrgIds([])
  }

  const toggleOrg = (orgId: number) => {
    setSelectedOrgIds((current) =>
      current.includes(orgId)
        ? current.filter((id) => id !== orgId)
        : [...current, orgId]
    )
  }

  const saveAccess = async () => {
    if (!selectedUser) return
    setSaving(true)
    try {
      await api.post(`/erp/config/erp-rbac/users/${selectedUser.id}`, {
        scope,
        org_ids: scope === 'SPECIFIC' ? selectedOrgIds : [],
      })
      await fetchData()
      closePanel()
    } finally {
      setSaving(false)
    }
  }

  const revokeAccess = async () => {
    if (!selectedUser) return
    setSaving(true)
    try {
      await api.delete(`/erp/config/erp-rbac/users/${selectedUser.id}`)
      await fetchData()
      closePanel()
    } finally {
      setSaving(false)
    }
  }

  const renderScopeBadge = (user: UserRow) => {
    if (user.scope === 'ALL') {
      return <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">All Orgs</span>
    }
    if (user.scope === 'SPECIFIC') {
      return <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-bold text-blue-700">{user.org_ids.length} Orgs</span>
    }
    return <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-500">No Access</span>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">ERP User Access</h1>
        <p className="text-slate-500">Manage organization access for ERP users.</p>
      </div>

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs font-bold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-6 py-4">User</th>
                <th className="px-6 py-4">Scope</th>
                <th className="px-6 py-4">Organizations</th>
                <th className="px-6 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((user) => (
                <tr key={user.id} className="transition-colors hover:bg-slate-50">
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-bold text-slate-900">{user.username}</span>
                        {user.is_admin && (
                          <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-bold text-amber-700">
                            Administrator
                          </span>
                        )}
                      </div>
                      <span className="text-sm text-slate-500">{user.email}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">{renderScopeBadge(user)}</td>
                  <td className="px-6 py-4 text-sm text-slate-600">
                    {user.org_names.length > 0 ? user.org_names.join(', ') : '—'}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {!user.is_admin && (
                      <button
                        type="button"
                        onClick={() => openPanel(user)}
                        className="rounded-xl bg-indigo-50 px-4 py-2 text-sm font-bold text-indigo-600 transition-colors hover:bg-indigo-100"
                      >
                        Edit
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-sm text-slate-400">
                    No users found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {panelOpen && selectedUser && (
        <>
          <button
            type="button"
            aria-label="Close access editor"
            className="fixed inset-0 z-40 bg-slate-900/30"
            onClick={closePanel}
          />
          <aside className="fixed right-0 top-0 z-50 flex h-screen w-96 max-w-full flex-col bg-white shadow-xl">
            <div className="flex items-start justify-between border-b border-slate-200 px-6 py-5">
              <div className="min-w-0">
                <h2 className="truncate text-xl font-extrabold text-slate-900">{selectedUser.username}</h2>
                <p className="truncate text-sm text-slate-500">{selectedUser.email}</p>
              </div>
              <button
                type="button"
                onClick={closePanel}
                className="rounded-xl p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
                aria-label="Close"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 space-y-6 overflow-y-auto px-6 py-6">
              <div className="space-y-3">
                {(['NONE', 'ALL', 'SPECIFIC'] as AccessScope[]).map((option) => (
                  <label
                    key={option}
                    className={`flex cursor-pointer items-center gap-3 rounded-2xl border px-4 py-3 transition-colors ${
                      scope === option
                        ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                        : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="erp-access-scope"
                      value={option}
                      checked={scope === option}
                      onChange={() => setScope(option)}
                      className="h-4 w-4 accent-indigo-600"
                    />
                    <span className="text-sm font-bold">{scopeLabels[option]}</span>
                  </label>
                ))}
              </div>

              {scope === 'SPECIFIC' && (
                <div className="space-y-3">
                  <h3 className="text-sm font-extrabold uppercase tracking-wider text-slate-500">Organizations</h3>
                  <div className="space-y-2">
                    {orgs.map((org) => (
                      <label
                        key={org.id}
                        className="flex cursor-pointer items-center gap-3 rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
                      >
                        <input
                          type="checkbox"
                          checked={selectedOrgIds.includes(org.id)}
                          onChange={() => toggleOrg(org.id)}
                          className="h-4 w-4 rounded accent-indigo-600"
                        />
                        <span>{org.name}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between gap-3 border-t border-slate-200 px-6 py-5">
              <button
                type="button"
                onClick={revokeAccess}
                disabled={saving}
                className="rounded-xl border border-red-200 px-4 py-2.5 text-sm font-bold text-red-600 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Revoke All
              </button>
              <button
                type="button"
                onClick={saveAccess}
                disabled={saving}
                className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-bold text-white shadow-sm transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Save
              </button>
            </div>
          </aside>
        </>
      )}
    </div>
  )
}

export default ErpUserAccess

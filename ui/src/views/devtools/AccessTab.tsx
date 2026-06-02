import React, { useEffect, useState } from 'react'
import { Shield, UserCog, Check, X } from 'lucide-react'
import api from '../../lib/api'
import { devApi } from './devApi'

// claude-opus-4-8
type Matrix = { roles: { id: number; name: string }[]; resources: { id: number; name: string; label: string }[]; grid: Record<string, { can_read: boolean; can_create: boolean; can_update: boolean; can_delete: boolean }> }
type Simulation = { allowed: boolean; reason: string; user: { username?: string; email?: string; is_admin?: boolean }; roles: { id: number; name: string }[]; matches: Record<string, unknown>[] }

// claude-opus-4-8
export default function AccessTab() {
  const [matrix, setMatrix] = useState<Matrix | null>(null)
  const [userId, setUserId] = useState('')
  const [impToken, setImpToken] = useState<{ token: string; user: { username?: string; email?: string }; expires_in: number } | null>(null)
  const [impError, setImpError] = useState('')
  const [simUserId, setSimUserId] = useState('')
  const [simResource, setSimResource] = useState('')
  const [simAction, setSimAction] = useState('READ')
  const [simulation, setSimulation] = useState<Simulation | null>(null)
  const [simError, setSimError] = useState('')

  useEffect(() => {
    api.get(devApi.permissionsMatrix).then(r => setMatrix(r.data)).catch(() => {})
  }, [])

  const impersonate = async () => {
    setImpError('')
    try {
      const r = await api.post(devApi.impersonate, { user_id: Number(userId) })
      setImpToken(r.data)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setImpError(err.response?.data?.detail || 'failed')
      setImpToken(null)
    }
  }

  const simulate = async () => {
    setSimError('')
    setSimulation(null)
    try {
      const r = await api.post(devApi.permissionsSimulate, {
        user_id: Number(simUserId),
        resource: simResource,
        action: simAction,
      })
      setSimulation(r.data)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setSimError(err.response?.data?.detail || 'simulation failed')
    }
  }

  const cell = (roleId: number, resource: string) => matrix?.grid[`${roleId}:${resource}`]

  return (
    <div className="space-y-6">
      <Section icon={<UserCog size={18} />} title="Impersonate User">
        <div className="flex gap-2 mb-3">
          <input
            value={userId}
            onChange={e => setUserId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && impersonate()}
            placeholder="user id…"
            type="number"
            className="flex-1 px-3 py-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] text-sm"
          />
          <button onClick={impersonate} className="px-4 py-2 bg-[var(--accent)] text-white rounded-[var(--radius)] font-bold text-sm hover:opacity-90">
            Generate token
          </button>
        </div>
        {impError && <div className="text-red-600 text-sm font-mono">{impError}</div>}
        {impToken && (
          <div className="text-sm space-y-1.5 bg-[var(--surface-2)] p-3 rounded-[var(--radius)] border border-[var(--line)]">
            <div className="text-[var(--text)]">Impersonating <strong>{impToken.user.username || impToken.user.email}</strong> · expires in {impToken.expires_in / 60}m</div>
            <code className="block font-mono text-xs text-[var(--text-3)] break-all">{impToken.token}</code>
          </div>
        )}
      </Section>

      <Section icon={<Shield size={18} />} title="Permissions Matrix">
        {!matrix ? <div className="text-[var(--text-3)] text-sm">Loading…</div> : (
          <div className="overflow-auto border border-[var(--line)] rounded-[var(--radius)]">
            <table className="text-sm border-collapse w-full">
              <thead className="bg-[var(--surface-2)]">
                <tr>
                  <th className="text-left px-3 py-2 font-bold text-[var(--text-2)] sticky left-0 bg-[var(--surface-2)]">Resource</th>
                  {matrix.roles.map(r => (
                    <th key={r.id} className="px-3 py-2 font-bold text-[var(--text-2)] whitespace-nowrap">{r.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {matrix.resources.map(res => (
                  <tr key={res.id} className="hover:bg-[var(--surface-2)]">
                    <td className="px-3 py-1.5 font-semibold text-[var(--text)] border-t border-[var(--line)] sticky left-0 bg-[var(--surface)]">{res.label}</td>
                    {matrix.roles.map(role => {
                      const c = cell(role.id, res.name)
                      return (
                        <td key={role.id} className="px-3 py-1.5 border-t border-[var(--line)] text-center">
                          {c ? <Crud c={c} /> : <span className="text-[var(--text-3)]">—</span>}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Section icon={<Shield size={18} />} title="Permission Simulator">
        <div className="grid grid-cols-1 md:grid-cols-[120px_1fr_140px_auto] gap-2 mb-3">
          <input className="px-3 py-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] text-sm" type="number" placeholder="user id" value={simUserId} onChange={e => setSimUserId(e.target.value)} />
          <input className="px-3 py-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] text-sm font-mono" placeholder="resource name" value={simResource} onChange={e => setSimResource(e.target.value)} />
          <select className="px-3 py-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] text-sm font-bold" value={simAction} onChange={e => setSimAction(e.target.value)}>
            {['READ', 'CREATE', 'UPDATE', 'DELETE'].map(a => <option key={a} value={a}>{a}</option>)}
          </select>
          <button onClick={simulate} className="px-4 py-2 bg-[var(--accent)] text-white rounded-[var(--radius)] font-bold text-sm hover:opacity-90">Simulate</button>
        </div>
        {simError && <div className="text-red-600 text-sm font-mono">{simError}</div>}
        {simulation && (
          <div className={`p-3 rounded-[var(--radius)] border text-sm ${simulation.allowed ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-amber-50 border-amber-200 text-amber-800'}`}>
            <div className="font-black">{simulation.allowed ? 'Allowed' : 'Denied'} · {simulation.reason}</div>
            <div className="mt-1 text-xs">
              {simulation.user.username || simulation.user.email || 'user'} · roles: {simulation.roles.map(r => r.name).join(', ') || 'none'} · matches: {simulation.matches.length}
            </div>
          </div>
        )}
      </Section>
    </div>
  )
}

// claude-opus-4-8
function Crud({ c }: { c: { can_read: boolean; can_create: boolean; can_update: boolean; can_delete: boolean } }) {
  const f = (on: boolean, label: string) => (
    <span title={label} className={`inline-flex items-center justify-center w-4 h-4 rounded text-[9px] font-bold ${on ? 'bg-emerald-100 text-emerald-700' : 'bg-[var(--surface-2)] text-[var(--text-3)]'}`}>
      {on ? <Check size={10} /> : <X size={10} />}
    </span>
  )
  return (
    <div className="flex gap-0.5 justify-center" title="read · create · update · delete">
      {f(c.can_read, 'read')}{f(c.can_create, 'create')}{f(c.can_update, 'update')}{f(c.can_delete, 'delete')}
    </div>
  )
}

const Section = ({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) => (
  <div className="bg-[var(--surface)] p-5 rounded-[var(--radius-lg)] border border-[var(--line)] shadow-sm">
    <div className="flex items-center gap-2 text-[var(--text)] mb-3">{icon}<h3 className="font-black text-sm">{title}</h3></div>
    {children}
  </div>
)

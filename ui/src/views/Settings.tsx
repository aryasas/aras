// claude-opus-4-7
// ARC settings index: dense list of configuration sections with mono IDs.
import React, { useEffect } from 'react'
import {
  Settings as SettingsIcon, Shield, Globe, Package,
  Terminal, History, Paintbrush, Server, Key,
  LayoutDashboard, ChevronRight
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'

interface SectionDef {
  id: string
  label: string
  icon: React.ReactNode
  description: string
  path: string
  external?: boolean
}

function Settings() {
  const user = useAuthStore((s) => s.user)
  const setPageTitle = useUIStore((state) => state.setPageTitle)

  useEffect(() => {
    setPageTitle('System Settings', 'Configure platform behavior and global preferences.', 'SYSTEM')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  const sections: SectionDef[] = [
    { id: 'apps',     label: 'App Manager',        icon: <Package size={18} />,         description: 'Install, update, and manage framework extensions.', path: '/apps' },
    { id: 'tenants',  label: 'Tenant Management',  icon: <Server size={18} />,          description: 'Provision and manage client databases.',           path: '/admin/tenants' },
    { id: 'license',  label: 'License',            icon: <Key size={18} />,             description: 'Instance license status and activation.',           path: '/admin/license' },
    { id: 'dashboard',label: 'Dashboard Builder',  icon: <LayoutDashboard size={18} />, description: 'Manage dashboard widgets and layout preferences.', path: '/settings/dashboard' },
    { id: 'devtools', label: 'Developer Tools',    icon: <Terminal size={18} />,        description: 'System inspection, metadata sync, and DB stats.',  path: '/dev' },
    { id: 'global',   label: 'Global Preferences', icon: <Globe size={18} />,           description: 'Date/Number formats, localization, constraints.', path: '/settings/global' },
    { id: 'security', label: 'Security & Auth',    icon: <Shield size={18} />,          description: 'Password policies, roles, and session management.',path: '/settings/rbac' },
    { id: 'audit',    label: 'Activity Audit',     icon: <History size={18} />,         description: 'System changes and user activity logs.',           path: '/settings/audit' },
    { id: 'mocks',    label: 'UI Mocks',           icon: <Paintbrush size={18} />,      description: 'Design proposals and mockups for review.',         path: '/mocks/', external: true },
  ]
  const visible = sections.filter(s => !['tenants', 'license', 'dashboard'].includes(s.id) || user?.is_admin)

  return (
    <div className="arc flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="arc-id"><b>system</b>/configuration</div>
        <div className="arc-chip">
          <SettingsIcon size={11} />
          <span className="arc-mono">aras-os/v1.2.4</span>
        </div>
      </div>

      <div className="arc-card overflow-hidden">
        {visible.map((section, idx) => {
          const body = (
            <>
              <div className="grid place-items-center w-9 h-9 rounded-[var(--radius)]"
                   style={{ background: 'color-mix(in oklch, var(--accent) 12%, var(--surface))', color: 'var(--accent)' }}>
                {section.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[13.5px] font-medium text-[var(--text)]">{section.label}</span>
                  <span className="arc-id arc-dim2">/{section.id}</span>
                </div>
                <div className="arc-dim text-[12px] mt-0.5 truncate">{section.description}</div>
              </div>
              <ChevronRight size={14} className="text-[var(--text-3)] group-hover:text-[var(--accent)] transition-colors" />
            </>
          )
          const cls = `group flex items-center gap-3 px-4 py-3 hover:bg-[var(--surface-2)] transition-colors ${idx > 0 ? 'border-t border-[var(--line)]' : ''}`
          return section.external ? (
            <a key={section.id} href={section.path} target="_blank" rel="noopener noreferrer" className={cls}>{body}</a>
          ) : (
            <Link key={section.id} to={section.path} className={cls}>{body}</Link>
          )
        })}
      </div>

      <div className="arc-card arc-dotgrid p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6"
           style={{ background: 'var(--bg-2)' }}>
        <div className="flex-1">
          <div className="arc-id"><b>raw</b>/global-config</div>
          <h2 className="text-[17px] font-semibold text-[var(--text)] mt-1 tracking-tight">Advanced system tuning</h2>
          <p className="arc-dim text-[12.5px] mt-1 leading-relaxed max-w-xl">
            Adjust low-level constants and environment flags directly in the global configuration table.
          </p>
        </div>
        <Link to="/settings/global" className="arc-btn primary">
          Open settings table <ChevronRight size={14} />
        </Link>
      </div>
    </div>
  )
}

export default Settings

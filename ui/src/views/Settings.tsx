// claude-opus-4-7
// ARC settings: hero + grouped dense row sections matching AppHome design.
import React, { useEffect } from 'react'
import {
  Settings as SettingsIcon, Shield, Globe, Package,
  Terminal, History, Server, Key,
  LayoutDashboard, ChevronRight, SlidersHorizontal,
  CreditCard, Users, Activity, UploadCloud, Database
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
  group: 'platform' | 'preferences' | 'security' | 'tools'
  external?: boolean
}

const GROUP_LABELS: Record<SectionDef['group'], string> = {
  platform: 'platform',
  preferences: 'preferences',
  security: 'security',
  tools: 'tools',
}

const getArasRole = () => {
  const injectedRole = (globalThis as any).__ARAS_ROLE__
  return String(injectedRole || import.meta.env.VITE_ARAS_ROLE || 'tenant')
}

function Settings() {
  const user = useAuthStore((s) => s.user)
  const setPageTitle = useUIStore((state) => state.setPageTitle)
  const arasRole = getArasRole()

  useEffect(() => {
    setPageTitle('System Settings', 'Configure platform behavior and global preferences.', 'SYSTEM')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  const sections: SectionDef[] = [
    { id: 'workspace',group: 'platform',    label: 'Settings', icon: <SlidersHorizontal size={14} />, description: 'Company info, feature flags, and per-app config sections.', path: '/admin/settings' },
    { id: 'master-data', group: 'platform', label: 'Master Data', icon: <Database size={14} />, description: 'Shared and module-owned reference records.', path: '/admin/master-data' },
    { id: 'apps',     group: 'platform',    label: 'App Manager',        icon: <Package size={14} />,         description: 'Install, update, and manage framework extensions.', path: '/apps' },
    { id: 'tenants',  group: 'platform',    label: 'Tenant Management',  icon: <Server size={14} />,          description: 'Provision and manage client databases.',           path: '/control-panel/tenants' },
    { id: 'cp-licenses', group: 'platform', label: 'Tenant Licenses',    icon: <Key size={14} />,             description: 'Issue, renew, and revoke tenant licenses.',         path: '/control-panel/licenses' },
    { id: 'cp-plans', group: 'platform',    label: 'SaaS Plans',         icon: <CreditCard size={14} />,      description: 'Define subscription plans and pricing tiers.',     path: '/control-panel/plans' },
    { id: 'license',  group: 'platform',    label: 'License',            icon: <Key size={14} />,             description: 'Instance license status and activation.',           path: '/admin/license' },
    { id: 'dashboard',group: 'preferences', label: 'Dashboard Builder',  icon: <LayoutDashboard size={14} />, description: 'Manage dashboard widgets and layout preferences.', path: '/settings/dashboard' },
    { id: 'global',   group: 'preferences', label: 'Global Preferences', icon: <Globe size={14} />,           description: 'Date/Number formats, localization, constraints.', path: '/settings/global' },
    { id: 'security', group: 'security',    label: 'Security & Auth',    icon: <Shield size={14} />,          description: 'Password policies, roles, and session management.',path: '/settings/rbac' },
    { id: 'erp-access', group: 'security',  label: 'ERP User Access',    icon: <Users size={14} />,           description: 'Map users to ERP roles and organization scope.',   path: '/config/user-access' },
    { id: 'audit',    group: 'security',    label: 'Activity Audit',     icon: <History size={14} />,         description: 'System changes and user activity logs.',           path: '/settings/audit' },
    { id: 'devtools', group: 'tools',       label: 'Developer Tools',    icon: <Terminal size={14} />,        description: 'System inspection, metadata sync, and DB stats.',  path: '/dev' },
    { id: 'tasks',    group: 'tools',       label: 'Background Tasks',   icon: <Activity size={14} />,        description: 'Enqueue async jobs and inspect task status.',      path: '/dev/tasks' },
    { id: 'files',    group: 'tools',       label: 'File Manager',       icon: <UploadCloud size={14} />,     description: 'Upload framework-managed files and download by name.', path: '/settings/files' },
  ]
  const visible = sections.filter((section) => {
    if (section.id === 'tenants' || section.id === 'cp-licenses' || section.id === 'cp-plans')
      return user?.is_admin && arasRole === 'control-panel'
    if (section.id === 'license') return user?.is_admin && arasRole !== 'control-panel'
    if (section.id === 'dashboard' || section.id === 'workspace' || section.id === 'erp-access') return user?.is_admin
    if (section.id === 'tasks') return user?.is_admin
    return true
  })

  const grouped = visible.reduce<Record<string, SectionDef[]>>((acc, s) => {
    (acc[s.group] ||= []).push(s)
    return acc
  }, {})

  const renderRow = (section: SectionDef) => {
    const body = (
      <>
        <span className="text-[var(--text-3)] group-hover:text-[var(--accent)] shrink-0">{section.icon}</span>
        <div className="min-w-0 flex-1">
          <div className="text-[13px] font-medium text-[var(--text)] truncate">{section.label}</div>
          <div className="arc-dim text-[11.5px] truncate">{section.description}</div>
        </div>
        <span className="arc-id arc-dim2 truncate hidden md:inline">{section.path}</span>
        <ChevronRight size={13} className="text-[var(--text-3)] group-hover:text-[var(--accent)] shrink-0" />
      </>
    )
    const cls = 'group flex items-center gap-3 px-4 py-2.5 border-t border-[var(--line)] hover:bg-[var(--surface-2)] transition-colors'
    return section.external ? (
      <a key={section.id} href={section.path} target="_blank" rel="noopener noreferrer" className={cls}>{body}</a>
    ) : (
      <Link key={section.id} to={section.path} className={cls}>{body}</Link>
    )
  }

  const groupOrder: SectionDef['group'][] = ['platform', 'preferences', 'security', 'tools']

  return (
    <div className="arc flex flex-col gap-5">
      {/* Hero */}
      <div className="arc-card arc-dotgrid p-6 flex items-center gap-5" style={{ background: 'var(--bg-2)' }}>
        <div className="grid place-items-center w-14 h-14 rounded-[var(--radius-lg)]"
             style={{ background: 'color-mix(in oklch, var(--accent) 18%, var(--surface))', color: 'var(--accent)', border: '1px solid color-mix(in oklch, var(--accent) 35%, var(--line))' }}>
          <SettingsIcon size={26} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="arc-id"><b>system</b>/configuration</div>
          <h1 className="text-[20px] font-semibold text-[var(--text)] tracking-tight mt-0.5">System Settings</h1>
          <div className="arc-dim text-[12px] mt-0.5">
            {visible.length} sections · aras-os/v1.2.4
          </div>
        </div>
      </div>

      {groupOrder.map((g) => {
        const items = grouped[g]
        if (!items?.length) return null
        return (
          <section key={g} className="arc-card overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
              <span className="arc-id"><b>{GROUP_LABELS[g]}</b></span>
              <span className="arc-id arc-dim2">{items.length}</span>
            </div>
            {items.map(renderRow)}
          </section>
        )
      })}
    </div>
  )
}

export default Settings

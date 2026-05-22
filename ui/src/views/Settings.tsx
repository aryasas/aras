import React from 'react'
import { Settings as SettingsIcon, Shield, Globe, Package, Terminal, History, Paintbrush, Server, Key, LayoutDashboard } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'
import { useEffect } from 'react'

function Settings() {
  const user = useAuthStore((s) => s.user)
  const setPageTitle = useUIStore(state => state.setPageTitle)

  useEffect(() => {
    setPageTitle('System Settings', 'Configure your platform behavior and global preferences.', 'SYSTEM')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  const sections: { id: string; label: string; icon: React.ReactNode; description: string; path: string; external?: boolean }[] = [
    { id: 'apps', label: 'App Manager', icon: <Package size={20} />, description: 'Install, update, and manage framework extensions.', path: '/apps' },
    { id: 'tenants', label: 'Tenant Management', icon: <Server size={20} />, description: 'Provision and manage client databases.', path: '/admin/tenants' },
    { id: 'license', label: 'License', icon: <Key size={20} />, description: 'Instance license status and activation.', path: '/admin/license' },
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={20} />, description: 'Manage dashboard widgets and user layout preferences.', path: '/settings/dashboard' },
    { id: 'devtools', label: 'Developer Tools', icon: <Terminal size={20} />, description: 'System inspection, metadata sync, and database stats.', path: '/dev' },
    { id: 'global', label: 'Global Preferences', icon: <Globe size={20} />, description: 'Date/Number formats, localization, and system constraints.', path: '/settings/global' },
    { id: 'security', label: 'Security & Auth', icon: <Shield size={20} />, description: 'Password policies, roles, and session management.', path: '/settings/rbac' },
    { id: 'audit', label: 'Activity Audit Trail', icon: <History size={20} />, description: 'System changes and user activity logs.', path: '/settings/audit' },
    { id: 'mocks', label: 'UI Mocks', icon: <Paintbrush size={20} />, description: 'Design proposals and UI mockups for review.', path: '/mocks/', external: true },
  ]
  const visibleSections = sections.filter(s => !['tenants', 'license', 'dashboard'].includes(s.id) || user?.is_admin)

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-end mb-8">
        <div className="flex items-center gap-2 px-4 py-2 bg-[var(--aras-panel)] border border-[var(--aras-border)] rounded-xl text-[var(--aras-muted)] text-sm font-medium shadow-sm">
          <SettingsIcon size={16} />
          <span>Version 1.0.0</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {visibleSections.map(section => {
          const cardContent = (
            <div className="flex items-start gap-4">
              <div className="p-4 bg-[var(--aras-panel-soft)] rounded-2xl transition-colors text-[var(--aras-muted)] group-hover:text-[var(--aras-accent)]">
                {section.icon}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-[var(--aras-text)] mb-1 group-hover:text-[var(--aras-accent)] transition-colors">{section.label}</h3>
                <p className="text-[var(--aras-muted)] text-sm leading-relaxed">{section.description}</p>
                <div className="mt-4 flex items-center text-[var(--aras-accent)] text-sm font-bold opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>{section.external ? 'Open Mocks' : 'Manage Settings'}</span>
                  <span className="ml-1 group-hover:translate-x-1 transition-transform">→</span>
                </div>
              </div>
            </div>
          )
          const cls = "aras-island p-5 md:p-6 transition-all group cursor-pointer hover:-translate-y-0.5 hover:border-[var(--aras-border-strong)]"
          return section.external ? (
            <a key={section.id} href={section.path} target="_blank" rel="noopener noreferrer" className={cls}>{cardContent}</a>
          ) : (
            <Link key={section.id} to={section.path} className={cls}>{cardContent}</Link>
          )
        })}
      </div>

      <div className="mt-12 aras-island bg-[var(--aras-button)] p-8 md:p-10 relative overflow-hidden text-[var(--aras-button-text)]">
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="text-center md:text-left">
            <h2 className="text-2xl font-bold text-white mb-2">Need to adjust advanced settings?</h2>
            <p className="text-white/70">Access the raw configuration table to modify system-level variables directly.</p>
          </div>
          <Link 
            to="/settings/global"
            className="px-6 py-3 bg-white text-slate-900 rounded-2xl font-black hover:bg-slate-50 transition-all shadow-xl whitespace-nowrap"
          >
            Open Settings Table
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Settings

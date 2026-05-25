import React from 'react'
import { 
  Settings as SettingsIcon, Shield, Globe, Package, 
  Terminal, History, Paintbrush, Server, Key, 
  LayoutDashboard, ChevronRight 
} from 'lucide-react'
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
    { id: 'apps', label: 'App Manager', icon: <Package size={22} strokeWidth={2.2} />, description: 'Install, update, and manage framework extensions.', path: '/apps' },
    { id: 'tenants', label: 'Tenant Management', icon: <Server size={22} strokeWidth={2.2} />, description: 'Provision and manage client databases.', path: '/admin/tenants' },
    { id: 'license', label: 'License', icon: <Key size={22} strokeWidth={2.2} />, description: 'Instance license status and activation.', path: '/admin/license' },
    { id: 'dashboard', label: 'Dashboard Builder', icon: <LayoutDashboard size={22} strokeWidth={2.2} />, description: 'Manage dashboard widgets and user layout preferences.', path: '/settings/dashboard' },
    { id: 'devtools', label: 'Developer Tools', icon: <Terminal size={22} strokeWidth={2.2} />, description: 'System inspection, metadata sync, and database stats.', path: '/dev' },
    { id: 'global', label: 'Global Preferences', icon: <Globe size={22} strokeWidth={2.2} />, description: 'Date/Number formats, localization, and system constraints.', path: '/settings/global' },
    { id: 'security', label: 'Security & Auth', icon: <Shield size={22} strokeWidth={2.2} />, description: 'Password policies, roles, and session management.', path: '/settings/rbac' },
    { id: 'audit', label: 'Activity Audit Trail', icon: <History size={22} strokeWidth={2.2} />, description: 'System changes and user activity logs.', path: '/settings/audit' },
    { id: 'mocks', label: 'UI Mocks', icon: <Paintbrush size={22} strokeWidth={2.2} />, description: 'Design proposals and UI mockups for review.', path: '/mocks/', external: true },
  ]
  const visibleSections = sections.filter(s => !['tenants', 'license', 'dashboard'].includes(s.id) || user?.is_admin)

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 flex flex-col gap-10">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-[var(--app-text)]">Configuration Sections</h2>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-[var(--app-panel-soft)] border border-[var(--app-border)] rounded-full text-[var(--app-muted)] text-[11px] font-extrabold uppercase tracking-widest shadow-sm">
          <SettingsIcon size={12} strokeWidth={3} />
          <span>Aras OS v1.2.4</span>
        </div>
      </div>

      <div className="app-app-grid">
        {visibleSections.map(section => {
          const cardContent = (
            <>
              <div className="app-app-card__icon">
                {section.icon}
              </div>
              <div className="app-app-card__content">
                <p>System Configuration</p>
                <h2>{section.label}</h2>
                <p className="mt-2 text-[var(--app-muted)] text-[13px] font-medium leading-relaxed normal-case">
                  {section.description}
                </p>
              </div>
              <div className="app-app-card__arrow">
                <ChevronRight size={18} strokeWidth={2.5} />
              </div>
            </>
          )
          const cls = "app-app-card"
          return section.external ? (
            <a key={section.id} href={section.path} target="_blank" rel="noopener noreferrer" className={cls}>{cardContent}</a>
          ) : (
            <Link key={section.id} to={section.path} className={cls}>{cardContent}</Link>
          )
        })}
      </div>

      <div className="app-island bg-gradient-to-br from-[var(--app-button)] to-slate-800 p-8 md:p-12 relative overflow-hidden text-white border-none shadow-xl rounded-[var(--app-radius-lg)]">
        {/* Abstract Background Decoration */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--app-panel)]/5 rounded-full -mr-32 -mt-32 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-[var(--app-accent)]/10 rounded-full -ml-24 -mb-24 blur-3xl pointer-events-none" />
        
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-10">
          <div className="text-center md:text-left max-w-xl">
            <h2 className="text-2xl md:text-3xl font-black text-white mb-4 tracking-tight">Advanced System Tuning</h2>
            <p className="text-white/70 text-base md:text-lg font-medium leading-relaxed">
              Need to adjust granular variables? Access the raw configuration table to modify low-level system constants and environment flags.
            </p>
          </div>
          <Link 
            to="/settings/global"
            className="flex items-center gap-3 px-8 py-4 bg-[var(--app-panel)] text-[var(--app-text)] rounded-[var(--app-radius)] font-black hover:bg-[var(--app-accent)] hover:text-white transition-all shadow-2xl group active:scale-95"
          >
            <span>Open Settings Table</span>
            <ChevronRight size={20} strokeWidth={3} className="group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Settings

import React from 'react'
import { Settings as SettingsIcon, Shield, Globe, Package, Terminal, History, Paintbrush } from 'lucide-react'
import { Link } from 'react-router-dom'

function Settings() {
  const sections: { id: string; label: string; icon: React.ReactNode; description: string; path: string; external?: boolean }[] = [
    { id: 'apps', label: 'App Manager', icon: <Package size={20} />, description: 'Install, update, and manage framework extensions.', path: '/apps' },
    { id: 'devtools', label: 'Developer Tools', icon: <Terminal size={20} />, description: 'System inspection, metadata sync, and database stats.', path: '/dev' },
    { id: 'global', label: 'Global Preferences', icon: <Globe size={20} />, description: 'Date/Number formats, localization, and system constraints.', path: '/settings/global' },
    { id: 'security', label: 'Security & Auth', icon: <Shield size={20} />, description: 'Password policies, roles, and session management.', path: '/settings/rbac' },
    { id: 'audit', label: 'Activity Audit Trail', icon: <History size={20} />, description: 'System changes and user activity logs.', path: '/settings/audit' },
    { id: 'mocks', label: 'UI Mocks', icon: <Paintbrush size={20} />, description: 'Design proposals and UI mockups for review.', path: '/mocks/', external: true },
  ]

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">System Settings</h1>
          <p className="text-slate-500 mt-1">Configure your platform behavior and global preferences.</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-slate-500 text-sm font-medium shadow-sm">
          <SettingsIcon size={16} />
          <span>Version 1.0.0</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sections.map(section => {
          const cardContent = (
            <div className="flex items-start gap-4">
              <div className="p-4 bg-slate-50 rounded-2xl group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors text-slate-400">
                {section.icon}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-900 mb-1 group-hover:text-indigo-600 transition-colors">{section.label}</h3>
                <p className="text-slate-500 text-sm leading-relaxed">{section.description}</p>
                <div className="mt-4 flex items-center text-indigo-600 text-sm font-bold opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>{section.external ? 'Open Mocks' : 'Manage Settings'}</span>
                  <span className="ml-1 group-hover:translate-x-1 transition-transform">→</span>
                </div>
              </div>
            </div>
          )
          const cls = "bg-white p-6 rounded-3xl border border-slate-200 shadow-sm hover:shadow-xl hover:shadow-slate-200/50 transition-all group cursor-pointer"
          return section.external ? (
            <a key={section.id} href={section.path} target="_blank" rel="noopener noreferrer" className={cls}>{cardContent}</a>
          ) : (
            <Link key={section.id} to={section.path} className={cls}>{cardContent}</Link>
          )
        })}
      </div>

      <div className="mt-12 bg-indigo-900 rounded-[2.5rem] p-12 relative overflow-hidden shadow-2xl shadow-indigo-200">
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="text-center md:text-left">
            <h2 className="text-2xl font-bold text-white mb-2">Need to adjust advanced settings?</h2>
            <p className="text-indigo-200">Access the raw configuration table to modify system-level variables directly.</p>
          </div>
          <Link 
            to="/settings/global"
            className="px-8 py-4 bg-white text-indigo-900 rounded-2xl font-black hover:bg-indigo-50 transition-all shadow-xl whitespace-nowrap"
          >
            Open Settings Table
          </Link>
        </div>
        
        {/* Decorative elements */}
        <div className="absolute top-0 right-0 -translate-y-1/2 translate-x-1/2 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 translate-y-1/2 -translate-x-1/2 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>
    </div>
  )
}

export default Settings

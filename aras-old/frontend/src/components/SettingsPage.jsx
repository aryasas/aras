import React, { useState, useEffect } from 'react'
import GeneralPanel from './settings/panels/GeneralPanel'
import ServerPanel from './settings/panels/ServerPanel'
import DatabasePanel from './settings/panels/DatabasePanel'
import HealthPanel from './settings/panels/HealthPanel'
import SystemPanel from './settings/panels/SystemPanel'
import UploadsPanel from './settings/panels/UploadsPanel'
import UsersPanel from './settings/panels/UsersPanel'

const PANELS = [
  { id: 'panel-general',  icon: 'fa-cog',        label: 'General', component: GeneralPanel },
  { id: 'panel-server',   icon: 'fa-server',     label: 'Server', component: ServerPanel },
  { id: 'panel-uploads',  icon: 'fa-folder-open',label: 'Uploads', component: UploadsPanel },
  { id: 'panel-users',    icon: 'fa-users',      label: 'Users', component: UsersPanel },
  { id: 'panel-database', icon: 'fa-database',   label: 'Database', component: DatabasePanel },
  { id: 'panel-health',   icon: 'fa-heartbeat',  label: 'Health', component: HealthPanel },
  { id: 'panel-system',   icon: 'fa-sliders',    label: 'System', component: SystemPanel },
]

export default function SettingsPage({ server_info, config }) {
  const [activePanel, setActivePanel] = useState('panel-general')

  useEffect(() => {
    const hash = window.location.hash.replace('#', '')
    if (hash && PANELS.find(p => p.id === hash)) {
      setActivePanel(hash)
    }
  }, [])

  const handlePanelChange = (id) => {
    setActivePanel(id)
    window.location.hash = id
  }

  const ActiveComponent = PANELS.find(p => p.id === activePanel)?.component || (() => <div>Panel not found</div>)

  return (
    <div className="min-h-screen bg-[#faf8f3] pb-32 animate-fade-in">
      <div className="max-w-6xl mx-auto px-4 sm:px-8 pt-8">
        
        {/* BREADCRUMB / NAV */}
        <div className="mb-6 flex items-center gap-2 text-[11px] font-bold text-[#9aacb8] uppercase tracking-widest">
          <a href="/admin/" className="hover:text-[#0f1b2d] transition-colors">Aras</a>
          <span>/</span>
          <span className="text-[#0f1b2d]">Settings Studio</span>
        </div>

        <div className="bg-white border border-[#dde3e7] rounded-md shadow-2xl overflow-hidden animate-slide-up flex flex-col md:flex-row">
          
          {/* SIDEBAR */}
          <aside className="w-full md:w-72 bg-[#faf8f3] border-b md:border-b-0 md:border-r border-[#dde3e7] flex-shrink-0">
            <div className="p-8 border-b border-[#dde3e7]">
              <h2 className="text-[10px] font-mono font-bold text-[#c9a568] uppercase tracking-[0.3em] mb-2">Configuration</h2>
              <h1 className="font-studio-serif text-[24px] font-bold text-[#0f1b2d] leading-none tracking-tight">System Ledger</h1>
            </div>
            
            <nav className="p-4 space-y-1">
              {PANELS.map(panel => (
                <button
                  key={panel.id}
                  onClick={() => handlePanelChange(panel.id)}
                  className={`w-full flex items-center px-4 py-3 text-[13px] font-medium transition-all duration-200 rounded-md ${
                    activePanel === panel.id
                      ? 'text-[#6b2c2c] bg-white shadow-sm border border-[#dde3e7] font-bold'
                      : 'text-[#9aacb8] hover:text-[#0f1b2d] hover:bg-white/60 border border-transparent'
                  }`}
                >
                  <i className={`fa ${panel.icon} w-6 text-center ${activePanel === panel.id ? 'text-[#c9a568]' : 'opacity-50'} mr-3`}></i>
                  <span>{panel.label}</span>
                  {activePanel === panel.id && (
                    <svg className="w-3 h-3 ml-auto text-[#c9a568]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M9 5l7 7-7 7"/></svg>
                  )}
                </button>
              ))}
            </nav>
          </aside>

          {/* MAIN CONTENT */}
          <main className="flex-1 p-8 md:p-12 min-h-[600px] bg-white relative">
            {/* TOP ACCENT */}
            <div className="absolute top-0 left-0 right-0 h-1.5 w-full bg-[#6b2c2c]"></div>
            
            <div className="max-w-3xl">
              <ActiveComponent server_info={server_info} config={config} />
            </div>
          </main>

        </div>
        
        {/* AUDIT NOTE */}
        <div className="mt-12 text-center">
          <p className="text-[11px] font-studio-serif italic text-[#9aacb8] max-w-lg mx-auto leading-relaxed">
            System configuration modifications are restricted to personnel with Level 5 administrative clearance. Proceed with caution.
          </p>
        </div>
      </div>
    </div>
  )
}


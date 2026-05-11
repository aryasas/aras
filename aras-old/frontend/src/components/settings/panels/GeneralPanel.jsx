import React from 'react'

export default function GeneralPanel({ server_info, config }) {
  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h3 className="text-3xl font-studio-serif font-bold text-aras-primary mb-2">General Settings</h3>
        <p className="text-aras-primary/50 text-sm italic">Global framework identity and environment configuration.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* App Name Card */}
        <div className="bg-white border border-aras-primary/10 p-8 shadow-sm">
          <div>
            <label className="text-[9px] font-bold text-aras-primary/30 uppercase tracking-[0.2em] mb-2 block">App Name</label>
            <div className="text-3xl font-studio-serif font-bold text-aras-primary">
              {config?.APP_NAME || 'Aras'}
            </div>
          </div>
        </div>

        {/* Environment Card */}
        <div className="bg-white border border-aras-primary/10 p-8 shadow-sm">
          <div>
            <label className="text-[9px] font-bold text-aras-primary/30 uppercase tracking-[0.2em] mb-2 block">Environment</label>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-aras-accent text-white text-[10px] font-bold uppercase tracking-widest">
                {server_info?.env || 'development'}
              </span>
            </div>
          </div>
        </div>

        {/* Framework Details */}
        <div className="md:col-span-2 bg-white border border-aras-primary/10 p-8 shadow-sm">
           <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
              <div>
                <label className="text-[9px] font-bold text-aras-primary/30 uppercase tracking-[0.2em] mb-2 block">Framework Version</label>
                <div className="text-sm font-mono text-aras-primary/80 font-bold">v1.2.0-stable</div>
              </div>
              <div>
                <label className="text-[9px] font-bold text-aras-primary/30 uppercase tracking-[0.2em] mb-2 block">Database Type</label>
                <div className="text-sm font-mono text-aras-primary/80 font-bold">MariaDB / SQLAlchemy</div>
              </div>
              <div>
                <label className="text-[9px] font-bold text-aras-primary/30 uppercase tracking-[0.2em] mb-2 block">License</label>
                <div className="text-sm text-aras-primary/80 font-bold">MIT Enterprise</div>
              </div>
           </div>
        </div>

        {/* Server Info */}
        <div className="md:col-span-2 bg-white border border-aras-primary/10 p-8 shadow-sm space-y-6">
          <h4 className="text-[10px] font-bold text-aras-primary/30 uppercase tracking-[0.2em] border-b border-aras-primary/5 pb-3">Server Information</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-16 gap-y-6">
            <InfoRow label="Python Version" value={server_info?.python_version} />
            <InfoRow label="Server Host" value={server_info?.host} />
            <InfoRow label="Server Time" value={server_info?.server_time} />
            <InfoRow label="Uptime" value={server_info?.uptime} />
          </div>
        </div>
      </div>
    </div>
  )
}

function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-aras-primary/5 last:border-0">
      <span className="text-[10px] font-bold text-aras-primary/40 uppercase tracking-wider">{label}</span>
      <span className="text-sm font-mono text-aras-primary/70">{value || '—'}</span>
    </div>
  )
}

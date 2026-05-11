import React from 'react'

/**
 * ArasAppHome - Compact "Small Card" version.
 * Optimized for high density and quick navigation.
 */
export default function ArasAppHome({ config }) {
  const { title, description, icon, tiles = [], widgets = [], isSubmodule, backUrl, viewType } = config
  const isDashboard = viewType === 'dashboard'

  return (
    <div className="space-y-6 pb-20 animate-fade-in max-w-[1600px] mx-auto">
      
      {/* COMPACT APP HEADER */}
      <div className="bg-white border border-[#dde3e7] rounded-md shadow-sm overflow-hidden">
        <div className="h-1 bg-aras-accent w-full"></div>
        <div className="px-6 py-5 flex items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <div className="w-12 h-12 bg-[#f4f2ee] flex items-center justify-center text-aras-accent rounded border border-[#dde3e7] shadow-sm">
              <i className={`fa ${icon || 'fa-cubes'} text-xl`}></i>
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-studio-serif font-bold text-aras-primary tracking-tight">
                  {title}
                </h1>
                {isSubmodule && (
                  <a 
                    href={backUrl || '/admin/'} 
                    className="px-2 py-0.5 bg-[#f4f2ee] text-[9px] font-bold text-[#9aacb8] uppercase tracking-widest rounded border border-[#dde3e7] hover:text-aras-accent transition-colors"
                  >
                    Back
                  </a>
                )}
              </div>
              <p className="text-[12px] text-[#9aacb8] font-studio-serif italic line-clamp-1 max-w-xl">
                {description || `Management tools for ${title}.`}
              </p>
            </div>
          </div>

        </div>
      </div>

      {/* WIDGETS - Compact Grid */}
      {widgets.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4">
          {widgets.map((w, i) => (
            <div key={i} className="bg-white border border-[#dde3e7] p-4 rounded-md shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden flex flex-col justify-between h-[100px]">
               <div className="flex items-start justify-between">
                  <span className="block text-[9px] font-bold text-[#9aacb8] uppercase tracking-wider truncate mr-2">{w.label}</span>
                  <i className={`fa ${w.icon || 'fa-chart-bar'} text-[10px] text-aras-accent/40 group-hover:text-aras-accent transition-colors`}></i>
               </div>
               <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-2xl font-studio-serif font-bold text-aras-primary tracking-tight">
                    {typeof w.value === 'number' ? w.value.toLocaleString() : w.value}
                  </span>
                  {w.unit && <span className="text-[9px] font-bold text-[#9aacb8] uppercase">{w.unit}</span>}
               </div>
               {w.link && (
                 <a href={w.link} className="absolute inset-0 z-10" aria-label="View Details"></a>
               )}
            </div>
          ))}
        </div>
      )}

      {/* TILES - Small Card Grid */}
      <div className="space-y-4">
        <div className="flex items-center gap-4 px-1">
           <h2 className="text-[10px] font-bold text-aras-primary uppercase tracking-[0.3em]">
              {isDashboard ? "Application Ecosystem" : "Resource Directory"}
           </h2>
           <div className="h-px flex-1 bg-[#dde3e7]"></div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {tiles.map((t, i) => (
            <a 
              key={i} 
              href={`${t.url}${t.url.includes('?') ? '&' : '?'}view_engine=react`}
              className="group bg-white border border-[#dde3e7] p-5 rounded-md shadow-sm hover:border-aras-accent hover:shadow-lg transition-all duration-300 flex flex-col"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-10 h-10 bg-[#faf8f3] border border-[#dde3e7] flex items-center justify-center text-aras-accent group-hover:bg-aras-accent group-hover:text-white transition-colors rounded">
                   <i className={`fa ${t.icon || 'fa-table'} text-lg`}></i>
                </div>
                <div className="text-right">
                    {t.count !== null && (
                      <span className="block text-lg font-studio-serif font-bold text-aras-primary leading-none mb-1">
                        {t.count}
                      </span>
                    )}
                    {t.tile_count && (
                       <span className="text-[9px] font-bold text-aras-accent uppercase tracking-tighter">{t.tile_count}</span>
                    )}
                </div>
              </div>
              
              <h3 className="text-sm font-studio-serif font-bold text-aras-primary mb-1 group-hover:text-aras-accent transition-colors truncate">
                {t.title}
              </h3>
              <p className="text-[11px] text-[#9aacb8] font-studio-serif italic mb-4 line-clamp-1">
                {t.description || `Manage ${t.title.toLowerCase()} data.`}
              </p>

              <div className="mt-auto pt-3 border-t border-[#f4f2ee] flex items-center justify-between opacity-60 group-hover:opacity-100 transition-opacity">
                <span className="text-[8px] font-bold text-[#9aacb8] uppercase tracking-widest group-hover:text-aras-primary">
                  Open
                </span>
                <i className="fa fa-chevron-right text-[8px] transform group-hover:translate-x-1 transition-transform"></i>
              </div>
            </a>
          ))}
          
          {/* COMPACT ADD TILE */}
          {!isDashboard && (
            <div className="border border-dashed border-[#dde3e7] p-5 rounded-md flex flex-col items-center justify-center text-center group hover:border-aras-accent transition-colors cursor-pointer bg-white/50">
                <div className="w-8 h-8 rounded-full bg-[#f4f2ee] flex items-center justify-center text-[#9aacb8] group-hover:text-aras-accent mb-2 transition-colors">
                    <i className="fa fa-plus text-xs"></i>
                </div>
                <h4 className="text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest">Add Page</h4>
            </div>
          )}
        </div>
      </div>

    </div>
  )
}

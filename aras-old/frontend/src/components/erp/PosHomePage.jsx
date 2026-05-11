import React from 'react'

export default function PosHomePage({ terminals = [], open_sessions = {} }) {
  return (
    <div className="space-y-12 pb-24 animate-fade-in">
      
      {/* APP HERO */}
      <div className="bg-white border border-[#dde3e7] rounded-md overflow-hidden shadow-sm">
        <div className="h-1 bg-aras-accent w-full"></div>
        <div className="p-8 md:p-12 flex flex-col md:flex-row items-center gap-8">
          <div className="w-20 h-20 bg-[#f4f2ee] flex items-center justify-center text-aras-accent rounded-md border border-[#dde3e7] shadow-inner">
            <i className="fa fa-desktop text-3xl"></i>
          </div>
          <div className="flex-1 text-center md:text-left">
            <div className="flex items-center justify-center md:justify-start gap-4 mb-2">
              <h1 className="text-3xl font-studio-serif font-bold text-aras-primary tracking-tight">
                arasPos
              </h1>
            </div>
            <p className="text-[#9aacb8] font-studio-serif italic max-w-2xl">
              Point of Sale Terminal Management. Open or resume sessions to start selling.
            </p>
          </div>
          <div className="flex gap-3">
             <a href="/admin/erp/pos/terminal/" className="px-6 py-3 bg-[#faf8f3] border border-[#dde3e7] rounded-md text-center hover:border-aras-accent transition-colors">
                <span className="block text-[10px] font-bold text-[#9aacb8] uppercase tracking-widest mb-1">Setup</span>
                <span className="text-[12px] font-bold text-aras-primary uppercase tracking-wider"><i className="fa fa-cog mr-2"></i> Terminals</span>
             </a>
          </div>
        </div>
      </div>

      {/* TERMINALS SECTION */}
      <div>
        <div className="flex items-center gap-4 mb-8">
           <h2 className="text-[14px] font-bold text-aras-primary uppercase tracking-[0.3em]">Active Terminals</h2>
           <div className="h-px flex-1 bg-[#dde3e7]"></div>
        </div>

        {terminals.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-20 border-2 border-dashed border-[#dde3e7] rounded-md bg-[#faf8f3]">
            <i className="fa fa-exclamation-triangle text-4xl text-yellow-500 mb-4"></i>
            <p className="text-[#9aacb8] font-studio-serif italic mb-6">No active terminals found.</p>
            <a href="/admin/erp/pos/terminal/add/" className="px-8 py-3 bg-aras-accent text-white font-bold rounded-md hover:bg-aras-accent/90 transition-colors">
              Add New Terminal
            </a>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {terminals.map((t) => {
              const sess = open_sessions[t.id];
              return (
                <div key={t.id} className="group bg-white border border-[#dde3e7] p-8 rounded-md shadow-sm flex flex-col relative overflow-hidden">
                  <div className={`absolute top-0 right-0 w-1.5 h-full ${sess ? 'bg-aras-accent' : 'bg-[#dde3e7]'}`}></div>
                  
                  <div className="flex items-start justify-between mb-6">
                    <div className={`w-12 h-12 flex items-center justify-center rounded-md border ${sess ? 'bg-aras-accent/5 border-aras-accent/20 text-aras-accent' : 'bg-[#faf8f3] border-[#dde3e7] text-[#9aacb8]'}`}>
                       <i className="fa fa-desktop text-xl"></i>
                    </div>
                    {sess ? (
                      <span className="px-3 py-1 bg-aras-accent/10 rounded-full text-[10px] font-bold text-aras-accent uppercase tracking-wider">
                        Active
                      </span>
                    ) : (
                      <span className="px-3 py-1 bg-[#f4f2ee] rounded-full text-[10px] font-bold text-[#9aacb8] uppercase tracking-wider">
                        Closed
                      </span>
                    )}
                  </div>
                  
                  <h3 className="text-xl font-studio-serif font-bold text-aras-primary mb-1">
                    {t.name}
                  </h3>
                  <p className="text-[12px] text-[#9aacb8] font-mono mb-6">
                    {t.code}
                  </p>
                  
                  {sess && (
                    <div className="mb-6 p-3 bg-[#faf8f3] rounded border border-[#dde3e7]">
                      <span className="block text-[9px] font-bold text-[#9aacb8] uppercase tracking-widest mb-1">Cashier</span>
                      <span className="text-[11px] font-bold text-aras-primary">{sess.cashier_name || 'N/A'}</span>
                    </div>
                  )}
                  
                  <div className="mt-auto pt-6 border-t border-[#f4f2ee] flex flex-col gap-2">
                    {sess ? (
                      <>
                        <a 
                          href={`/admin/erp/pos/session/${sess.id}`} 
                          className="w-full py-3 bg-aras-accent text-white text-[11px] font-bold uppercase tracking-[0.2em] rounded-md text-center hover:bg-aras-accent/90 transition-all flex items-center justify-center"
                        >
                          <i className="fa fa-play mr-2"></i> Resume Session
                        </a>
                        <a 
                          href={`/admin/erp/pos/session/${sess.id}/close`} 
                          className="w-full py-2 border border-red-200 text-red-500 text-[10px] font-bold uppercase tracking-widest rounded-md text-center hover:bg-red-50 transition-all"
                        >
                          <i className="fa fa-stop mr-2"></i> Close Session
                        </a>
                      </>
                    ) : (
                      <a 
                        href={`/admin/erp/pos/open/${t.id}`} 
                        className="w-full py-3 border border-aras-accent text-aras-accent text-[11px] font-bold uppercase tracking-[0.2em] rounded-md text-center hover:bg-aras-accent/5 transition-all flex items-center justify-center"
                      >
                        <i className="fa fa-plus mr-2"></i> Open New Session
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  )
}

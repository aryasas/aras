import React from 'react'

export default function ArasTableToolbar({
  title,
  searchValue,
  onSearch,
  onAdd,
  totalRecords,
  isLoading
}) {
  return (
    <div className="flex flex-col gap-8 mb-6 animate-fade-in">
      
      {/* Header Row */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="flex flex-col">
          <h1 className="text-[32px] font-studio-serif font-bold text-[#0f1b2d] tracking-tight leading-none mb-2">
            {title}
          </h1>
          <p className="text-[13px] font-studio-serif italic text-[#9aacb8]">
            Registry overview and record management for {title}.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="px-4 py-2 bg-white border border-[#dde3e7] rounded-md shadow-sm">
             <span className="text-[11px] font-bold text-[#c9a568] uppercase tracking-[0.2em]">{totalRecords} Total Records</span>
          </div>
          <button
            onClick={onAdd}
            className="px-8 py-3 bg-[#6b2c2c] text-white rounded-md text-[12px] font-bold uppercase tracking-[0.2em] hover:bg-[#4d1e1e] transition-all shadow-xl hover:-translate-y-0.5 active:scale-95 whitespace-nowrap"
          >
            Start New {title.split(' ').pop()}
          </button>
        </div>
      </div>

      {/* Filter Row */}
      <div className="flex flex-col md:flex-row items-end justify-between gap-6 bg-[#faf8f3] p-6 border border-[#dde3e7] rounded-md">
        
        {/* Left Side: Dropdowns & Search */}
        <div className="flex flex-wrap items-end gap-6 flex-1">
          
          <div className="flex flex-col gap-2">
            <label className="text-[9px] font-bold text-[#9aacb8] uppercase tracking-[0.2em]">State / Status</label>
            <div className="relative">
              <select className="appearance-none bg-white border border-[#dde3e7] rounded-md px-4 py-2.5 pr-10 text-[13px] font-bold text-[#0f1b2d] min-w-[180px] focus:outline-none focus:border-[#c9a568] transition-all cursor-pointer shadow-inner aras-engraved">
                <option>— Choose Status —</option>
                <option>Draft</option>
                <option>Active</option>
                <option>Archived</option>
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center px-3 pointer-events-none text-[#9aacb8]">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/></svg>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-2 flex-1 max-w-md">
            <label className="text-[9px] font-bold text-[#9aacb8] uppercase tracking-[0.2em]">Search Registry</label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-[#9aacb8]">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                className="block w-full pl-11 pr-4 py-2.5 border border-[#dde3e7] rounded-md bg-white text-[13px] text-[#0f1b2d] placeholder-[#9aacb8] focus:outline-none focus:border-[#c9a568] transition-all shadow-inner aras-engraved"
                placeholder="Reference number, name, or keywords..."
                value={searchValue}
                onChange={(e) => onSearch(e.target.value)}
              />
            </div>
          </div>

          {/* Toggle archived */}
          <div className="flex items-center gap-4 py-2.5">
             <div 
               className="relative inline-block w-11 h-6 transition duration-200 ease-in bg-[#eef0f2] rounded-md cursor-pointer overflow-hidden border border-[#dde3e7]"
               onClick={() => {}}
             >
                <div className="absolute top-1 left-1 w-4 h-4 bg-white rounded-md shadow-sm transition-transform duration-200"></div>
             </div>
             <span className="text-[11px] font-bold text-[#9aacb8] uppercase tracking-widest">Show Archived</span>
          </div>

        </div>

      </div>
      
    </div>
  )
}

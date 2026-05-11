export function SidebarBrand({ isOpen }: { isOpen: boolean }) {
  return (
    <div className="p-6 flex items-center gap-3">
      <div className="min-w-[32px] w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-100">
        <span className="text-white font-bold text-xl">A</span>
      </div>
      {isOpen && <span className="font-bold text-xl tracking-tight text-slate-800">ARAS</span>}
    </div>
  )
}

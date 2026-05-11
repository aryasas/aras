import { Bell } from 'lucide-react'
import { Link } from 'react-router-dom'

export function HeaderActions() {
  return (
    <div className="flex items-center gap-4">
      <button className="p-2 text-slate-500 hover:bg-slate-50 rounded-full relative transition-colors">
        <Bell size={20} />
        <span className="absolute top-2 right-2 w-2 h-2 bg-rose-500 rounded-full border-2 border-white"></span>
      </button>
      <Link to="/profile" className="h-9 w-9 bg-gradient-to-tr from-indigo-500 to-purple-600 rounded-xl border-2 border-white shadow-md cursor-pointer hover:scale-105 transition-transform block"></Link>
    </div>
  )
}

import { Moon, Sun } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useUIStore } from '../../store/uiStore'
import NotificationHistory from '../../aras-core/components/NotificationHistory'; // Import NotificationHistory

export function HeaderActions() {
  const { darkMode, toggleDarkMode } = useUIStore()

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={toggleDarkMode}
        className="p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full transition-colors"
        title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {darkMode ? <Sun size={20} /> : <Moon size={20} />}
      </button>
      <NotificationHistory /> {/* Replaced existing bell button with NotificationHistory */}
      <Link to="/profile" className="h-9 w-9 bg-gradient-to-tr from-indigo-500 to-purple-600 rounded-xl border-2 border-white shadow-md cursor-pointer hover:scale-105 transition-transform block"></Link>
    </div>
  )
}

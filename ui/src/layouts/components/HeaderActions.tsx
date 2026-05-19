import { Moon, Sun } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useUIStore } from '../../store/uiStore'
import NotificationHistory from '../../aras-core/components/NotificationHistory'; // Import NotificationHistory
import { ThemeTweakPanel } from './ThemeTweakPanel'

export function HeaderActions() {
  const { darkMode, toggleDarkMode } = useUIStore()

  return (
    <div className="flex items-center gap-3">
      <ThemeTweakPanel />
      <button
        onClick={toggleDarkMode}
        className="grid h-14 w-14 place-items-center text-[var(--aras-text)] transition-colors hover:bg-[var(--aras-panel-soft)] max-sm:h-12 max-sm:w-12"
        title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {darkMode ? <Sun size={20} /> : <Moon size={20} />}
      </button>
      <NotificationHistory /> {/* Replaced existing bell button with NotificationHistory */}
      <Link to="/profile" className="block h-7 w-7 cursor-pointer rounded-full border-2 border-white shadow-md transition-transform hover:scale-105" style={{ background: 'linear-gradient(135deg, var(--aras-accent), var(--aras-button))' }}></Link>
    </div>
  )
}

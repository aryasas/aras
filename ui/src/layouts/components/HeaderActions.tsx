import { Link } from 'react-router-dom'
import NotificationHistory from '../../aras-core/components/NotificationHistory';
import { ThemeTweakPanel } from './ThemeTweakPanel'
import { TemplateDesignToggle } from './TemplateDesignToggle'

export function HeaderActions() {
  return (
    <div className="flex items-center gap-2 md:gap-3">
      <TemplateDesignToggle />
      <ThemeTweakPanel />
      <NotificationHistory />
      <Link to="/profile" className="block h-10 w-10 md:h-12 md:w-12 cursor-pointer rounded-[var(--aras-radius)] shadow-sm border-2 border-[var(--aras-panel)] transition-transform hover:scale-105" style={{ background: 'linear-gradient(135deg, var(--aras-accent), var(--aras-button))' }}></Link>
    </div>
  )
}

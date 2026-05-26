// claude-sonnet-4-6
// ARC topbar: title+breadcrumb LEFT, centered CommandBar, Live + actions RIGHT.
import type { ReactNode } from 'react'
import { ChevronRight, Menu, Globe } from 'lucide-react'
import { CommandPaletteTrigger } from './CommandPaletteTrigger'
import { ThemeTweakPanel } from './ThemeTweakPanel'
import NotificationHistory from '../../aras-core/components/NotificationHistory'
import { Link } from 'react-router-dom'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'
import { TemplateDesignToggle } from './TemplateDesignToggle'
import { useLanguage } from '../../context/LanguageContext'

export function Header({ children }: { children?: ReactNode }) {
  const { pageTitle, breadcrumbs, setMobileSidebarOpen } = useUIStore()
  const { lang, setLang } = useLanguage()
  const user = useAuthStore((s) => s.user)
const initial = (user?.full_name || user?.username || 'A')[0].toUpperCase()

  return (
    <div
      className="z-40 flex items-center shrink-0 gap-4"
      style={{
        height: 52, minHeight: 52, padding: '0 18px',
        borderBottom: '1px solid var(--line)',
        background: 'color-mix(in oklch, var(--bg) 88%, transparent)',
        backdropFilter: 'blur(20px)',
      }}
    >
      {/* Left: hamburger (mobile) + title + breadcrumb */}
      <div className="flex items-center gap-2 min-w-0 shrink-0">
        <button
          onClick={() => setMobileSidebarOpen(true)}
          aria-label="Open menu"
          className="md:hidden inline-flex items-center justify-center text-[var(--text-2)] hover:text-[var(--text)]"
          style={{ width: 32, height: 32, borderRadius: 8, border: '1px solid var(--line)' }}
        >
          <Menu size={16} />
        </button>
        <span style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--text)', letterSpacing: '-.005em' }}>
          {pageTitle || 'Aras'}
        </span>
        {breadcrumbs && (
          <span className="flex items-center gap-1.5 truncate" style={{ fontSize: 12, color: 'var(--text-3)' }}>
            <ChevronRight size={11} />
            <span className="truncate">{breadcrumbs}</span>
          </span>
        )}
      </div>

      {/* Center: command bar */}
      <div className="flex-1 flex justify-center min-w-0">
        <div style={{ width: 520, maxWidth: '100%' }}>
          <CommandPaletteTrigger />
        </div>
      </div>

      {/* Right: live + actions */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="hidden md:inline-flex items-center gap-1.5" style={{ fontSize: 11.5, color: 'var(--text-3)' }}>
          <span style={{ width: 6, height: 6, borderRadius: 999, background: 'var(--accent)' }} />
          Live · <b className="font-semibold text-[var(--text-2)]">live</b>
        </span>

        <div id="header-actions-portal" className="flex items-center gap-1.5" />
        {children}

        <span className="hidden md:block" style={{ width: 1, height: 18, background: 'var(--line)', margin: '0 2px' }} />

        {/* Language Switcher */}
        <div className="hidden md:flex items-center gap-1 mr-1">
          <Globe size={14} className="text-[var(--text-3)] mr-0.5" />
          <button
            onClick={() => setLang('en')}
            style={{
              fontSize: 10, fontWeight: 700, padding: '2px 4px', borderRadius: 4,
              color: lang === 'en' ? 'var(--bg)' : 'var(--text-3)',
              background: lang === 'en' ? 'var(--accent)' : 'transparent',
              transition: 'all 0.2s'
            }}
          >
            EN
          </button>
          <button
            onClick={() => setLang('id')}
            style={{
              fontSize: 10, fontWeight: 700, padding: '2px 4px', borderRadius: 4,
              color: lang === 'id' ? 'var(--bg)' : 'var(--text-3)',
              background: lang === 'id' ? 'var(--accent)' : 'transparent',
              transition: 'all 0.2s'
            }}
          >
            ID
          </button>
        </div>

        <TemplateDesignToggle />
        <ThemeTweakPanel />
        <NotificationHistory />

        <Link
          to="/profile"
          aria-label="Open profile"
          className="arc-av cursor-pointer hover:border-[var(--accent)] transition-colors inline-flex items-center justify-center"
          style={{
            width: 26, height: 26, borderRadius: 999,
            border: '1px solid var(--line)',
            background: 'color-mix(in oklch, var(--accent) 14%, var(--surface))',
            color: 'var(--accent)',
          }}
        >
          <span className="arc-mono" style={{ fontSize: 10.5, fontWeight: 700 }}>{initial}</span>
        </Link>
      </div>
    </div>
  )
}

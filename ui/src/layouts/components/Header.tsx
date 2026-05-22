import type { ReactNode } from 'react'
import { PageHeader } from '../../components/PageHeader'
import { CommandPaletteTrigger } from './CommandPaletteTrigger'
import { DesignContainer } from '../../aras-core/components/design/DesignContainer'
import { DesignElement } from '../../aras-core/components/design/DesignElement'
import { ThemeTweakPanel } from './ThemeTweakPanel'
import NotificationHistory from '../../aras-core/components/NotificationHistory'
import { Link } from 'react-router-dom'
import { TemplateDesignToggle } from './TemplateDesignToggle'

export function Header({ children, moduleMenu }: { children?: ReactNode; moduleMenu?: ReactNode }) {
  return (
    <header className="sticky top-0 z-40 flex flex-col gap-2 shrink-0 bg-[var(--aras-panel)]/90 backdrop-blur-[16px] border border-[var(--aras-border)] shadow-[0_10px_32px_-16px_rgba(15,23,42,0.22)] rounded-[var(--aras-radius-lg)] px-4 py-3 md:px-5 md:py-4">
      <div className="flex items-center gap-3">
        {/* Left: title */}
        <div className="flex-1 min-w-0">
          <PageHeader />
        </div>

        {/* Right: Granular Items */}
        <div className="flex items-center gap-2 shrink-0">
          <DesignContainer id="topbar-items" className="flex items-center gap-2">
            
            <DesignElement id="page-portal">
              <div id="header-actions-portal" className="flex items-center gap-2" />
            </DesignElement>
            
            <DesignElement id="custom-content" className="hidden md:flex items-center">
              {children}
            </DesignElement>

            <DesignElement id="design-toggle">
              <TemplateDesignToggle />
            </DesignElement>
            
            <DesignElement id="search">
              <CommandPaletteTrigger />
            </DesignElement>
            
            <DesignElement id="theme-switch">
              <ThemeTweakPanel />
            </DesignElement>
            
            <DesignElement id="notifs">
              <NotificationHistory />
            </DesignElement>
            
            <DesignElement id="profile">
              <Link 
                to="/profile" 
                className="block h-10 w-10 md:h-12 md:w-12 cursor-pointer rounded-2xl shadow-sm border-2 border-white transition-transform hover:scale-105" 
                style={{ background: 'linear-gradient(135deg, var(--aras-accent), var(--aras-button))' }}
              />
            </DesignElement>

          </DesignContainer>
        </div>
      </div>

      {moduleMenu && (
        <div className="max-sm:hidden">
          {moduleMenu}
        </div>
      )}
    </header>
  )
}

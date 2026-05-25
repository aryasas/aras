import type { ReactNode } from 'react'
import { CommandPaletteTrigger } from './CommandPaletteTrigger'
import { DesignContainer } from '../../aras-core/components/design/DesignContainer'
import { DesignElement } from '../../aras-core/components/design/DesignElement'
import { ThemeTweakPanel } from './ThemeTweakPanel'
import NotificationHistory from '../../aras-core/components/NotificationHistory'
import { Link } from 'react-router-dom'
import { TemplateDesignToggle } from './TemplateDesignToggle'

export function Header({ children }: { children?: ReactNode }) {
  return (
    <div className="z-40 flex items-center shrink-0 bg-[var(--app-panel)] border-b border-[var(--app-border)] px-4 sm:px-8 lg:px-12 h-[64px] min-h-[64px] max-h-[64px] box-border">
      <div className="flex items-center gap-6 w-full">
        {/* Left: Search & Brand */}
        <div className="flex items-center gap-4">
          <CommandPaletteTrigger />
        </div>

        {/* Center/Right Spacer */}
        <div className="flex-1" />

        {/* Right: Granular Items */}
        <div className="flex items-center gap-4 shrink-0">
          <DesignContainer id="topbar-items" className="flex items-center gap-4">
            
            <DesignElement id="page-portal">
              <div id="header-actions-portal" className="flex items-center gap-2" />
            </DesignElement>
            
            <DesignElement id="custom-content" className="hidden md:flex items-center">
              {children}
            </DesignElement>

            <DesignElement id="design-toggle">
              <TemplateDesignToggle />
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
                className="block h-9 w-9 cursor-pointer rounded-full shadow-sm border border-[var(--app-border-strong)] transition-transform hover:scale-105" 
                style={{ background: 'linear-gradient(135deg, var(--app-accent), var(--app-primary-action-strong))' }}
              />
            </DesignElement>

          </DesignContainer>
        </div>
      </div>

    </div>
  )
}

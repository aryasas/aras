// claude-opus-4-7
// ARC topbar: command bar pill + slot for org context + actions on the right.
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
    <div className="z-40 flex items-center shrink-0 px-5 lg:px-7 h-[52px] min-h-[52px] max-h-[52px] box-border border-b border-[var(--line)]"
         style={{ background: 'color-mix(in oklch, var(--surface) 92%, transparent)', backdropFilter: 'blur(20px)' }}>
      <div className="flex items-center gap-5 w-full">
        <div className="flex items-center gap-3">
          <CommandPaletteTrigger />
        </div>

        <div className="flex-1" />

        <div className="flex items-center gap-3 shrink-0">
          <DesignContainer id="topbar-items" className="flex items-center gap-3">

            <DesignElement id="page-portal">
              <div id="header-actions-portal" className="flex items-center gap-2" />
            </DesignElement>

            <DesignElement id="custom-content" className="hidden md:flex items-center">
              {children}
            </DesignElement>

            <div className="hidden md:block w-px h-5 bg-[var(--line)]" />

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
                aria-label="Open profile"
                className="arc-av cursor-pointer hover:border-[var(--accent)] transition-colors"
                style={{ width: 28, height: 28, background: 'color-mix(in oklch, var(--accent) 16%, var(--surface))', color: 'var(--accent)' }}
              >
                <span className="arc-mono">A</span>
              </Link>
            </DesignElement>

          </DesignContainer>
        </div>
      </div>
    </div>
  )
}

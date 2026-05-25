import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Link, useLocation } from 'react-router-dom'
import { ChevronDown } from 'lucide-react'
import type { AppMenuData, SidebarApp, MenuElement, MenuItem } from '../types'
import { useVocabulary } from '../../context/VocabularyContext'
import { resolveIcon } from '../../lib/iconUtils'
import { filterMenuElements, filterMenuItems } from '../../lib/menuUtils'
import api from '../../lib/api'

interface Props {
  sidebarData: SidebarApp[]
}

const SKIP_APPS = new Set(['dashboard', 'settings', 'profile', 'help'])

interface DropdownPos { top: number; left: number }

export function HorizontalAppNav({ sidebarData }: Props) {
  const vocabulary = useVocabulary()
  const location = useLocation()
  const [menuData, setMenuData] = useState<AppMenuData | null>(null)
  const [openGroup, setOpenGroup] = useState<string | null>(null)
  const [isSwitcherOpen, setIsSwitcherOpen] = useState(false)
  const [dropdownPos, setDropdownPos] = useState<DropdownPos>({ top: 0, left: 0 })
  const navRef = useRef<HTMLDivElement>(null)
  const switcherRef = useRef<HTMLButtonElement>(null)
  const buttonRefs = useRef<Record<string, HTMLButtonElement | null>>({})

  const appName = useMemo(() => {
    const [first] = location.pathname.split('/').filter(Boolean)
    if (!first || SKIP_APPS.has(first)) return null
    return first
  }, [location.pathname])

  const activeApp = useMemo(() => {
    return sidebarData.find(app => (app.path || `/${app.name}`).replace(/^\//, '') === appName)
  }, [sidebarData, appName])

  useEffect(() => {
    if (!appName) { setMenuData(null); return }
    let cancelled = false
    api.get(`/app-menu/${appName}`)
      .then(res => { if (!cancelled) setMenuData(res.data) })
      .catch(() => { if (!cancelled) setMenuData(null) })
    return () => { cancelled = true }
  }, [appName])

  useEffect(() => { 
    setOpenGroup(null)
    setIsSwitcherOpen(false)
  }, [location.pathname])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        const target = e.target as Element
        if (!target.closest('[data-nav-dropdown]')) {
          setOpenGroup(null)
          setIsSwitcherOpen(false)
        }
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const groups = useMemo(() => {
    if (!menuData) return []
    return filterMenuElements(menuData.menu || []).filter(
      (e): e is MenuElement & { type: 'group' } => e.type === 'group'
    )
  }, [menuData])

  const handleGroupClick = (groupLabel: string) => {
    setIsSwitcherOpen(false)
    if (openGroup === groupLabel) {
      setOpenGroup(null)
      return
    }
    const btn = buttonRefs.current[groupLabel]
    if (btn) {
      const rect = btn.getBoundingClientRect()
      setDropdownPos({ top: rect.bottom + 8, left: rect.left })
    }
    setOpenGroup(groupLabel)
  }

  const handleSwitcherClick = () => {
    setOpenGroup(null)
    if (isSwitcherOpen) {
      setIsSwitcherOpen(false)
      return
    }
    if (switcherRef.current) {
      const rect = switcherRef.current.getBoundingClientRect()
      setDropdownPos({ top: rect.bottom + 8, left: rect.left })
    }
    setIsSwitcherOpen(true)
  }

  if (!appName) return null

  const activeGroup = groups.find(g => g.label === openGroup)
  const activeItems = activeGroup ? (filterMenuItems(activeGroup.items || []) as MenuItem[]) : []

  const GridIcon = resolveIcon('LayoutGrid')
  const AppIcon = resolveIcon(activeApp?.icon || 'Package')

  return (
    <div ref={navRef} className="flex justify-center w-full animate-in fade-in slide-in-from-top-4 duration-500">
      <div className="bg-[var(--app-panel)] border border-[var(--app-border)] rounded-[var(--app-radius-lg)] shadow-sm px-1 py-1 flex items-center gap-0.5 overflow-hidden">
        
        {/* Step 1: Global Switcher */}
        <button
          ref={switcherRef}
          onClick={handleSwitcherClick}
          className={`flex flex-col items-center justify-center w-12 h-12 rounded-[calc(var(--app-radius-lg)*0.7)] transition-all ${
            isSwitcherOpen 
              ? 'bg-[var(--app-primary-action)] text-white shadow-md' 
              : 'text-[var(--app-muted)] hover:bg-[var(--app-panel-soft)] hover:text-[var(--app-text)]'
          }`}
          title="Switch Application"
        >
          <GridIcon size={20} strokeWidth={2.5} />
        </button>

        <div className="w-px h-6 bg-[var(--app-border)] mx-1 opacity-50" />

        {/* Step 2: Active App Context */}
        <Link
          to={`/${appName}`}
          className={`flex flex-col items-center gap-0.5 px-4 py-1.5 transition-all rounded-[calc(var(--app-radius-lg)*0.7)] ${
            location.pathname === `/${appName}` || location.pathname === `/${appName}/`
              ? 'text-[var(--app-primary-action)] bg-[var(--app-primary-action)]/10'
              : 'text-[var(--app-muted)] hover:text-[var(--app-text)] hover:bg-[var(--app-panel-soft)]'
          }`}
        >
          <AppIcon size={18} strokeWidth={2.2} />
          <span className="text-[11px] font-extrabold tracking-tight truncate max-w-[100px]">
            {vocabulary.get(activeApp?.label || appName)}
          </span>
        </Link>

        {groups.length > 0 && <div className="w-px h-6 bg-[var(--app-border)] mx-1 opacity-50" />}

        {/* Step 3: Current Modules */}
        <nav className="flex items-center gap-0.5 overflow-x-auto hide-scroll" aria-label="Module navigation">
          {groups.map((group) => {
            const GroupIcon = resolveIcon(group.icon || 'Layers')
            const groupLabel = vocabulary.get(group.label)
            const isOpen = openGroup === group.label
            const items = filterMenuItems(group.items || []) as MenuItem[]
            const isGroupActive = items.some(
              item => location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)
            )

            return (
              <div key={group.label} className="relative">
                <button
                  ref={el => { buttonRefs.current[group.label] = el }}
                  type="button"
                  onClick={() => handleGroupClick(group.label)}
                  className={`flex flex-col shrink-0 items-center gap-0.5 px-4 py-1.5 text-[11px] font-bold tracking-tight transition-all rounded-[calc(var(--app-radius-lg)*0.7)] ${
                    isGroupActive || isOpen
                      ? 'text-[var(--app-primary-action)] bg-[var(--app-primary-action)]/10'
                      : 'text-[var(--app-muted)] hover:text-[var(--app-text)] hover:bg-[var(--app-panel-soft)]'
                  }`}
                >
                  <GroupIcon size={18} strokeWidth={2.2} className="shrink-0" />
                  <div className="flex items-center gap-1">
                    <span className="truncate max-w-[90px]">{groupLabel}</span>
                    <ChevronDown
                      size={10}
                      strokeWidth={2.5}
                      className={`shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                    />
                  </div>
                </button>
              </div>
            )
          })}
        </nav>
      </div>

      {/* Switcher Portal */}
      {isSwitcherOpen && createPortal(
        <div
          data-nav-dropdown
          style={{ position: 'fixed', top: dropdownPos.top, left: dropdownPos.left, zIndex: 9999 }}
          className="w-[420px] rounded-[var(--app-radius-lg)] border border-[var(--app-border)] bg-[var(--app-panel)] p-4 shadow-[var(--shadow-premium)] animate-in fade-in zoom-in-95 duration-100"
        >
          <div className="text-[10px] font-black uppercase tracking-widest text-[var(--app-muted)] mb-3 px-2">Switch Application</div>
          <div className="grid grid-cols-2 gap-2">
            {sidebarData.map(app => {
              const Icon = resolveIcon(app.icon || 'Package')
              const path = app.path || `/${app.name}`
              const isActive = location.pathname.startsWith(path)
              return (
                <Link
                  key={app.name}
                  to={path}
                  className={`flex items-center gap-3 p-3 rounded-[var(--app-radius)] transition-all ${
                    isActive 
                      ? 'bg-[var(--app-primary-action)]/10 text-[var(--app-primary-action)]' 
                      : 'hover:bg-[var(--app-panel-soft)] text-[var(--app-muted)] hover:text-[var(--app-text)]'
                  }`}
                >
                  <div className={`p-2 rounded-lg ${isActive ? 'bg-[var(--app-primary-action)] text-white' : 'bg-[var(--app-panel-soft)] text-[var(--app-muted)]'}`}>
                    <Icon size={20} strokeWidth={2.2} />
                  </div>
                  <div className="min-w-0">
                    <div className="text-[13px] font-bold truncate">{vocabulary.get(app.label || app.name)}</div>
                    <div className="text-[10px] opacity-60 truncate">Open Workspace</div>
                  </div>
                </Link>
              )
            })}
          </div>
        </div>,
        document.body
      )}

      {/* Group Items Portal */}
      {openGroup && activeItems.length > 0 && createPortal(
        <div
          data-nav-dropdown
          style={{ position: 'fixed', top: dropdownPos.top, left: dropdownPos.left, zIndex: 9999 }}
          className="min-w-[200px] rounded-[var(--app-radius)] border border-[var(--app-border)] bg-[var(--app-panel)] p-2 shadow-[var(--shadow-premium)] animate-in fade-in zoom-in-95 duration-100"
        >
          {activeItems.map((item) => {
            const ItemIcon = resolveIcon(item.icon || 'FileText')
            const isActive = location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)
            return (
              <Link
                key={item.name}
                to={item.path}
                onClick={() => setOpenGroup(null)}
                className={`flex items-center gap-3 rounded-[var(--app-radius)] px-3 py-2 text-[13px] font-bold transition-all ${
                  isActive
                    ? 'text-[var(--app-primary-action)] bg-[var(--app-primary-action)]/10'
                    : 'text-[var(--app-muted)] hover:bg-[var(--app-panel-soft)] hover:text-[var(--app-text)]'
                }`}
              >
                <ItemIcon size={16} strokeWidth={2.5} className="shrink-0" />
                {vocabulary.get(item.label || item.name)}
              </Link>
            )
          })}
        </div>,
        document.body
      )}
    </div>
  )
}

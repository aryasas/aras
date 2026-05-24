import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Link, useLocation } from 'react-router-dom'
import { ChevronDown } from 'lucide-react'
import type { AppMenuData, SidebarApp, MenuElement, MenuItem } from '../types'
import { useVocabulary } from '../../context/VocabularyContext'
import { resolveIcon } from '../../lib/iconUtils'
import { useUIStore } from '../../store/uiStore'
import { filterMenuElements, filterMenuItems } from '../../lib/menuUtils'
import api from '../../lib/api'

interface Props {
  sidebarData: SidebarApp[]
}

const SKIP_APPS = new Set(['dashboard', 'settings', 'profile', 'help'])

interface DropdownPos { top: number; left: number }

export function HorizontalAppNav({ sidebarData: _unused }: Props) {
  const vocabulary = useVocabulary()
  const location = useLocation()
  const topbarNavStyle = useUIStore(state => state.topbarNavStyle)
  const iconOnly = topbarNavStyle === 'icon-only'
  const [menuData, setMenuData] = useState<AppMenuData | null>(null)
  const [openGroup, setOpenGroup] = useState<string | null>(null)
  const [dropdownPos, setDropdownPos] = useState<DropdownPos>({ top: 0, left: 0 })
  const navRef = useRef<HTMLDivElement>(null)
  const buttonRefs = useRef<Record<string, HTMLButtonElement | null>>({})

  const appName = useMemo(() => {
    const [first] = location.pathname.split('/').filter(Boolean)
    if (!first || SKIP_APPS.has(first)) return null
    return first
  }, [location.pathname])

  useEffect(() => {
    if (!appName) { setMenuData(null); return }
    let cancelled = false
    api.get(`/app-menu/${appName}`)
      .then(res => { if (!cancelled) setMenuData(res.data) })
      .catch(() => { if (!cancelled) setMenuData(null) })
    return () => { cancelled = true }
  }, [appName])

  useEffect(() => { setOpenGroup(null) }, [location.pathname])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        const target = e.target as Element
        if (!target.closest('[data-nav-dropdown]')) setOpenGroup(null)
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

  if (!appName || !menuData || groups.length === 0) return null

  const activeGroup = groups.find(g => g.label === openGroup)
  const activeItems = activeGroup ? (filterMenuItems(activeGroup.items || []) as MenuItem[]) : []

  return (
    <div ref={navRef}>
      <nav
        className="shrink-0 flex items-center gap-1 px-2 py-2 bg-[var(--aras-panel)] border border-[var(--aras-border)] shadow-[0_4px_16px_-8px_rgba(15,23,42,0.12)] rounded-[var(--aras-radius-lg)] overflow-x-auto hide-scroll"
        aria-label="Module navigation"
      >
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
                className={`flex shrink-0 items-center gap-2 rounded-[var(--aras-radius)] px-3 py-2 text-[12px] font-bold transition-all ${
                  isGroupActive || isOpen
                    ? 'bg-[var(--aras-accent)] text-white shadow-sm'
                    : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)] hover:text-[var(--aras-text)]'
                }`}
              >
                <GroupIcon size={15} strokeWidth={2.2} className="shrink-0" />
                {!iconOnly && <span className="truncate max-w-[96px]">{groupLabel}</span>}
                <ChevronDown
                  size={13}
                  strokeWidth={2.5}
                  className={`shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                />
              </button>
            </div>
          )
        })}
      </nav>

      {openGroup && activeItems.length > 0 && createPortal(
        <div
          data-nav-dropdown
          style={{ position: 'fixed', top: dropdownPos.top, left: dropdownPos.left, zIndex: 9999 }}
          className="min-w-[200px] rounded-[var(--aras-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel)] p-1.5 shadow-[0_18px_45px_-18px_rgba(15,23,42,0.35)] animate-in fade-in zoom-in-95 duration-100"
        >
          {activeItems.map((item) => {
            const ItemIcon = resolveIcon(item.icon || 'FileText')
            const isActive = location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)
            return (
              <Link
                key={item.name}
                to={item.path}
                onClick={() => setOpenGroup(null)}
                className={`flex items-center gap-3 rounded-[calc(var(--aras-radius)*0.75)] px-3 py-2 text-[13px] font-semibold transition-all ${
                  isActive
                    ? 'text-[var(--aras-accent)] bg-[color-mix(in_srgb,var(--aras-accent)_8%,transparent)]'
                    : 'text-[var(--aras-muted)] hover:bg-[var(--aras-panel-soft)] hover:text-[var(--aras-text)]'
                }`}
              >
                <ItemIcon size={15} strokeWidth={2.2} className="shrink-0" />
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

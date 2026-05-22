import { createContext, useContext } from 'react'

export type Breakpoint = 'desktop' | 'tablet' | 'mobile'

export const BREAKPOINT_WIDTHS = {
  desktop: 1440,
  tablet: 834,
  mobile: 390,
} as const

export const BREAKPOINT_ORDER: Breakpoint[] = ['desktop', 'tablet', 'mobile']

export const BREAKPOINT_LABELS: Record<Breakpoint, string> = {
  desktop: 'Desktop',
  tablet: 'Tablet',
  mobile: 'Mobile',
}

export type SpacingSide = 'top' | 'right' | 'bottom' | 'left'
export type FlexDirection = 'row' | 'col'
export type FlexAlign = 'start' | 'center' | 'end' | 'stretch'
export type FlexJustify = 'start' | 'center' | 'end' | 'between'

export interface BoxSpacing {
  top: number
  right: number
  bottom: number
  left: number
}

export interface BoxSettings {
  margin: BoxSpacing
  padding: BoxSpacing
  width: number | null
  height: number | null
  gap: number
  bg: string
  radius: number
  direction: FlexDirection
  align: FlexAlign
  justify: FlexJustify
}

export type ResponsiveBoxSettings = Record<Breakpoint, BoxSettings>
export type ResponsiveColumns = Record<Breakpoint, 1 | 2 | 3>

export interface BreakpointContextValue {
  activeBreakpoint: Breakpoint
  setActiveBreakpoint: (breakpoint: Breakpoint) => void
}

export const BreakpointContext = createContext<BreakpointContextValue>({
  activeBreakpoint: 'desktop',
  setActiveBreakpoint: () => undefined,
})

export function useBreakpoint() {
  return useContext(BreakpointContext)
}

export function createSpacing(value = 0): BoxSpacing {
  return { top: value, right: value, bottom: value, left: value }
}

const DEFAULT_SETTINGS: BoxSettings = {
  margin: createSpacing(0),
  padding: createSpacing(0),
  width: null,
  height: null,
  gap: 16,
  bg: 'transparent',
  radius: 0,
  direction: 'col',
  align: 'stretch',
  justify: 'start',
}

function mergeSpacing(
  base: BoxSpacing,
  next?: Partial<BoxSpacing>,
): BoxSpacing {
  return {
    top: next?.top ?? base.top,
    right: next?.right ?? base.right,
    bottom: next?.bottom ?? base.bottom,
    left: next?.left ?? base.left,
  }
}

function mergeSettings(base: BoxSettings, next?: Partial<BoxSettings>): BoxSettings {
  if (!next) return structuredClone(base)
  return {
    ...base,
    ...next,
    margin: mergeSpacing(base.margin, next.margin),
    padding: mergeSpacing(base.padding, next.padding),
  }
}

export function createResponsiveBoxSettings(
  overrides?: Partial<Record<Breakpoint, Partial<BoxSettings>>>,
): ResponsiveBoxSettings {
  return {
    desktop: mergeSettings(DEFAULT_SETTINGS, overrides?.desktop),
    tablet: mergeSettings(DEFAULT_SETTINGS, overrides?.tablet),
    mobile: mergeSettings(DEFAULT_SETTINGS, overrides?.mobile),
  }
}

export function createResponsiveColumns(
  desktop: 1 | 2 | 3,
  tablet: 1 | 2 | 3,
  mobile: 1 | 2 | 3,
): ResponsiveColumns {
  return { desktop, tablet, mobile }
}

export function cloneResponsiveSettings(settings: ResponsiveBoxSettings) {
  return structuredClone(settings)
}

export function cloneResponsiveColumns(columns: ResponsiveColumns) {
  return structuredClone(columns)
}

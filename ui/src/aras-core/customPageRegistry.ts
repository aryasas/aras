import { lazy, type ComponentType, type LazyExoticComponent } from 'react'

const registry: Record<string, LazyExoticComponent<ComponentType<any>>> = {}

export function registerCustomPage(
  key: string,
  loader: () => Promise<{ default: ComponentType<any> }>,
) {
  registry[key] = lazy(loader)
}

export function getCustomPage(key: string) {
  return registry[key] ?? null
}

export function hasCustomPage(key: string) {
  return key in registry
}

import * as LucideIcons from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export function resolveIcon(name?: string | null): LucideIcon {
  return ((name ? (LucideIcons as any)[name] : null) || LucideIcons.Package) as LucideIcon
}

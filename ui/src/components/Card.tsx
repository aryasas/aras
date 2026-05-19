import type { HTMLAttributes } from 'react'

export function Card({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`bg-[var(--aras-panel)] rounded-[var(--aras-radius)] border border-[var(--aras-border)] shadow-sm ${className}`} {...props} />
}

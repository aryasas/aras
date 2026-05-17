import type { HTMLAttributes } from 'react'

export function PageShell({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`animate-in fade-in slide-in-from-bottom-4 duration-500 ${className}`} {...props} />
}

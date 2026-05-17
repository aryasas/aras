import { Loader2 } from 'lucide-react'

interface LoadingStateProps {
  label?: string
  className?: string
}

export function LoadingState({ label = 'Loading...', className = '' }: LoadingStateProps) {
  return (
    <div className={`flex items-center justify-center gap-2 p-8 text-sm text-slate-400 ${className}`}>
      <Loader2 size={18} className="animate-spin" />
      <span>{label}</span>
    </div>
  )
}

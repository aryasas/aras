import { Wand2 } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'

export function TemplateDesignToggle() {
  const location = useLocation()
  const navigate = useNavigate()

  const handleClick = () => {
    navigate(`/dev/template-builder?from=${encodeURIComponent(location.pathname)}`)
  }

  return (
    <button
      onClick={handleClick}
      className="flex items-center justify-center w-10 h-10 rounded-[var(--aras-radius)] border transition-all bg-[var(--aras-panel)] border-[var(--aras-border)] text-[var(--aras-muted)] hover:text-[var(--aras-accent)] hover:border-[var(--aras-accent)] shadow-sm"
      title="Open Template Studio for this page"
    >
      <Wand2 size={18} />
    </button>
  )
}

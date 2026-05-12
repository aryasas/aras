import { Link, useLocation } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'

export function Breadcrumbs() {
  const location = useLocation()
  const pathnames = location.pathname.split('/').filter((x) => x)

  return (
    <nav className="h-10 bg-white border-b border-slate-200 flex items-center px-8 z-0">
      <div className="flex items-center space-x-2 text-xs font-medium">
        <Link 
          to="/" 
          className="flex items-center text-slate-500 hover:text-indigo-600 transition-colors"
        >
          <Home className="w-3.5 h-3.5" />
        </Link>

        {pathnames.length > 0 && (
          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
        )}

        {pathnames.map((name, index) => {
          const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`
          const isLast = index === pathnames.length - 1

          // Capitalize and format name
          const displayName = name
            .replace(/-/g, ' ')
            .replace(/_/g, ' ')
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ')

          return (
            <div key={name} className="flex items-center space-x-2">
              {isLast ? (
                <span className="text-slate-900 font-semibold truncate max-w-[200px]">
                  {displayName}
                </span>
              ) : (
                <>
                  <Link
                    to={routeTo}
                    className="text-slate-500 hover:text-indigo-600 transition-colors"
                  >
                    {displayName}
                  </Link>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                </>
              )}
            </div>
          )
        })}
      </div>
    </nav>
  )
}

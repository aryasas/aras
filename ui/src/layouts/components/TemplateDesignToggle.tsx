import { Wand2 } from 'lucide-react'
import { useUIStore } from '../../store/uiStore'
import { useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import api from '../../lib/api'

export function TemplateDesignToggle() {
  const { toggleDesignMode, designMode, setDesignData } = useUIStore()
  const location = useLocation()

  // Pre-load saved design data for this route when design mode is toggled on
  useEffect(() => {
    if (designMode) {
      const templateName = location.pathname
      api.get(`/dev/dev_template_annotations?template_name=${templateName}`)
        .then(res => {
          if (res.data.items?.length > 0) {
            const dataSec = res.data.items[0].sections.find((s: any) => s.id === '__designData__')
            if (dataSec && dataSec.data) {
              setDesignData(dataSec.data)
            }
          }
        })
        .catch(console.error)
    }
  }, [designMode, location.pathname, setDesignData])

  return (
    <button
      onClick={toggleDesignMode}
      className={`p-2 rounded-xl transition-all border ${
        designMode
          ? 'bg-pink-100 border-pink-200 text-pink-600'
          : 'bg-white border-slate-200 text-slate-400 hover:text-pink-500 hover:border-pink-200 shadow-sm'
      }`}
      title={designMode ? "Exit WYSIWYG Design Mode" : "Enter WYSIWYG Design Mode"}
    >
      <Wand2 size={18} />
    </button>
  )
}

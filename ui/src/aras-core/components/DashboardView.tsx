import React, { useState, useEffect } from 'react'
import * as LucideIcons from 'lucide-react'
import api from '../../lib/api'
import { useAras } from '../hooks/useAras'

interface Widget {
  id: number
  name: string
  title: string
  widget_type: 'stat' | 'chart' | 'list'
  resource_name: string
  config_json: any
  size: string
}

export const DashboardView: React.FC = () => {
  const [widgets, setWidgets] = useState<Widget[]>([])
  const [loading, setLoading] = useState(true)
  const { notify } = useAras()

  useEffect(() => {
    loadWidgets()
  }, [])

  const loadWidgets = async () => {
    try {
      const res = await api.get('/dashboard/widgets')
      setWidgets(res.data.layout_config?.widgets || [])
    } catch (err) {
      notify('Failed to load dashboard widgets', 'error')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="p-12 text-center text-slate-400 animate-pulse">Loading dashboard...</div>
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      {widgets.map((widget) => (
        <div key={widget.id} className={`${widget.size}`}>
          {widget.widget_type === 'stat' && <StatWidget widget={widget} />}
          {widget.widget_type === 'list' && <ListWidget widget={widget} />}
        </div>
      ))}
    </div>
  )
}

const StatWidget: React.FC<{ widget: Widget }> = ({ widget }) => {
  const [value, setValue] = useState<string | number>('...')
  const config = widget.config_json || {}
  const Icon = (LucideIcons as any)[config.icon || 'Activity']

  useEffect(() => {
    api.get(`/${widget.resource_name}`).then((res: any) => {
      setValue(res.data.total || res.data.length || 0)
    })
  }, [widget.resource_name])

  return (
    <div className="bg-white p-7 rounded-3xl border border-slate-200 shadow-sm hover:shadow-xl hover:shadow-slate-200/50 transition-all group h-full">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-2xl transition-colors ${
          config.color === 'indigo' ? 'bg-indigo-50 text-indigo-600' :
          config.color === 'emerald' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-50 text-slate-400'
        }`}>
          <Icon size={20} />
        </div>
      </div>
      <p className="text-slate-500 text-sm font-medium mb-1 uppercase tracking-wide">{widget.title}</p>
      <h3 className="text-3xl font-black text-slate-900 tracking-tight">{value}</h3>
    </div>
  )
}

const ListWidget: React.FC<{ widget: Widget }> = ({ widget }) => {
  const [items, setItems] = useState<any[]>([])
  const config = widget.config_json || {}

  useEffect(() => {
    api.get(`/${widget.resource_name}?per_page=${config.limit || 5}`).then((res: any) => {
      setItems(res.data.items || res.data)
    })
  }, [widget.resource_name])

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden h-full flex flex-col">
      <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/20">
        <h2 className="font-bold text-lg text-slate-900">{widget.title}</h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        {items.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">No recent activity</div>
        ) : (
          <div className="divide-y divide-slate-50">
            {items.map((item, idx) => (
              <div key={idx} className="p-4 hover:bg-slate-50 transition-colors flex items-center gap-4">
                <div className="w-2 h-2 rounded-full bg-indigo-400" />
                <div className="flex-1 text-sm text-slate-600 truncate font-medium">
                  {item.description || item.name || item.id}
                </div>
                <div className="text-[10px] text-slate-400 font-bold uppercase">
                  {item.created_at ? new Date(item.created_at).toLocaleTimeString() : ''}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

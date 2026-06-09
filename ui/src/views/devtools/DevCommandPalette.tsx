import { useMemo, useState } from 'react'
import { Command, Search } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '../../lib/api'
import { openApiDocs } from '../../lib/apiDocs'
import { MetadataService } from '../../aras-core/services/MetadataService'
import { devApi } from './devApi'

type CommandItem = { label: string; detail: string; run: () => void | Promise<void> }

export default function DevCommandPalette() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [message, setMessage] = useState('')

  const commands: CommandItem[] = useMemo(() => [
    { label: 'Open route debugger', detail: 'DevTools / Routes', run: () => navigate('/admin/dev/routes-debug') },
    { label: 'Open activity heatmap', detail: '/dev/activity-heatmap', run: () => navigate('/dev/activity-heatmap') },
    { label: 'Open background tasks', detail: '/dev/tasks', run: () => navigate('/dev/tasks') },
    { label: 'Open dev help', detail: '/dev/help', run: () => navigate('/dev/help') },
    { label: 'Flush metadata cache', detail: `POST ${devApi.metadataFlush}`, run: async () => { await api.post(devApi.metadataFlush, {}); MetadataService.clearCache(); setMessage('Metadata cache flushed') } },
    { label: 'Force metadata sync', detail: `POST ${devApi.sync}`, run: async () => { await api.post(devApi.sync); MetadataService.clearCache(); setMessage('Metadata sync complete') } },
    { label: 'Open Swagger UI', detail: '/docs', run: openApiDocs },
  ], [navigate])

  const filtered = commands.filter(c => `${c.label} ${c.detail}`.toLowerCase().includes(query.toLowerCase()))

  const execute = async (cmd: CommandItem) => {
    setMessage('')
    try {
      await cmd.run()
    } catch (e: any) {
      setMessage(e?.response?.data?.detail || e.message || 'Command failed')
    }
  }

  return (
    <section className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius-lg)] overflow-hidden">
      <div className="p-4 border-b border-[var(--line)] bg-[var(--surface-2)]">
        <div className="flex items-center gap-2 font-black text-[var(--text)]"><Command size={17} /> Dev Command Palette</div>
        <div className="relative mt-3">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
          <input className="arc-input pl-9" autoFocus placeholder="Search dev commands" value={query} onChange={e => setQuery(e.target.value)} />
        </div>
      </div>
      <div className="divide-y divide-[var(--line)]">
        {filtered.map(cmd => (
          <button key={cmd.label} onClick={() => execute(cmd)} className="w-full px-4 py-3 text-left hover:bg-[var(--surface-2)]">
            <div className="font-bold text-sm text-[var(--text)]">{cmd.label}</div>
            <div className="font-mono text-[11px] text-[var(--text-3)]">{cmd.detail}</div>
          </button>
        ))}
      </div>
      {message && <div className="px-4 py-3 border-t border-[var(--line)] text-sm font-semibold text-[var(--text-2)]">{message}</div>}
    </section>
  )
}

import { useState } from 'react'
import { RefreshCw, Trash2 } from 'lucide-react'
import api from '../../lib/api'
import { MetadataService } from '../../aras-core/services/MetadataService'
import { devApi } from './devApi'

export default function CacheControl() {
  const [resource, setResource] = useState('')
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)

  const flush = async () => {
    setBusy(true)
    setStatus('')
    try {
      await api.post(devApi.metadataFlush, { resource: resource.trim() || null })
      MetadataService.clearCache()
      setStatus(resource.trim() ? `Flushed metadata cache for ${resource.trim()}` : 'Flushed all metadata caches')
    } catch (e: any) {
      setStatus(e?.response?.data?.detail || 'Flush failed')
    } finally {
      setBusy(false)
    }
  }

  const sync = async () => {
    setBusy(true)
    setStatus('')
    try {
      await api.post(devApi.sync)
      MetadataService.clearCache()
      setStatus(`Metadata sync completed at ${new Date().toLocaleTimeString()}`)
    } catch (e: any) {
      setStatus(e?.response?.data?.detail || 'Sync failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-5">
      <section className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius-lg)] p-5">
        <h2 className="text-lg font-black text-[var(--text)] mb-1">Cache and Metadata Control</h2>
        <p className="text-sm text-[var(--text-3)] mb-5">Flush generated UI metadata, clear the frontend metadata cache, and run registry sync.</p>
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-3">
          <input className="arc-input" placeholder="Optional resource name" value={resource} onChange={e => setResource(e.target.value)} />
          <button className="arc-btn" onClick={flush} disabled={busy}><Trash2 size={14} /> Flush cache</button>
          <button className="arc-btn primary" onClick={sync} disabled={busy}><RefreshCw size={14} className={busy ? 'animate-spin' : ''} /> Sync metadata</button>
        </div>
        {status && <div className="mt-4 text-sm font-semibold text-[var(--text-2)]">{status}</div>}
      </section>
      <section className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Info label="Backend cache" value="UIGenerator.flush_cache" />
        <Info label="Frontend cache" value="MetadataService.clearCache" />
        <Info label="Registry sync" value="POST /dev/sync" />
      </section>
    </div>
  )
}

function Info({ label, value }: { label: string; value: string }) {
  return <div className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius)] p-4"><div className="text-[10px] uppercase font-black text-[var(--text-3)]">{label}</div><code className="block mt-1 text-xs text-[var(--accent)]">{value}</code></div>
}

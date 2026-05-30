// claude-opus-4-7
// ARC file manager: upload via /files/upload, download via /files/download/:filename.
// No list endpoint exists — recent uploads are remembered locally.
import { useEffect, useRef, useState } from 'react'
import { UploadCloud, FileText, Download, Search, Trash2 } from 'lucide-react'
import api from '../lib/api'
import { useUIStore } from '../store/uiStore'
import { EmptyState } from '../components/EmptyState'

interface UploadedFile {
  filename: string
  url?: string
  size?: number
  uploadedAt: number
}

const STORE_KEY = 'aras.files.recent'

function loadRecent(): UploadedFile[] {
  try { return JSON.parse(localStorage.getItem(STORE_KEY) || '[]') } catch { return [] }
}
function saveRecent(items: UploadedFile[]) {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(items.slice(0, 100))) } catch { /* ignore */ }
}

const fmtSize = (n?: number) => {
  if (n == null) return '—'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

export default function FileManager() {
  const setPageTitle = useUIStore((s) => s.setPageTitle)
  const [recent, setRecent] = useState<UploadedFile[]>(() => loadRecent())
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)
  const [lookup, setLookup] = useState('')
  const fileRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    setPageTitle('File Manager', 'Upload and retrieve framework-managed files.', 'SYSTEM')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  useEffect(() => { saveRecent(recent) }, [recent])

  const upload = async (file: File) => {
    setBusy(true)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await api.post('/files/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      const data = res.data || {}
      const filename: string = data.filename || data.name || file.name
      const entry: UploadedFile = {
        filename,
        url: data.url,
        size: data.size ?? file.size,
        uploadedAt: Date.now(),
      }
      setRecent((prev) => [entry, ...prev.filter((f) => f.filename !== filename)])
      setMessage({ kind: 'ok', text: `Uploaded ${filename}` })
    } catch (e: any) {
      setMessage({ kind: 'err', text: e?.response?.data?.detail || e.message || 'Upload failed' })
    } finally {
      setBusy(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const onPickFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) upload(f)
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const f = e.dataTransfer.files?.[0]
    if (f) upload(f)
  }

  const downloadByName = (name: string) => {
    const safe = name.trim()
    if (!safe) return
    const a = document.createElement('a')
    a.href = `/api/v1/files/download/${encodeURIComponent(safe)}`
    a.download = safe
    document.body.appendChild(a)
    a.click()
    a.remove()
  }

  const removeRecent = (name: string) => {
    setRecent((prev) => prev.filter((f) => f.filename !== name))
  }

  return (
    <div className="arc flex flex-col gap-5">
      <div className="arc-card arc-dotgrid p-6 flex items-center gap-5" style={{ background: 'var(--bg-2)' }}>
        <div className="grid place-items-center w-14 h-14 rounded-[var(--radius-lg)]"
             style={{ background: 'color-mix(in oklch, var(--accent) 18%, var(--surface))', color: 'var(--accent)', border: '1px solid color-mix(in oklch, var(--accent) 35%, var(--line))' }}>
          <UploadCloud size={26} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="arc-id"><b>system</b>/files</div>
          <h1 className="text-[20px] font-semibold text-[var(--text)] tracking-tight mt-0.5">File Manager</h1>
          <div className="arc-dim text-[12px] mt-0.5">{recent.length} recent · stored locally for this browser</div>
        </div>
      </div>

      <section className="arc-card overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
          <span className="arc-id"><b>upload</b></span>
        </div>
        <div className="p-4 flex flex-col gap-3">
          <label
            onDragOver={(e) => e.preventDefault()}
            onDrop={onDrop}
            className="border-2 border-dashed rounded-[var(--radius)] py-8 px-4 text-center cursor-pointer hover:bg-[var(--surface-2)] transition-colors"
            style={{ borderColor: 'var(--line)' }}
          >
            <input ref={fileRef} type="file" className="hidden" onChange={onPickFile} disabled={busy} />
            <UploadCloud size={28} className="mx-auto text-[var(--text-3)]" />
            <div className="text-[13px] font-medium mt-2">{busy ? 'Uploading…' : 'Drop a file or click to choose'}</div>
            <div className="arc-dim text-[11.5px] mt-0.5">POST /files/upload</div>
          </label>
          {message && (
            <div className="text-[12px]" style={{ color: message.kind === 'ok' ? 'var(--success, #2e7d32)' : 'var(--danger, #c62828)' }}>
              {message.text}
            </div>
          )}
        </div>
      </section>

      <section className="arc-card overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
          <span className="arc-id"><b>download-by-name</b></span>
        </div>
        <div className="p-4 flex items-center gap-2">
          <input className="arc-input flex-1" placeholder="filename"
                 value={lookup} onChange={(e) => setLookup(e.target.value)}
                 onKeyDown={(e) => { if (e.key === 'Enter') downloadByName(lookup) }} />
          <button className="arc-btn" onClick={() => downloadByName(lookup)}>
            <Search size={14} /> Download
          </button>
        </div>
      </section>

      <section className="arc-card overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
          <span className="arc-id"><b>recent</b></span>
          <span className="arc-id arc-dim2">{recent.length}</span>
        </div>
        {recent.length === 0 && <EmptyState title="No recent uploads" description="Files you upload here will be listed for quick re-download." />}
        {recent.map((f) => (
          <div key={f.filename} className="flex items-center gap-3 px-4 py-2.5 border-t border-[var(--line)] hover:bg-[var(--surface-2)] transition-colors">
            <FileText size={14} className="text-[var(--text-3)] shrink-0" />
            <div className="min-w-0 flex-1">
              <div className="text-[13px] font-medium text-[var(--text)] truncate">{f.filename}</div>
              <div className="arc-dim text-[11px] mt-0.5">
                {fmtSize(f.size)} · uploaded {new Date(f.uploadedAt).toLocaleString()}
              </div>
            </div>
            <button className="arc-btn" onClick={() => downloadByName(f.filename)}>
              <Download size={13} />
            </button>
            <button className="arc-btn" onClick={() => removeRecent(f.filename)} title="Remove from recents">
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </section>
    </div>
  )
}

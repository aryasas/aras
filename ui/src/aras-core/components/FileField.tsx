import React, { useState } from 'react'
import * as LucideIcons from 'lucide-react'
import api from '../../lib/api'
import { useNotify } from '../contexts/NotificationContext'

interface FileFieldProps {
  value?: string
  onChange: (value: string) => void
  label: string
}

export const FileField: React.FC<FileFieldProps> = ({ value, onChange, label }) => {
  const [uploading, setUploading] = useState(false)
  const notify = useNotify()

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await api.post('/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      onChange(res.data.url)
      notify('File uploaded successfully', 'success')
    } catch (err) {
      notify('Upload failed', 'error')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-2">
      <label className="text-xs font-black text-[var(--aras-muted)] uppercase tracking-widest">{label}</label>
      <div className="relative group">
        {value ? (
          <div className="flex items-center gap-4 p-4 bg-[var(--aras-panel-soft)] rounded-[var(--aras-radius-lg)] border border-[var(--aras-border)] group-hover:border-[var(--aras-border-strong)] transition-all">
            <div className="p-2 bg-[var(--aras-panel)] rounded-[var(--aras-radius)] shadow-sm text-[var(--aras-accent)]">
              <LucideIcons.File size={20} />
            </div>
            <div className="flex-1 truncate text-sm font-medium text-[var(--aras-muted)]">
              {value.split('/').pop()}
            </div>
            <button
              type="button"
              onClick={() => onChange('')}
              className="p-2 text-rose-500 hover:bg-rose-50 rounded-[var(--aras-radius)] transition-colors"
            >
              <LucideIcons.Trash2 size={18} />
            </button>
          </div>
        ) : (
          <label className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-[var(--aras-border)] rounded-[var(--aras-radius-lg)] hover:border-[var(--aras-accent)] hover:bg-[color-mix(in_srgb,var(--aras-accent)_10%,transparent)]/30 transition-all cursor-pointer group">
            <div className="p-4 bg-[var(--aras-panel-soft)] rounded-[var(--aras-radius-lg)] group-hover:bg-[color-mix(in_srgb,var(--aras-accent)_15%,transparent)] group-hover:text-[var(--aras-accent)] transition-colors mb-4">
              <LucideIcons.Upload size={24} />
            </div>
            <p className="text-sm font-bold text-[var(--aras-muted)]">Click to upload or drag & drop</p>
            <p className="text-xs text-[var(--aras-muted)] mt-1 uppercase font-black tracking-widest">Any file up to 50MB</p>
            <input
              type="file"
              className="hidden"
              onChange={handleFileChange}
              disabled={uploading}
            />
          </label>
        )}
        {uploading && (
          <div className="absolute inset-0 bg-[var(--aras-panel)]/80 backdrop-blur-sm rounded-[var(--aras-radius-lg)] flex items-center justify-center animate-pulse">
             <span className="font-black text-xs text-[var(--aras-accent)] uppercase tracking-widest">Uploading...</span>
          </div>
        )}
      </div>
    </div>
  )
}

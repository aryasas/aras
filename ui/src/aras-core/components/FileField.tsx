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
      <label className="text-xs font-black text-slate-400 uppercase tracking-widest">{label}</label>
      <div className="relative group">
        {value ? (
          <div className="flex items-center gap-4 p-4 bg-slate-50 rounded-2xl border border-slate-200 group-hover:border-indigo-300 transition-all">
            <div className="p-2 bg-white rounded-xl shadow-sm text-indigo-600">
              <LucideIcons.File size={20} />
            </div>
            <div className="flex-1 truncate text-sm font-medium text-slate-600">
              {value.split('/').pop()}
            </div>
            <button 
              type="button"
              onClick={() => onChange('')}
              className="p-2 text-rose-500 hover:bg-rose-50 rounded-lg transition-colors"
            >
              <LucideIcons.Trash2 size={18} />
            </button>
          </div>
        ) : (
          <label className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-slate-200 rounded-3xl hover:border-indigo-400 hover:bg-indigo-50/30 transition-all cursor-pointer group">
            <div className="p-4 bg-slate-50 rounded-2xl group-hover:bg-indigo-100 group-hover:text-indigo-600 transition-colors mb-4">
              <LucideIcons.Upload size={24} />
            </div>
            <p className="text-sm font-bold text-slate-500">Click to upload or drag & drop</p>
            <p className="text-xs text-slate-400 mt-1 uppercase font-black tracking-widest">Any file up to 50MB</p>
            <input 
              type="file" 
              className="hidden" 
              onChange={handleFileChange} 
              disabled={uploading}
            />
          </label>
        )}
        {uploading && (
          <div className="absolute inset-0 bg-white/80 backdrop-blur-sm rounded-3xl flex items-center justify-center animate-pulse">
             <span className="font-black text-xs text-indigo-600 uppercase tracking-widest">Uploading...</span>
          </div>
        )}
      </div>
    </div>
  )
}

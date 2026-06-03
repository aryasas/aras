import { useState } from 'react'
import { Plus, Trash2, Loader2, Copy, Check, Wand2 } from 'lucide-react'
import api from '../../lib/api'
import { devApi } from './devApi'

interface Field {
  name: string
  type: string
}

interface ScaffoldResult {
  filename: string
  code: string
}

const FIELD_TYPES = ['String', 'Integer', 'Boolean', 'DateTime', 'Text', 'Float']

// claude-sonnet-4-6
export default function ScaffoldTab() {
  const [kind, setKind] = useState<'app' | 'model'>('app')
  const [name, setName] = useState('')
  const [label, setLabel] = useState('')
  const [icon, setIcon] = useState('')
  const [fields, setFields] = useState<Field[]>([{ name: '', type: 'String' }])
  const [result, setResult] = useState<ScaffoldResult | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  // claude-sonnet-4-6
  const addField = () => setFields(f => [...f, { name: '', type: 'String' }])

  // claude-sonnet-4-6
  const removeField = (i: number) => setFields(f => f.filter((_, idx) => idx !== i))

  // claude-sonnet-4-6
  const updateField = (i: number, key: keyof Field, value: string) =>
    setFields(f => f.map((row, idx) => idx === i ? { ...row, [key]: value } : row))

  // claude-sonnet-4-6
  const generate = async () => {
    if (!name.trim()) { setError('Name is required.'); return }
    if (!/^[a-zA-Z0-9_]+$/.test(name)) { setError('Name must be alphanumeric/underscore only.'); return }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const body: Record<string, unknown> = { kind, name }
      if (label) body.label = label
      if (icon) body.icon = icon
      if (kind === 'model') body.fields = fields.filter(f => f.name.trim())
      const res = await api.post(devApi.scaffold, body)
      setResult(res.data as ScaffoldResult)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setError(err.response?.data?.detail || 'Scaffold generation failed.')
    } finally {
      setLoading(false)
    }
  }

  // claude-sonnet-4-6
  const copy = async () => {
    if (!result) return
    await navigator.clipboard.writeText(result.code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-black text-[var(--text)]">Scaffold Generator</h2>
        <span className="text-xs text-[var(--text-3)]">Generate boilerplate files for apps and models</span>
      </div>

      {/* Kind toggle */}
      <div className="flex gap-1 bg-[var(--surface-2)] p-1 rounded-[var(--radius-lg)] w-fit border border-[var(--line)]">
        {(['app', 'model'] as const).map(k => (
          <button
            key={k}
            onClick={() => { setKind(k); setResult(null); setError('') }}
            className={`px-5 py-2 rounded-[var(--radius)] font-semibold text-sm transition-all capitalize ${
              kind === k
                ? 'bg-[var(--surface)] text-[var(--text)] shadow-sm border border-[var(--line)]'
                : 'text-[var(--text-3)] hover:text-[var(--text-2)]'
            }`}
          >
            {k}
          </button>
        ))}
      </div>

      {/* Form */}
      <div className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius-lg)] p-6 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-bold text-[var(--text-3)] uppercase tracking-wider mb-1.5">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder={kind === 'app' ? 'my_app' : 'MyModel'}
              className="w-full px-3 py-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/40"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-[var(--text-3)] uppercase tracking-wider mb-1.5">Label</label>
            <input
              value={label}
              onChange={e => setLabel(e.target.value)}
              placeholder="Human-readable label"
              className="w-full px-3 py-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/40"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-[var(--text-3)] uppercase tracking-wider mb-1.5">Icon</label>
            <input
              value={icon}
              onChange={e => setIcon(e.target.value)}
              placeholder="Box"
              className="w-full px-3 py-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/40"
            />
          </div>
        </div>

        {/* Fields editor — model only */}
        {kind === 'model' && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[var(--text-3)] uppercase tracking-wider">Fields</span>
              <button
                onClick={addField}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--surface-2)] hover:bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius)] text-xs font-semibold text-[var(--text-2)] transition-all"
              >
                <Plus size={12} />
                Add Field
              </button>
            </div>
            <div className="space-y-2">
              {fields.map((field, i) => (
                <div key={i} className="flex gap-2 items-center">
                  <input
                    value={field.name}
                    onChange={e => updateField(i, 'name', e.target.value)}
                    placeholder="field_name"
                    className="flex-1 px-3 py-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] text-[var(--text)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/40 font-mono"
                  />
                  <select
                    value={field.type}
                    onChange={e => updateField(i, 'type', e.target.value)}
                    className="w-36 px-3 py-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] text-[var(--text)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/40"
                  >
                    {FIELD_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                  <button
                    onClick={() => removeField(i)}
                    disabled={fields.length === 1}
                    className="p-2 rounded-[var(--radius)] text-[var(--text-3)] hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-30 disabled:pointer-events-none"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="pt-2">
          <button
            onClick={generate}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 bg-[var(--accent)] text-white rounded-[var(--radius)] font-bold text-sm hover:opacity-90 disabled:opacity-50 transition-all"
          >
            {loading ? <Loader2 size={15} className="animate-spin" /> : <Wand2 size={15} />}
            Generate
          </button>
        </div>
      </div>

      {error && (
        <div className="px-4 py-3 rounded-[var(--radius)] bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>
      )}

      {result && (
        <div className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius-lg)] overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--line)] bg-[var(--surface-2)]">
            <code className="text-sm font-mono font-bold text-[var(--accent)]">{result.filename}</code>
            <button
              onClick={copy}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--surface)] hover:bg-[var(--surface-2)] border border-[var(--line)] rounded-[var(--radius)] text-xs font-semibold text-[var(--text-2)] transition-all"
            >
              {copied ? <Check size={12} className="text-emerald-600" /> : <Copy size={12} />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <pre className="p-4 text-xs font-mono text-[var(--text)] overflow-x-auto whitespace-pre bg-slate-950 text-slate-200 max-h-[600px] overflow-y-auto">{result.code}</pre>
        </div>
      )}
    </div>
  )
}

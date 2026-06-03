import { useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle2, Key, RefreshCw, XCircle } from 'lucide-react'
import api from '../lib/api'
import { Card } from '../components/Card'
import { PageShell } from '../components/PageShell'
import { useAras } from '../aras-core/hooks/useAras'
import { useAsyncData } from '../hooks/useAsyncData'
import { fmtDate } from '../lib/formatters'

interface LicenseStatusResponse {
  valid: boolean
  tenant_id?: string | null
  days_remaining?: number | null
  expired?: boolean
  expires_at?: string | null
  expiry_date?: string | null
  reason?: string | null
}

const daysColor = (days?: number | null) => {
  if (days == null) return 'text-[var(--app-muted)]'
  if (days > 30) return 'text-emerald-600'
  if (days > 7) return 'text-amber-600'
  return 'text-red-600'
}

// claude-sonnet-4-6
export default function LicenseStatus() {
  const { notify } = useAras()
  const [activating, setActivating] = useState(false)
  const [activateOpen, setActivateOpen] = useState(false)
  const [token, setToken] = useState('')

  const { data: status, loading, reload: reloadStatus } = useAsyncData<LicenseStatusResponse>(
    async () => {
      try {
        const res = await api.get('/license/status')
        return res.data
      } catch (err: any) {
        notify(err.response?.data?.detail || 'Could not load license status', 'error')
        throw err
      }
    }
  )

  const expiryValue = status?.expires_at ?? status?.expiry_date ?? null
  const expiryLabel = useMemo(() => {
    if (!expiryValue) return 'Not provided'
    return fmtDate(expiryValue)
  }, [expiryValue])

  const activateLicense = async () => {
    const trimmed = token.trim()
    if (!trimmed) return

    setActivating(true)
    try {
      await api.post('/license/activate', { token: trimmed })
      setToken('')
      setActivateOpen(false)
      notify('License activated', 'success')
      reloadStatus()
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Failed to activate license', 'error')
    } finally {
      setActivating(false)
    }
  }

  const daysRemaining = status?.days_remaining
  const expiringSoon = status?.valid && daysRemaining != null && daysRemaining <= 7

  return (
    <PageShell>
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-[var(--app-text)]">License</h1>
            <p className="mt-1 text-sm text-[var(--app-muted)]">Instance license status and activation.</p>
          </div>
          <button
            type="button"
            onClick={() => setActivateOpen(true)}
            className="inline-flex items-center justify-center gap-2 rounded-[var(--app-radius)] bg-[var(--app-accent)] px-4 py-2.5 text-sm font-bold text-white shadow-sm transition-colors hover:bg-indigo-700"
          >
            <Key size={16} />
            Activate
          </button>
        </div>

        {expiringSoon && (
          <div className="flex items-start gap-3 rounded-[var(--app-radius)] border border-red-200 bg-red-50 p-4 text-red-800">
            <AlertTriangle size={20} className="mt-0.5 shrink-0" />
            <div>
              <div className="font-bold">License expires soon</div>
              <div className="text-sm">This instance license expires in {daysRemaining} day{daysRemaining === 1 ? '' : 's'}.</div>
            </div>
          </div>
        )}

        <Card className="p-6">
          {loading ? (
            <div className="flex items-center gap-3 text-sm text-[var(--app-muted)]">
              <RefreshCw size={18} className="animate-spin" />
              Loading license status...
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-bold text-[var(--app-text)]">Current License</h2>
                  <p className="text-sm text-[var(--app-muted)]">Status returned by this instance.</p>
                </div>
                {status?.valid ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-sm font-bold text-emerald-700 ring-1 ring-emerald-200">
                    <CheckCircle2 size={15} />
                    Valid
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1 text-sm font-bold text-red-700 ring-1 ring-red-200">
                    <XCircle size={15} />
                    Invalid
                  </span>
                )}
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-[var(--app-radius)] border border-[var(--app-border)] bg-[var(--app-panel-soft)] p-4">
                  <div className="text-xs font-bold uppercase tracking-wide text-[var(--app-muted)]">Tenant ID</div>
                  <div className="mt-2 break-all text-sm font-semibold text-[var(--app-text)]">{status?.tenant_id || '-'}</div>
                </div>
                <div className="rounded-[var(--app-radius)] border border-[var(--app-border)] bg-[var(--app-panel-soft)] p-4">
                  <div className="text-xs font-bold uppercase tracking-wide text-[var(--app-muted)]">Days Remaining</div>
                  <div className={`mt-2 text-2xl font-black ${daysColor(daysRemaining)}`}>{daysRemaining ?? '-'}</div>
                </div>
                <div className="rounded-[var(--app-radius)] border border-[var(--app-border)] bg-[var(--app-panel-soft)] p-4">
                  <div className="text-xs font-bold uppercase tracking-wide text-[var(--app-muted)]">Expiry Date</div>
                  <div className="mt-2 text-sm font-semibold text-[var(--app-text)]">{expiryLabel}</div>
                </div>
              </div>

              {!status?.valid && (
                <div className="rounded-[var(--app-radius)] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                  This instance does not have a valid license{status?.reason ? `: ${status.reason}` : '.'}
                </div>
              )}
            </div>
          )}
        </Card>
      </div>

      {activateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-[var(--app-radius-lg)] bg-[var(--app-panel)] p-6 shadow-2xl">
            <h2 className="text-lg font-bold text-[var(--app-text)]">Activate License</h2>
            <p className="mt-1 text-sm text-[var(--app-muted)]">Paste the license token for this instance.</p>
            <textarea
              value={token}
              onChange={(event) => setToken(event.target.value)}
              rows={8}
              className="mt-4 w-full resize-y rounded-[var(--app-radius)] border border-[var(--app-border)] bg-[var(--app-panel-soft)] px-3 py-2 font-mono text-sm text-slate-800 outline-none transition-colors focus:border-indigo-400 focus:bg-[var(--app-panel)] focus:ring-2 focus:ring-indigo-100"
              placeholder="eyJ..."
            />
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setActivateOpen(false)}
                className="rounded-[var(--app-radius)] border border-[var(--app-border)] px-4 py-2 text-sm font-semibold text-slate-600 transition-colors hover:bg-[var(--app-panel-soft)]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={activateLicense}
                disabled={activating || !token.trim()}
                className="rounded-[var(--app-radius)] bg-[var(--app-accent)] px-4 py-2 text-sm font-bold text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {activating ? 'Activating...' : 'Activate'}
              </button>
            </div>
          </div>
        </div>
      )}
    </PageShell>
  )
}

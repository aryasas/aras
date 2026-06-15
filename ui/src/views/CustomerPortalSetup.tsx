// claude-opus-4-7
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { AlertCircle, ArrowRight, CheckCircle2, Clock3, KeyRound, Lock, ShieldAlert, XCircle } from 'lucide-react'
import { ArasLogo } from '../components/ArasLogo'
import type { ReactNode } from 'react'

function SetupShell({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string
  title: string
  description: string
  children: ReactNode
}) {
  return (
    <main className="arc arc-bg arc-dotgrid min-h-screen px-4 py-10">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-lg items-center">
        <section className="arc-card w-full overflow-hidden bg-[var(--surface)] shadow-[var(--shadow-card-lift)]">
          <div className="px-8 pt-8 pb-2 flex items-start gap-4">
            <ArasLogo size="lg" />
            <div className="flex-1 min-w-0">
              <div className="arc-id"><b>arc</b>/portal/<b>{eyebrow}</b></div>
              <h1 className="mt-1 text-[28px] font-semibold tracking-tight text-[var(--text)]">{title}</h1>
              <p className="mt-1 text-sm leading-6 text-[var(--text-2)]">{description}</p>
            </div>
          </div>
          {children}
        </section>
      </div>
    </main>
  )
}

export default function CustomerPortalSetup() {
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const status = params.get('status')
  const invoiceId = params.get('invoice_id')
  const subscriptionId = params.get('subscription_id')
  const [paymentState, setPaymentState] = useState(status || '')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  useEffect(() => {
    if (!status || status === 'failed' || (!invoiceId && !subscriptionId)) return
    let cancelled = false
    let attempts = 0
    const poll = async () => {
      attempts += 1
      try {
        const query = invoiceId ? `invoice_id=${invoiceId}` : `subscription_id=${subscriptionId}`
        const res = await fetch(`/api/v1/saas/billing/invoices?${query}`)
        if (res.ok) {
          const data = await res.json().catch(() => [])
          const payload = data?.data && typeof data.data === 'object' ? data.data : data
          const invoices = Array.isArray(payload) ? payload : []
          const target = invoiceId ? invoices.find((invoice: any) => String(invoice.id) === invoiceId) : invoices[0]
          if (target?.status === 'paid') {
            if (!cancelled) setPaymentState('success')
            return
          }
        }
      } catch {
        // keep polling until timeout
      }
      if (!cancelled && attempts < 20) window.setTimeout(poll, 3000)
      if (!cancelled && attempts >= 20) setPaymentState('pending')
    }
    poll()
    return () => { cancelled = true }
  }, [invoiceId, status, subscriptionId])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      const res = await fetch('/api/v1/saas/portal/setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError(data.detail || 'Setup link is invalid or has expired.')
        return
      }
      setDone(true)
    } finally {
      setLoading(false)
    }
  }

  if (status && !token) {
    const failed = paymentState === 'failed'
    const success = paymentState === 'success'
    const icon = success ? <CheckCircle2 size={28} /> : failed ? <XCircle size={28} /> : <Clock3 size={28} />
    const tone = success
      ? { bg: 'bg-emerald-50', text: 'text-emerald-600' }
      : failed
        ? { bg: 'bg-red-50', text: 'text-red-600' }
        : { bg: 'bg-amber-50', text: 'text-amber-600' }
    return (
      <SetupShell
        eyebrow="setup-status"
        title={success ? 'Payment confirmed' : failed ? 'Payment failed' : 'Payment pending'}
        description={success
          ? 'Your invoice has been paid. Provisioning will continue automatically.'
          : failed
            ? 'The provider reported a failed payment. Return to billing to try again.'
            : 'We are waiting for the provider to confirm this invoice.'}
      >
        <div className="px-8 py-8 text-center">
          <div className={`mx-auto flex h-16 w-16 items-center justify-center rounded-[var(--radius-lg)] ${tone.bg} ${tone.text}`}>
            {icon}
          </div>
          <Link to="/portal?tab=billing" className="arc-btn primary mt-6 inline-flex items-center">
            <ArrowRight size={16} />
            Go to billing
          </Link>
        </div>
      </SetupShell>
    )
  }

  if (!token) {
    return (
      <SetupShell
        eyebrow="setup-invalid"
        title="Invalid setup link"
        description="This setup link is missing a token. Use the full link sent by your administrator."
      >
        <div className="px-8 py-8">
          <div
            className="flex items-center gap-3 rounded-[var(--radius)] border px-4 py-3 text-sm"
            style={{
              background: 'color-mix(in oklch, var(--danger) 8%, var(--surface))',
              borderColor: 'color-mix(in oklch, var(--danger) 25%, var(--line))',
              color: 'var(--danger)',
            }}
          >
            <ShieldAlert size={18} />
            <span>Request a fresh setup email from your administrator to continue.</span>
          </div>
        </div>
      </SetupShell>
    )
  }

  if (done) {
    return (
      <SetupShell
        eyebrow="setup-complete"
        title="Password set"
        description="Your portal account is ready. Sign in to manage billing, access, and subscription details."
      >
        <div className="px-8 py-8 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[var(--radius-lg)] bg-emerald-50 text-emerald-600">
            <CheckCircle2 size={28} />
          </div>
          <Link to="/portal" className="arc-btn primary mt-6 inline-flex items-center">
            <ArrowRight size={16} />
            Go to portal
          </Link>
        </div>
      </SetupShell>
    )
  }

  return (
    <SetupShell
      eyebrow="setup-password"
      title="Set your password"
      description="Create a password to activate your portal account and finish setup."
    >
      <form onSubmit={submit} className="px-8 py-6 flex flex-col gap-5">
        {error ? (
          <div
            className="flex items-center gap-2 rounded-[var(--radius)] border px-3 py-2 text-[12.5px]"
            style={{
              background: 'color-mix(in oklch, var(--danger) 10%, var(--surface))',
              borderColor: 'color-mix(in oklch, var(--danger) 30%, var(--line))',
              color: 'var(--danger)',
            }}
          >
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        ) : null}

        <label className="flex flex-col gap-1.5">
          <span className="arc-id">new-pass</span>
          <span className="relative">
            <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
            <input
              id="pw"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="arc-input"
              style={{ paddingLeft: 32 }}
              placeholder="At least 8 characters"
            />
          </span>
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="arc-id">confirm-pass</span>
          <span className="relative">
            <KeyRound size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
            <input
              id="pw2"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              minLength={8}
              className="arc-input"
              style={{ paddingLeft: 32 }}
              placeholder="Repeat your password"
            />
          </span>
        </label>

        <button type="submit" disabled={loading} className="arc-btn primary w-full justify-center" style={{ height: 44 }}>
          {loading ? 'Saving password…' : 'Set password'}
        </button>
      </form>
    </SetupShell>
  )
}

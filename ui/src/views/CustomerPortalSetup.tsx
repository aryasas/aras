// claude-opus-4-7
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

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
    return (
      <main className="mx-auto max-w-md px-6 py-12">
        <h1 className="text-2xl font-bold text-[var(--app-text)]">
          {success ? 'Payment confirmed' : failed ? 'Payment failed' : 'Payment pending'}
        </h1>
        <p className="mt-3 text-sm text-[var(--app-muted)]">
          {success
            ? 'Your invoice has been paid. Provisioning will continue automatically.'
            : failed
              ? 'The provider reported a failed payment. Please return to billing and try again.'
              : 'We are waiting for the provider to confirm this invoice.'}
        </p>
        <Link to="/portal?tab=billing" className="mt-6 inline-block rounded-[var(--app-radius)] bg-[var(--app-accent)] px-5 py-2.5 text-sm font-bold text-white hover:bg-indigo-700">Go to billing</Link>
      </main>
    )
  }

  if (!token) {
    return (
      <main className="mx-auto max-w-md px-6 py-12">
        <h1 className="text-2xl font-bold text-[var(--app-text)]">Invalid setup link</h1>
        <p className="mt-3 text-sm text-[var(--app-muted)]">This link is missing a token. Please use the link your admin sent you.</p>
      </main>
    )
  }

  if (done) {
    return (
      <main className="mx-auto max-w-md px-6 py-12">
        <h1 className="text-2xl font-bold text-[var(--app-text)]">Password set</h1>
        <p className="mt-3 text-sm text-[var(--app-muted)]">You can now sign in to your portal.</p>
        <Link to="/portal" className="mt-6 inline-block rounded-[var(--app-radius)] bg-[var(--app-accent)] px-5 py-2.5 text-sm font-bold text-white hover:bg-indigo-700">Go to portal</Link>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-md px-6 py-12">
      <h1 className="text-3xl font-bold text-[var(--app-text)]">Set your password</h1>
      <p className="mt-2 text-sm text-[var(--app-muted)]">Welcome. Create a password to activate your account.</p>
      <form onSubmit={submit} className="mt-8 space-y-5">
        <div>
          <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="pw">New password</label>
          <input id="pw" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8}
            className="mt-2 w-full rounded-[var(--app-radius)] border border-[var(--app-border)] px-4 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100" />
        </div>
        <div>
          <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="pw2">Confirm password</label>
          <input id="pw2" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8}
            className="mt-2 w-full rounded-[var(--app-radius)] border border-[var(--app-border)] px-4 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100" />
        </div>
        {error && <div className="rounded-[var(--app-radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}
        <button type="submit" disabled={loading}
          className="rounded-[var(--app-radius)] bg-[var(--app-accent)] px-5 py-2.5 text-sm font-bold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50">
          {loading ? 'Saving...' : 'Set password'}
        </button>
      </form>
    </main>
  )
}

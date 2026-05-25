import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

interface Plan {
  id: number
  name: string
  price: number
  currency: string
}

const initialForm = {
  email: '',
  company_name: '',
  full_name: '',
  phone: '',
  plan_id: '',
}

export default function CustomerSignup() {
  const [searchParams] = useSearchParams()
  const [plans, setPlans] = useState<Plan[]>([])
  const [form, setForm] = useState({ ...initialForm, plan_id: searchParams.get('plan') || '' })
  const [submitting, setSubmitting] = useState(false)
  const [successEmail, setSuccessEmail] = useState('')
  const [successSubscriptionId, setSuccessSubscriptionId] = useState<number | string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [plansError, setPlansError] = useState<string | null>(null)

  useEffect(() => {
    const loadPlans = async () => {
      try {
        setPlansError(null)
        const res = await fetch('/api/v1/saas/plans/public')
        if (!res.ok) throw new Error('Could not load plans.')
        const data = await res.json()
        setPlans(Array.isArray(data) ? data : [])
      } catch {
        setPlans([])
        setPlansError('Could not load plans. You can still submit your signup without selecting a plan.')
      }
    }
    loadPlans()
  }, [])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      const payload = {
        email: form.email,
        company_name: form.company_name,
        full_name: form.full_name,
        phone: form.phone || undefined,
        plan_id: form.plan_id ? Number(form.plan_id) : undefined,
      }
      const response = await fetch('/api/v1/saas/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (response.status === 409) {
        setError('An account with this email already exists.')
        return
      }
      if (!response.ok) {
        setError('Could not submit your signup.')
        return
      }
      const data = await response.json().catch(() => ({}))
      const responseData = data?.data && typeof data.data === 'object' ? data.data : data
      setSuccessEmail(form.email)
      setSuccessSubscriptionId(responseData.subscription_id ?? null)
      setForm(initialForm)
    } finally {
      setSubmitting(false)
    }
  }

  if (successEmail) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-[var(--app-radius)] border border-[var(--app-border)] bg-white px-6 py-5">
          <h1 className="text-2xl font-bold text-[var(--app-text)]">Signup received</h1>
          <p className="mt-3 text-sm text-[var(--app-muted)]">
            Your signup is pending approval. We'll email you at {successEmail} with login details.
          </p>
          {successSubscriptionId && (
            <p className="mt-3 text-sm font-semibold text-[var(--app-text)]">Reference: #{successSubscriptionId}</p>
          )}
          <Link to="/welcome" className="mt-5 inline-flex rounded-[var(--app-radius)] bg-[var(--app-accent)] px-5 py-2.5 text-sm font-bold text-white">
            Back to welcome
          </Link>
        </div>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <h1 className="text-3xl font-bold text-[var(--app-text)]">Start your free trial</h1>

      <form onSubmit={handleSubmit} className="mt-8 space-y-5">
        {plansError && (
          <div className="rounded-[var(--app-radius)] border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
            {plansError}
          </div>
        )}

        <div>
          <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
            required
            className="mt-2 w-full rounded-[var(--app-radius)] border border-[var(--app-border)] px-4 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="company_name">Company</label>
          <input
            id="company_name"
            value={form.company_name}
            onChange={(event) => setForm({ ...form, company_name: event.target.value })}
            required
            className="mt-2 w-full rounded-[var(--app-radius)] border border-[var(--app-border)] px-4 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="full_name">Full name</label>
          <input
            id="full_name"
            value={form.full_name}
            onChange={(event) => setForm({ ...form, full_name: event.target.value })}
            required
            className="mt-2 w-full rounded-[var(--app-radius)] border border-[var(--app-border)] px-4 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="phone">Phone</label>
          <input
            id="phone"
            value={form.phone}
            onChange={(event) => setForm({ ...form, phone: event.target.value })}
            className="mt-2 w-full rounded-[var(--app-radius)] border border-[var(--app-border)] px-4 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="plan_id">Plan</label>
          <select
            id="plan_id"
            value={form.plan_id}
            onChange={(event) => setForm({ ...form, plan_id: event.target.value })}
            className="mt-2 w-full rounded-[var(--app-radius)] border border-[var(--app-border)] px-4 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
          >
            <option value="">Select a plan</option>
            {plans.map((plan) => (
              <option key={plan.id} value={plan.id}>{plan.name} - {plan.price} {plan.currency}/mo</option>
            ))}
          </select>
        </div>

        {error && (
          <div className="rounded-[var(--app-radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="rounded-[var(--app-radius)] bg-[var(--app-accent)] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? 'Submitting...' : 'Submit signup'}
        </button>
      </form>
    </main>
  )
}

import { useEffect, useState } from 'react'
import { Save } from 'lucide-react'
import api from '../../lib/api'

interface Plan {
  id: number
  plan_key: string
  name: string
  price: number
  currency: string
  trial_days?: number
  annual_discount_pct?: number
  default_provider_code?: string
}

const providerOptions = ['', 'stripe', 'midtrans', 'xendit']

export default function Plans() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [savingId, setSavingId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.get('/saas/plans/public')
      .then((res) => setPlans(Array.isArray(res.data) ? res.data : []))
      .catch((err) => setError(err.message || 'Failed to load plans.'))
  }, [])

  const updatePlan = (id: number, patch: Partial<Plan>) => {
    setPlans((current) => current.map((plan) => plan.id === id ? { ...plan, ...patch } : plan))
  }

  const save = async (plan: Plan) => {
    setSavingId(plan.id)
    setError(null)
    try {
      await api.patch(`/saas/plan/${plan.id}`, {
        trial_days: Number(plan.trial_days || 0),
        annual_discount_pct: Number(plan.annual_discount_pct || 0),
        default_provider_code: plan.default_provider_code || null,
      })
    } catch (err: any) {
      setError(err.message || 'Failed to save plan.')
    } finally {
      setSavingId(null)
    }
  }

  return (
    <div className="p-6 lg:p-8">
      <p className="arc-id"><b>saas</b>/plans</p>
      <h1 className="mt-2 text-2xl font-bold text-[var(--text)]">Plans</h1>
      {error && <div className="mt-5 rounded-[var(--radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}

      <div className="mt-6 grid gap-4">
        {plans.map((plan) => (
          <section key={plan.id} className="arc-card p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase text-[var(--text-3)]">{plan.plan_key}</p>
                <h2 className="mt-1 text-lg font-bold text-[var(--text)]">{plan.name}</h2>
                <p className="text-sm text-[var(--text-3)]">{plan.currency} {Number(plan.price || 0).toLocaleString('id-ID')}</p>
              </div>
              <button
                type="button"
                onClick={() => save(plan)}
                disabled={savingId === plan.id}
                className="inline-flex items-center gap-2 rounded-[var(--radius)] bg-[var(--accent)] px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                <Save size={15} /> {savingId === plan.id ? 'Saving...' : 'Save'}
              </button>
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <label className="block">
                <span className="text-sm font-semibold text-[var(--text)]">Trial days</span>
                <input
                  type="number"
                  min={0}
                  value={plan.trial_days ?? 0}
                  onChange={(event) => updatePlan(plan.id, { trial_days: Number(event.target.value) })}
                  className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
                />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[var(--text)]">Annual discount %</span>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={plan.annual_discount_pct ?? 0}
                  onChange={(event) => updatePlan(plan.id, { annual_discount_pct: Number(event.target.value) })}
                  className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
                />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[var(--text)]">Provider override</span>
                <select
                  value={plan.default_provider_code || ''}
                  onChange={(event) => updatePlan(plan.id, { default_provider_code: event.target.value })}
                  className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
                >
                  {providerOptions.map((provider) => (
                    <option key={provider || 'auto'} value={provider}>{provider || 'Auto route'}</option>
                  ))}
                </select>
              </label>
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}

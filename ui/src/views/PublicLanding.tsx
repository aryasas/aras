import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

interface LandingSection {
  key: string
  title: string
  subtitle?: string | null
  body: string
  image_url?: string | null
  cta_label?: string | null
  cta_url?: string | null
}

interface Plan {
  id: number
  name: string
  price: number
  currency: string
  max_users: number
  max_branches: number
  features?: string | string[] | null
}

export default function PublicLanding() {
  const [sections, setSections] = useState<LandingSection[]>([])
  const [plans, setPlans] = useState<Plan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [landingRes, plansRes] = await Promise.all([
        fetch('/api/v1/web/landing'),
        fetch('/api/v1/saas/plans/public'),
      ])
      if (!landingRes.ok || !plansRes.ok) {
        throw new Error('Could not load landing page content.')
      }
      const [landingData, plansData] = await Promise.all([
        landingRes.json(),
        plansRes.json(),
      ])
      setSections(Array.isArray(landingData) ? landingData : [])
      setPlans(Array.isArray(plansData) ? plansData : [])
    } catch {
      setError('Some page content could not be loaded.')
      setSections([])
      setPlans([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const byKey = useMemo(() => {
    return sections.reduce<Record<string, LandingSection>>((acc, section) => {
      acc[section.key] = section
      return acc
    }, {})
  }, [sections])

  const hero = byKey.hero
  const features = byKey.features
  const pricingIntro = byKey.pricing_intro
  const cta = byKey.cta
  const footer = byKey.footer
  const featureItems = (features?.body || '').split('\n\n').map((item) => item.trim()).filter(Boolean)

  if (loading) {
    return (
      <main className="min-h-screen bg-[var(--bg)] text-[var(--text)] flex items-center justify-center">
        <div className="text-sm text-[var(--text-3)]">Loading...</div>
      </main>
    )
  }

  if (error) {
    return (
      <main className="min-h-screen bg-[var(--bg)] text-[var(--text)] flex items-center justify-center px-6">
        <div className="max-w-md text-center">
          <h1 className="text-2xl font-semibold">Content unavailable</h1>
          <p className="mt-3 text-sm leading-6 text-[var(--text-3)]">{error}</p>
          <button
            type="button"
            onClick={load}
            className="mt-6 inline-flex h-10 items-center rounded-[var(--radius)] bg-[var(--accent)] px-4 text-sm font-semibold text-white"
          >
            Retry
          </button>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <section className="mx-auto max-w-6xl px-6 py-16 md:py-24">
        <div className="grid gap-10 md:grid-cols-[1.1fr_0.9fr] md:items-center">
          <div>
            <h1 className="text-4xl font-bold tracking-tight md:text-6xl">{hero?.title || 'Aras'}</h1>
            {hero?.subtitle && <p className="mt-5 max-w-2xl text-lg text-[var(--text-2)]">{hero.subtitle}</p>}
            {hero?.body && <p className="mt-4 max-w-2xl text-sm leading-7 text-[var(--text-3)]">{hero.body}</p>}
            <Link
              to={hero?.cta_url || '/signup'}
              className="mt-8 inline-flex h-11 items-center rounded-[var(--radius)] bg-[var(--accent)] px-5 text-sm font-semibold text-white"
            >
              {hero?.cta_label || 'Start free trial'}
            </Link>
          </div>
          {hero?.image_url && (
            <img
              src={hero.image_url}
              alt=""
              className="aspect-[4/3] w-full rounded-[var(--radius)] border border-[var(--line)] object-cover"
            />
          )}
        </div>
      </section>

      {features && (
        <section className="border-y border-[var(--line)] bg-[var(--surface)]">
          <div className="mx-auto max-w-6xl px-6 py-14">
            <h2 className="text-2xl font-semibold">{features.title}</h2>
            {features.subtitle && <p className="mt-2 text-sm text-[var(--text-3)]">{features.subtitle}</p>}
            <div className="mt-8 grid gap-4 md:grid-cols-3">
              {featureItems.map((item, index) => (
                <article key={`${item}-${index}`} className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--bg)] p-5">
                  <p className="whitespace-pre-line text-sm leading-6 text-[var(--text-2)]">{item}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="mx-auto max-w-6xl px-6 py-14">
        <h2 className="text-2xl font-semibold">{pricingIntro?.title || 'Pricing'}</h2>
        {pricingIntro?.subtitle && <p className="mt-2 text-sm text-[var(--text-3)]">{pricingIntro.subtitle}</p>}
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {plans.map((plan) => (
            <article key={plan.id} className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] p-5">
              <h3 className="text-lg font-semibold">{plan.name}</h3>
              <div className="mt-3 text-3xl font-bold">
                {plan.price} <span className="text-sm font-medium text-[var(--text-3)]">{plan.currency}/mo</span>
              </div>
              <div className="mt-5 space-y-2 text-sm text-[var(--text-2)]">
                <p>{plan.max_users} users</p>
                <p>{plan.max_branches} branches</p>
              </div>
              <Link
                to={`/signup?plan=${plan.id}`}
                className="mt-6 inline-flex h-10 items-center rounded-[var(--radius)] bg-[var(--accent)] px-4 text-sm font-semibold text-white"
              >
                Get Started
              </Link>
            </article>
          ))}
        </div>
      </section>

      {cta && (
        <section className="bg-[var(--surface)]">
          <div className="mx-auto max-w-6xl px-6 py-14 text-center">
            <h2 className="text-2xl font-semibold">{cta.title}</h2>
            {cta.subtitle && <p className="mx-auto mt-2 max-w-2xl text-sm text-[var(--text-3)]">{cta.subtitle}</p>}
            <Link
              to={cta.cta_url || '/signup'}
              className="mt-6 inline-flex h-10 items-center rounded-[var(--radius)] bg-[var(--accent)] px-4 text-sm font-semibold text-white"
            >
              {cta.cta_label || 'Get Started'}
            </Link>
          </div>
        </section>
      )}

      {footer && (
        <footer className="mx-auto max-w-6xl px-6 py-8 text-center text-sm text-[var(--text-3)]">
          <p>{footer.title}</p>
          {footer.body && <p className="mt-2">{footer.body}</p>}
        </footer>
      )}
    </main>
  )
}

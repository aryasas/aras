// claude-sonnet-4-6
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { MODULE_LABELS, formatPrice } from '../lib/planUtils'
import { useLanguage } from '../context/LanguageContext'

interface Plan {
  id: number
  plan_key: string
  name: string
  price: number
  currency: string
  max_users: number
  max_branches: number
  active_modules: string[]
  features?: { included?: string[]; apps?: string[] } | null
}

const PUBLIC_PLAN_KEYS = new Set(['free', 'lite', 'growth', 'business'])
const EN_PLAN_FEATURES: Record<string, string[]> = {
  free: ['POS module', '50 transactions/month', '30 products', 'Basic daily reports'],
  lite: ['POS + Inventory + Payables/Receivables', 'Unlimited transactions', '500 products', 'Monthly reports', 'PDF export'],
  growth: ['Everything in Lite', 'Full accounting reports', 'Unlimited products', 'Up to 2 branches', 'Chat support'],
  business: ['Everything in Growth', 'Unlimited branches', '25 users', 'API access', 'Priority support', 'Onboarding'],
}

const initialForm = {
  email: '',
  company_name: '',
  full_name: '',
  phone: '',
  plan_key: '',
}

export default function CustomerSignup() {
  const { lang, setLang, t } = useLanguage()
  const [searchParams] = useSearchParams()
  const [plans, setPlans] = useState<Plan[]>([])
  const [form, setForm] = useState({ ...initialForm, plan_key: searchParams.get('plan') || '' })
  const [submitting, setSubmitting] = useState(false)
  const [successEmail, setSuccessEmail] = useState('')
  const [successId, setSuccessId] = useState<number | string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const moduleLabel = (module: string) => t(`public.modules.${module}`, MODULE_LABELS[module] ?? module)
  const localizedPrice = (price: number) => {
    if (price === 0) return t('public.pricing.free', 'Gratis')
    return lang === 'id'
      ? formatPrice(price)
      : `Rp ${price.toLocaleString('id-ID')}${t('public.pricing.perMonth', '/month')}`
  }
  const planFeatures = (plan: Plan) => {
    if (lang === 'en' && EN_PLAN_FEATURES[plan.plan_key]) return EN_PLAN_FEATURES[plan.plan_key]
    return plan.features?.included ?? []
  }

  useEffect(() => {
    fetch('/api/v1/saas/plans/public')
      .then((r) => r.ok ? r.json() : [])
      .then((data) => setPlans(Array.isArray(data) ? data.filter((p: Plan) => PUBLIC_PLAN_KEYS.has(p.plan_key)) : []))
      .catch(() => setPlans([]))
  }, [])

  const selectedPlan = plans.find((p) => p.plan_key === form.plan_key) ?? null

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
        plan_id: selectedPlan?.id ?? undefined,
      }
      const res = await fetch('/api/v1/saas/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (res.status === 409) { setError(t('public.signup.duplicateEmail', 'Email ini sudah terdaftar.')); return }
      if (!res.ok) { setError(t('public.signup.failed', 'Pendaftaran gagal. Silakan coba lagi.')); return }
      const data = await res.json().catch(() => ({}))
      const d = data?.data && typeof data.data === 'object' ? data.data : data
      setSuccessEmail(form.email)
      setSuccessId(d.subscription_id ?? null)
      setForm(initialForm)
    } finally {
      setSubmitting(false)
    }
  }

  if (successEmail) {
    return (
      <main className="mx-auto max-w-lg px-6 py-16 text-center">
        <div className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-8">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-2xl">✓</div>
          <h1 className="mt-4 text-xl font-bold">{t('public.signup.successTitle', 'Pendaftaran diterima!')}</h1>
          <p className="mt-3 text-sm leading-relaxed text-[var(--text-2)]">
            {t('public.signup.successBody', 'Tim kami akan menghubungi Anda di {email} dalam 1x24 jam untuk proses aktivasi.').replace('{email}', successEmail)}
          </p>
          {successId && <p className="mt-3 text-xs text-[var(--text-3)]">{t('public.signup.reference', 'Nomor referensi')}: #{successId}</p>}
          <Link to="/welcome" className="mt-6 inline-flex rounded-[var(--radius)] bg-[var(--accent)] px-5 py-2.5 text-sm font-semibold text-white">
            {t('public.signup.backHome', 'Kembali ke Beranda')}
          </Link>
        </div>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <Link to="/welcome" className="text-sm text-[var(--text-3)] hover:text-[var(--text)]">← {t('public.signup.back', 'Kembali')}</Link>
          <h1 className="mt-4 text-3xl font-bold">{t('public.signup.title', 'Daftar ARAS')}</h1>
          <p className="mt-1 text-sm text-[var(--text-2)]">{t('public.signup.subtitle', 'Mulai gratis, tanpa kartu kredit.')}</p>
        </div>
        <button
          type="button"
          onClick={() => setLang(lang === 'id' ? 'en' : 'id')}
          className="rounded-[var(--radius)] border border-[var(--line)] px-2.5 py-1 text-xs font-semibold text-[var(--text-2)] hover:text-[var(--text)]"
        >
          {lang === 'id' ? 'EN' : 'ID'}
        </button>
      </div>

      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-semibold" htmlFor="full_name">{t('public.signup.fullName', 'Nama Lengkap')}</label>
              <input
                id="full_name"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                required
                placeholder="Budi Santoso"
                className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-4 py-2.5 text-sm outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold" htmlFor="email">{t('public.signup.email', 'Email')}</label>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
                placeholder="budi@toko.com"
                className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-4 py-2.5 text-sm outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold" htmlFor="company_name">{t('public.signup.company', 'Nama Usaha')}</label>
              <input
                id="company_name"
                value={form.company_name}
                onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                required
                placeholder="Toko Sembako Makmur"
                className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-4 py-2.5 text-sm outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold" htmlFor="phone">{t('public.signup.phone', 'Nomor HP')}</label>
              <input
                id="phone"
                type="tel"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="08123456789"
                className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-4 py-2.5 text-sm outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold" htmlFor="plan_key">{t('public.signup.plan', 'Pilih Paket')}</label>
            <select
              id="plan_key"
              value={form.plan_key}
              onChange={(e) => setForm({ ...form, plan_key: e.target.value })}
              className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-4 py-2.5 text-sm outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
            >
              <option value="">{t('public.signup.planPlaceholder', '-- Pilih paket --')}</option>
              {plans.map((p) => (
                <option key={p.id} value={p.plan_key}>
                  {p.name} — {localizedPrice(p.price)}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="rounded-[var(--radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-[var(--radius)] bg-[var(--accent)] py-3 text-sm font-semibold text-white hover:bg-[var(--aras-accent-strong)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? t('public.signup.submitting', 'Mengirim...') : t('public.signup.submit', 'Daftar Sekarang')}
          </button>

          <p className="text-center text-xs text-[var(--text-3)]">
            {t('public.signup.hasAccount', 'Sudah punya akun?')}{' '}
            <Link to="/portal" className="text-[var(--accent)] hover:underline">{t('public.signup.loginLink', 'Masuk di sini')}</Link>
          </p>
        </form>

        {/* Plan summary sidebar */}
        <aside>
          {selectedPlan ? (
            <div className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-5">
              <p className="text-xs font-semibold uppercase text-[var(--text-3)]">{t('public.signup.selectedPlan', 'Paket Dipilih')}</p>
              <h3 className="mt-2 text-xl font-bold">{selectedPlan.name}</h3>
              <p className="text-2xl font-bold text-[var(--accent)]">
                {localizedPrice(selectedPlan.price)}
              </p>

              <div className="mt-4 flex flex-wrap gap-1">
                {selectedPlan.active_modules.map((m) => (
                  <span key={m} className="rounded-full border border-[var(--line)] bg-[var(--surface-2)] px-2 py-0.5 text-xs font-medium text-[var(--text-2)]">
                    {moduleLabel(m)}
                  </span>
                ))}
              </div>

              <ul className="mt-4 space-y-2">
                {planFeatures(selectedPlan).slice(0, 5).map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-[var(--text-2)]">
                    <span className="mt-0.5 text-[var(--accent)]">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="rounded-[var(--radius-lg)] border border-dashed border-[var(--line)] p-5 text-center text-sm text-[var(--text-3)]">
              {t('public.signup.selectPlanHint', 'Pilih paket untuk melihat detailnya')}
            </div>
          )}
        </aside>
      </div>
    </main>
  )
}

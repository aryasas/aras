// claude-sonnet-4-6
import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { MODULE_LABELS } from '../lib/planUtils'
import { formatCurrency } from '../lib/formatters'
import { useLanguage } from '../context/LanguageContext'
import { useNotify } from '../aras-core/contexts/NotificationContext'
import { consentApi, type ConsentPolicy } from '../lib/api'

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

interface PaymentMethod {
  code: string
  label: string
  provider_code?: string
  country?: string
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
  marketing_consent: false,
}

// gpt-5.4
export default function CustomerSignup() {
  const { lang, setLang, t } = useLanguage()
  const showNotification = useNotify()
  const [searchParams] = useSearchParams()
  const [plans, setPlans] = useState<Plan[]>([])
  const [form, setForm] = useState({ ...initialForm, plan_key: searchParams.get('plan') || '' })
  const [submitting, setSubmitting] = useState(false)
  const [successEmail, setSuccessEmail] = useState('')
  const [successId, setSuccessId] = useState<number | string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [plansLoading, setPlansLoading] = useState(true)
  const [plansError, setPlansError] = useState<string | null>(null)
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([])
  const [consentPolicy, setConsentPolicy] = useState<ConsentPolicy | null>(null)
  const [consentLoading, setConsentLoading] = useState(true)
  const [consentError, setConsentError] = useState<string | null>(null)
  const moduleLabel = (module: string) => t(`public.modules.${module}`, MODULE_LABELS[module] ?? module)
  const localizedPrice = (price: number, currency?: string) => {
    if (price === 0) return t('public.pricing.free', 'Gratis')
    return `${formatCurrency(price, currency)}${t('public.pricing.perMonth', '/month')}`
  }
  const planFeatures = (plan: Plan) => {
    if (lang === 'en' && EN_PLAN_FEATURES[plan.plan_key]) return EN_PLAN_FEATURES[plan.plan_key]
    return plan.features?.included ?? []
  }
  const consentText = consentPolicy ? consentPolicy.text[lang] || consentPolicy.text.en || consentPolicy.text.id : ''

  const loadPlans = useCallback(async () => {
    setPlansLoading(true)
    setPlansError(null)
    try {
      const res = await fetch('/api/v1/saas/plans/public')
      if (!res.ok) throw new Error('plan-load-failed')
      const data = await res.json()
      const payload = data?.data && typeof data.data === 'object' ? data.data : data
      setPlans(Array.isArray(payload) ? payload.filter((p: Plan) => PUBLIC_PLAN_KEYS.has(p.plan_key)) : [])
    } catch (err) {
      setPlans([])
      setPlansError(t('public.signup.planLoadFailed', 'Tidak dapat memuat paket. Silakan coba lagi.'))
      showNotification('Failed to load plan details', 'error')
      console.error(err)
    } finally {
      setPlansLoading(false)
    }
  }, [showNotification, t])

  useEffect(() => {
    loadPlans()
  }, [loadPlans])

  useEffect(() => {
    let cancelled = false

    consentApi
      .getPolicy()
      .then((policy) => {
        if (cancelled) return
        setConsentPolicy(policy)
        setConsentError(null)
      })
      .catch((err) => {
        if (cancelled) return
        setConsentPolicy(null)
        setConsentError(t('consent.loadFailed', 'Consent policy unavailable right now.'))
        console.error(err)
      })
      .finally(() => {
        if (!cancelled) {
          setConsentLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [t])

  useEffect(() => {
    fetch('/api/v1/saas/payments/methods')
      .then((res) => res.ok ? res.json() : [])
      .then((data) => {
        const payload = data?.data && typeof data.data === 'object' ? data.data : data
        setPaymentMethods(Array.isArray(payload) ? payload : [])
      })
      .catch((err) => {
        setPaymentMethods([])
        showNotification('Payment methods unavailable', 'warning')
        console.error(err)
      })
  }, [showNotification])

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
        marketing_consent: form.marketing_consent,
        consent_version: form.marketing_consent ? consentPolicy?.version : undefined,
      }
      const res = await fetch('/api/v1/saas/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json().catch(() => ({}))
      if (res.status === 409) { setError(t('public.signup.duplicateEmail', 'Email ini sudah terdaftar.')); showNotification(data.detail || 'Signup failed', 'error'); return }
      if (!res.ok) { setError(t('public.signup.failed', 'Pendaftaran gagal. Silakan coba lagi.')); showNotification(data.detail || 'Signup failed', 'error'); return }
      const d = data?.data && typeof data.data === 'object' ? data.data : data
      const subscriptionId = d.subscription_id ?? d.id ?? d.signup_id
      if (subscriptionId) sessionStorage.setItem('portal_subscription_id', String(subscriptionId))
      if (subscriptionId && selectedPlan && selectedPlan.price > 0) {
        const checkoutRes = await fetch('/api/v1/saas/payments/checkout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            subscription_id: subscriptionId,
            return_url: `${window.location.origin}/portal/setup?status=pending&subscription_id=${subscriptionId}`,
          }),
        })
        const checkoutData = await checkoutRes.json().catch(() => ({}))
        if (!checkoutRes.ok) {
          setError(t('public.signup.checkoutFailed', 'Pendaftaran tersimpan, tetapi checkout pembayaran gagal dimulai.'))
          showNotification(checkoutData.detail || 'Signup failed', 'error')
          return
        }
        const checkoutPayload = checkoutData?.data && typeof checkoutData.data === 'object' ? checkoutData.data : checkoutData
        if (checkoutPayload.checkout_url) {
          window.location.href = checkoutPayload.checkout_url
          return
        }
      }
      setSuccessEmail(form.email)
      setSuccessId(d.subscription_id ?? d.signup_id ?? null)
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
                  {p.name} — {localizedPrice(p.price, p.currency)}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="rounded-[var(--radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
              {error}
            </div>
          )}

          {plansError && (
            <div className="flex items-center justify-between gap-3 rounded-[var(--radius)] border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
              <span>{plansError}</span>
              <button
                type="button"
                onClick={loadPlans}
                className="shrink-0 rounded-[var(--radius)] border border-amber-300 px-3 py-1 text-xs font-semibold hover:bg-amber-100"
              >
                {t('public.retry', 'Coba lagi')}
              </button>
            </div>
          )}

          <label className="flex items-start gap-3 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text-2)]">
            <input
              type="checkbox"
              checked={form.marketing_consent}
              onChange={(e) => setForm({ ...form, marketing_consent: e.target.checked })}
              disabled={consentLoading || !consentPolicy}
              className="mt-0.5 h-4 w-4 rounded border-[var(--line)] text-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
            />
            <span className="space-y-2">
              <span className="block font-medium text-[var(--text)]">
                {t('consent.marketingOptIn', 'I agree to receive product updates and marketing emails')}
              </span>
              <span className="block text-xs text-[var(--text-3)]">
                {consentPolicy
                  ? `${t('consent.versionLabel', 'Consent version')}: ${consentPolicy.version}`
                  : consentLoading
                    ? t('consent.loading', 'Loading consent policy...')
                    : consentError || t('consent.unavailable', 'Consent policy is unavailable.')}
              </span>
              {consentText ? <span className="block whitespace-pre-wrap text-xs leading-5 text-[var(--text-2)]">{consentText}</span> : null}
            </span>
          </label>

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
                {localizedPrice(selectedPlan.price, selectedPlan.currency)}
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

              {paymentMethods.length > 0 && (
                <div className="mt-5 border-t border-[var(--line)] pt-4">
                  <p className="text-xs font-semibold uppercase text-[var(--text-3)]">{t('public.signup.paymentMethods', 'Metode Pembayaran')}</p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {paymentMethods.slice(0, 8).map((method) => (
                      <span key={`${method.provider_code || 'provider'}-${method.code}`} className="rounded-full border border-[var(--line)] bg-[var(--surface-2)] px-2 py-0.5 text-xs font-medium text-[var(--text-2)]">
                        {method.label || method.code}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="rounded-[var(--radius-lg)] border border-dashed border-[var(--line)] p-5 text-center text-sm text-[var(--text-3)]">
              {plansLoading ? t('public.pricing.loading', 'Memuat paket...') : t('public.signup.selectPlanHint', 'Pilih paket untuk melihat detailnya')}
            </div>
          )}
        </aside>
      </div>
    </main>
  )
}

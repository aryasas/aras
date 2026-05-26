// claude-sonnet-4-6
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { MODULE_LABELS } from '../lib/planUtils'
import { useLanguage } from '../context/LanguageContext'

interface Plan {
  id: number
  plan_key: string
  name: string
  price: number
  currency: string
  max_users: number
  max_branches: number
  max_transactions: number
  max_products: number
  api_access: boolean
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

export default function PublicLanding() {
  const { lang, setLang, t } = useLanguage()
  const [plans, setPlans] = useState<Plan[]>([])
  const [plansLoading, setPlansLoading] = useState(true)
  const moduleLabel = (module: string) => t(`public.modules.${module}`, MODULE_LABELS[module] ?? module)
  const formatLandingPrice = (price: number) => {
    if (price === 0) return t('public.pricing.free', 'Gratis')
    return `Rp ${price.toLocaleString('id-ID')}`
  }
  const planFeatures = (plan: Plan) => {
    if (lang === 'en' && EN_PLAN_FEATURES[plan.plan_key]) return EN_PLAN_FEATURES[plan.plan_key]
    return plan.features?.included ?? []
  }

  const features = [
    {
      icon: '🛒',
      title: t('public.features.pos.title', 'POS Mudah'),
      desc: t('public.features.pos.desc', 'Kasir digital yang cepat dan ringan.'),
    },
    {
      icon: '📦',
      title: t('public.features.stock.title', 'Stok Otomatis'),
      desc: t('public.features.stock.desc', 'Stok terpotong otomatis setiap transaksi.'),
    },
    {
      icon: '📊',
      title: t('public.features.report.title', 'Laporan Keuangan'),
      desc: t('public.features.report.desc', 'Laba rugi, neraca, dan arus kas tersaji rapi.'),
    },
  ]

  const testimonials = [
    {
      quote: t('public.testimonials.one.quote', 'Sebelumnya saya catat stok di buku.'),
      name: t('public.testimonials.one.name', 'Siti Rahayu'),
      role: t('public.testimonials.one.role', 'Pemilik Toko Sembako, Surabaya'),
    },
    {
      quote: t('public.testimonials.two.quote', 'Mudah dipakai karyawan baru.'),
      name: t('public.testimonials.two.name', 'Budi Santoso'),
      role: t('public.testimonials.two.role', 'Pemilik Warung Makan, Bandung'),
    },
  ]

  const loadPlans = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/saas/plans/public')
      if (res.ok) {
        const data = await res.json()
        setPlans(Array.isArray(data) ? data.filter((p: Plan) => PUBLIC_PLAN_KEYS.has(p.plan_key)) : [])
      }
    } catch {
      // show empty pricing gracefully
    } finally {
      setPlansLoading(false)
    }
  }, [])

  useEffect(() => { loadPlans() }, [loadPlans])

  return (
    <main className="min-h-screen bg-[var(--bg)] text-[var(--text)]">

      {/* Nav */}
      <nav className="sticky top-0 z-10 border-b border-[var(--line)] bg-[var(--bg)]/90 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="text-lg font-bold tracking-tight">ARAS</span>
          <div className="flex items-center gap-6">
            <a href="#pricing" className="hidden text-sm text-[var(--text-2)] hover:text-[var(--text)] sm:block">{t('public.nav.pricing', 'Harga')}</a>
            <button
              type="button"
              onClick={() => setLang(lang === 'id' ? 'en' : 'id')}
              className="rounded-[var(--radius)] border border-[var(--line)] px-2.5 py-1 text-xs font-semibold text-[var(--text-2)] hover:text-[var(--text)]"
            >
              {lang === 'id' ? 'EN' : 'ID'}
            </button>
            <Link to="/portal" className="text-sm text-[var(--text-2)] hover:text-[var(--text)]">{t('public.nav.login', 'Masuk')}</Link>
            <Link
              to="/signup"
              className="rounded-[var(--radius)] bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--aras-accent-strong)]"
            >
              {t('public.nav.tryFree', 'Coba Gratis')}
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 py-20 md:py-32">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-4 inline-flex items-center rounded-full border border-[var(--line)] bg-[var(--surface)] px-3 py-1 text-xs font-medium text-[var(--text-2)]">
            {t('public.hero.badge', 'Platform manajemen bisnis untuk UMKM Indonesia')}
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-[var(--text)] md:text-6xl">
            {t('public.hero.titleTop', 'Kelola bisnis lebih mudah,')}<br />
            <span className="text-[var(--accent)]">{t('public.hero.titleAccent', 'mulai dari Rp 0')}</span>
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-[var(--text-2)]">
            {t('public.hero.description', 'POS, stok, hutang piutang, dan laporan keuangan dalam satu platform.')}
          </p>
          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Link
              to="/signup"
              className="w-full rounded-[var(--radius)] bg-[var(--accent)] px-6 py-3 text-sm font-semibold text-white hover:bg-[var(--aras-accent-strong)] sm:w-auto"
            >
              {t('public.hero.primary', 'Coba Gratis Sekarang')}
            </Link>
            <a
              href="#pricing"
              className="w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-6 py-3 text-sm font-semibold text-[var(--text)] hover:bg-[var(--surface-2)] sm:w-auto"
            >
              {t('public.hero.secondary', 'Lihat Harga')}
            </a>
          </div>
        </div>
      </section>

      {/* Fitur */}
      <section className="border-y border-[var(--line)] bg-[var(--surface)]">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <div className="text-center">
            <h2 className="text-2xl font-bold md:text-3xl">{t('public.features.title', 'Semua yang Anda butuhkan')}</h2>
            <p className="mt-2 text-sm text-[var(--text-3)]">{t('public.features.subtitle', 'Dari kasir sampai laporan keuangan, semua tersedia di ARAS.')}</p>
          </div>
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {features.map((f) => (
              <div key={f.title} className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--bg)] p-6">
                <div className="text-3xl">{f.icon}</div>
                <h3 className="mt-4 font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--text-2)]">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="mx-auto max-w-6xl px-6 py-16">
        <div className="text-center">
          <h2 className="text-2xl font-bold md:text-3xl">{t('public.pricing.title', 'Harga yang jujur')}</h2>
          <p className="mt-2 text-sm text-[var(--text-3)]">{t('public.pricing.subtitle', 'Mulai gratis, upgrade kapan saja. Tidak ada biaya tersembunyi.')}</p>
        </div>

        {plansLoading ? (
          <div className="mt-10 text-center text-sm text-[var(--text-3)]">{t('public.pricing.loading', 'Memuat paket...')}</div>
        ) : (
          <div className="mt-10 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
            {plans.map((plan) => {
              const isPopular = plan.plan_key === 'growth'
              return (
                <div
                  key={plan.id}
                  className={`relative flex flex-col rounded-[var(--radius-lg)] border p-6 ${
                    isPopular
                      ? 'border-[var(--accent)] bg-[var(--surface)] shadow-md'
                      : 'border-[var(--line)] bg-[var(--surface)]'
                  }`}
                >
                  {isPopular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[var(--accent)] px-3 py-0.5 text-xs font-bold text-white">
                      {t('public.pricing.popular', 'Paling Populer')}
                    </div>
                  )}

                  <div>
                    <h3 className="font-bold text-[var(--text)]">{plan.name}</h3>
                    <div className="mt-3">
                      <span className="text-3xl font-bold">{formatLandingPrice(plan.price)}</span>
                      {plan.price > 0 && <span className="text-sm text-[var(--text-3)]">{t('public.pricing.perMonth', '/bulan')}</span>}
                    </div>

                    {/* Modul badges */}
                    <div className="mt-4 flex flex-wrap gap-1">
                      {plan.active_modules.map((m) => (
                        <span key={m} className="rounded-full bg-[var(--surface-2)] border border-[var(--line)] px-2 py-0.5 text-xs font-medium text-[var(--text-2)]">
                          {moduleLabel(m)}
                        </span>
                      ))}
                    </div>

                    <ul className="mt-5 space-y-2">
                      {planFeatures(plan).map((item) => (
                        <li key={item} className="flex items-start gap-2 text-sm text-[var(--text-2)]">
                          <span className="mt-0.5 text-[var(--accent)]">✓</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <Link
                    to={`/signup?plan=${plan.plan_key}`}
                    className={`mt-6 block rounded-[var(--radius)] px-4 py-2.5 text-center text-sm font-semibold transition-colors ${
                      isPopular
                        ? 'bg-[var(--accent)] text-white hover:bg-[var(--aras-accent-strong)]'
                        : 'border border-[var(--line)] bg-[var(--bg)] text-[var(--text)] hover:bg-[var(--surface-2)]'
                    }`}
                  >
                    {plan.price === 0 ? t('public.pricing.startFree', 'Mulai Gratis') : t('public.pricing.startNow', 'Mulai Sekarang')}
                  </Link>
                </div>
              )
            })}
          </div>
        )}

        <p className="mt-6 text-center text-xs text-[var(--text-3)]">
          {t('public.pricing.enterprisePrompt', 'Butuh lebih dari ini?')}{' '}
          <Link to="/contact" className="text-[var(--accent)] hover:underline">{t('public.pricing.enterpriseLink', 'Hubungi kami')}</Link>{' '}
          {t('public.pricing.enterpriseSuffix', 'untuk paket Enterprise dengan dedicated server dan SLA.')}
        </p>
      </section>

      {/* Testimonials */}
      <section className="border-y border-[var(--line)] bg-[var(--surface)]">
        <div className="mx-auto max-w-4xl px-6 py-16">
          <h2 className="text-center text-2xl font-bold">{t('public.testimonials.title', 'Dipercaya pemilik usaha')}</h2>
          <div className="mt-10 grid gap-5 md:grid-cols-2">
            {testimonials.map((item) => (
              <figure key={item.name} className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--bg)] p-6">
                <blockquote className="text-sm leading-relaxed text-[var(--text-2)]">"{item.quote}"</blockquote>
                <figcaption className="mt-4">
                  <p className="text-sm font-semibold text-[var(--text)]">{item.name}</p>
                  <p className="text-xs text-[var(--text-3)]">{item.role}</p>
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      {/* CTA bottom */}
      <section className="mx-auto max-w-3xl px-6 py-20 text-center">
        <h2 className="text-3xl font-bold">{t('public.cta.title', 'Mulai sekarang, gratis')}</h2>
        <p className="mt-3 text-sm text-[var(--text-3)]">{t('public.cta.subtitle', 'Tidak perlu kartu kredit. Setup kurang dari 5 menit.')}</p>
        <Link
          to="/signup"
          className="mt-8 inline-flex rounded-[var(--radius)] bg-[var(--accent)] px-7 py-3 text-sm font-semibold text-white hover:bg-[var(--aras-accent-strong)]"
        >
          {t('public.cta.button', 'Daftar Sekarang')}
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--line)]">
        <div className="mx-auto max-w-6xl px-6 py-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <span className="font-bold">ARAS</span>
            <nav className="flex gap-5 text-sm text-[var(--text-3)]">
              <Link to="/welcome" className="hover:text-[var(--text)]">{t('public.nav.home', 'Beranda')}</Link>
              <a href="#pricing" className="hover:text-[var(--text)]">{t('public.nav.pricing', 'Harga')}</a>
              <Link to="/signup" className="hover:text-[var(--text)]">{t('public.nav.signup', 'Daftar')}</Link>
              <Link to="/portal" className="hover:text-[var(--text)]">{t('public.nav.login', 'Masuk')}</Link>
              <Link to="/contact" className="hover:text-[var(--text)]">{t('public.nav.contact', 'Kontak')}</Link>
            </nav>
            <p className="text-xs text-[var(--text-3)]">© {new Date().getFullYear()} ARAS</p>
          </div>
        </div>
      </footer>
    </main>
  )
}

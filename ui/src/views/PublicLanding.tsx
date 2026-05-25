// claude-sonnet-4-6
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { MODULE_LABELS } from '../lib/planUtils'

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
  features?: { included?: string[] } | null
}

const FEATURES = [
  {
    icon: '🛒',
    title: 'POS Mudah',
    desc: 'Kasir digital yang cepat dan ringan. Bisa dipakai dari HP, tablet, atau laptop tanpa pelatihan khusus.',
  },
  {
    icon: '📦',
    title: 'Stok Otomatis',
    desc: 'Stok terpotong otomatis setiap transaksi. Tidak perlu input manual — pantau stok real-time kapan saja.',
  },
  {
    icon: '📊',
    title: 'Laporan Keuangan',
    desc: 'Laba rugi, neraca, dan arus kas tersaji rapi. Ambil keputusan bisnis berdasarkan data, bukan perkiraan.',
  },
]

const TESTIMONIALS = [
  {
    quote: 'Sebelumnya saya catat stok di buku. Sekarang semua sudah otomatis, dan laporan bulanan tinggal download.',
    name: 'Siti Rahayu',
    role: 'Pemilik Toko Sembako, Surabaya',
  },
  {
    quote: 'Mudah dipakai karyawan baru. Dalam 30 menit sudah bisa transaksi sendiri.',
    name: 'Budi Santoso',
    role: 'Pemilik Warung Makan, Bandung',
  },
]

export default function PublicLanding() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [plansLoading, setPlansLoading] = useState(true)

  const loadPlans = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/saas/plans/public')
      if (res.ok) {
        const data = await res.json()
        setPlans(Array.isArray(data) ? data.filter((p: Plan) => p.plan_key !== 'enterprise') : [])
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
            <a href="#pricing" className="hidden text-sm text-[var(--text-2)] hover:text-[var(--text)] sm:block">Harga</a>
            <Link to="/portal" className="text-sm text-[var(--text-2)] hover:text-[var(--text)]">Masuk</Link>
            <Link
              to="/signup"
              className="rounded-[var(--radius)] bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--aras-accent-strong)]"
            >
              Coba Gratis
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 py-20 md:py-32">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-4 inline-flex items-center rounded-full border border-[var(--line)] bg-[var(--surface)] px-3 py-1 text-xs font-medium text-[var(--text-2)]">
            Platform manajemen bisnis untuk UMKM Indonesia
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-[var(--text)] md:text-6xl">
            Kelola bisnis lebih mudah,<br />
            <span className="text-[var(--accent)]">mulai dari Rp 0</span>
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-[var(--text-2)]">
            POS, stok, hutang piutang, dan laporan keuangan dalam satu platform. Tidak perlu keahlian akuntansi.
          </p>
          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Link
              to="/signup"
              className="w-full rounded-[var(--radius)] bg-[var(--accent)] px-6 py-3 text-sm font-semibold text-white hover:bg-[var(--aras-accent-strong)] sm:w-auto"
            >
              Coba Gratis Sekarang
            </Link>
            <a
              href="#pricing"
              className="w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-6 py-3 text-sm font-semibold text-[var(--text)] hover:bg-[var(--surface-2)] sm:w-auto"
            >
              Lihat Harga
            </a>
          </div>
        </div>
      </section>

      {/* Fitur */}
      <section className="border-y border-[var(--line)] bg-[var(--surface)]">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <div className="text-center">
            <h2 className="text-2xl font-bold md:text-3xl">Semua yang Anda butuhkan</h2>
            <p className="mt-2 text-sm text-[var(--text-3)]">Dari kasir sampai laporan keuangan, semua tersedia di ARAS.</p>
          </div>
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {FEATURES.map((f) => (
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
          <h2 className="text-2xl font-bold md:text-3xl">Harga yang jujur</h2>
          <p className="mt-2 text-sm text-[var(--text-3)]">Mulai gratis, upgrade kapan saja. Tidak ada biaya tersembunyi.</p>
        </div>

        {plansLoading ? (
          <div className="mt-10 text-center text-sm text-[var(--text-3)]">Memuat paket...</div>
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
                      Paling Populer
                    </div>
                  )}

                  <div>
                    <h3 className="font-bold text-[var(--text)]">{plan.name}</h3>
                    <div className="mt-3">
                      <span className="text-3xl font-bold">{plan.price === 0 ? 'Gratis' : `Rp ${plan.price.toLocaleString('id-ID')}`}</span>
                      {plan.price > 0 && <span className="text-sm text-[var(--text-3)]">/bulan</span>}
                    </div>

                    {/* Modul badges */}
                    <div className="mt-4 flex flex-wrap gap-1">
                      {plan.active_modules.map((m) => (
                        <span key={m} className="rounded-full bg-[var(--surface-2)] border border-[var(--line)] px-2 py-0.5 text-xs font-medium text-[var(--text-2)]">
                          {MODULE_LABELS[m] ?? m}
                        </span>
                      ))}
                    </div>

                    <ul className="mt-5 space-y-2">
                      {(plan.features?.included ?? []).map((item) => (
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
                    {plan.price === 0 ? 'Mulai Gratis' : 'Mulai Sekarang'}
                  </Link>
                </div>
              )
            })}
          </div>
        )}

        <p className="mt-6 text-center text-xs text-[var(--text-3)]">
          Butuh lebih dari ini?{' '}
          <Link to="/contact" className="text-[var(--accent)] hover:underline">Hubungi kami</Link>{' '}
          untuk paket Enterprise dengan dedicated server dan SLA.
        </p>
      </section>

      {/* Testimonials */}
      <section className="border-y border-[var(--line)] bg-[var(--surface)]">
        <div className="mx-auto max-w-4xl px-6 py-16">
          <h2 className="text-center text-2xl font-bold">Dipercaya pemilik usaha</h2>
          <div className="mt-10 grid gap-5 md:grid-cols-2">
            {TESTIMONIALS.map((t) => (
              <figure key={t.name} className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--bg)] p-6">
                <blockquote className="text-sm leading-relaxed text-[var(--text-2)]">"{t.quote}"</blockquote>
                <figcaption className="mt-4">
                  <p className="text-sm font-semibold text-[var(--text)]">{t.name}</p>
                  <p className="text-xs text-[var(--text-3)]">{t.role}</p>
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      {/* CTA bottom */}
      <section className="mx-auto max-w-3xl px-6 py-20 text-center">
        <h2 className="text-3xl font-bold">Mulai sekarang, gratis</h2>
        <p className="mt-3 text-sm text-[var(--text-3)]">Tidak perlu kartu kredit. Setup kurang dari 5 menit.</p>
        <Link
          to="/signup"
          className="mt-8 inline-flex rounded-[var(--radius)] bg-[var(--accent)] px-7 py-3 text-sm font-semibold text-white hover:bg-[var(--aras-accent-strong)]"
        >
          Daftar Sekarang
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--line)]">
        <div className="mx-auto max-w-6xl px-6 py-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <span className="font-bold">ARAS</span>
            <nav className="flex gap-5 text-sm text-[var(--text-3)]">
              <Link to="/welcome" className="hover:text-[var(--text)]">Beranda</Link>
              <a href="#pricing" className="hover:text-[var(--text)]">Harga</a>
              <Link to="/signup" className="hover:text-[var(--text)]">Daftar</Link>
              <Link to="/portal" className="hover:text-[var(--text)]">Masuk</Link>
              <Link to="/contact" className="hover:text-[var(--text)]">Kontak</Link>
            </nav>
            <p className="text-xs text-[var(--text-3)]">© {new Date().getFullYear()} ARAS</p>
          </div>
        </div>
      </footer>
    </main>
  )
}

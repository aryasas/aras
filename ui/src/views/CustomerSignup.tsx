// claude-sonnet-4-6
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { MODULE_LABELS, formatPrice } from '../lib/planUtils'

interface Plan {
  id: number
  plan_key: string
  name: string
  price: number
  currency: string
  max_users: number
  max_branches: number
  active_modules: string[]
  features?: { included?: string[] } | null
}

const initialForm = {
  email: '',
  company_name: '',
  full_name: '',
  phone: '',
  plan_key: '',
}

export default function CustomerSignup() {
  const [searchParams] = useSearchParams()
  const [plans, setPlans] = useState<Plan[]>([])
  const [form, setForm] = useState({ ...initialForm, plan_key: searchParams.get('plan') || '' })
  const [submitting, setSubmitting] = useState(false)
  const [successEmail, setSuccessEmail] = useState('')
  const [successId, setSuccessId] = useState<number | string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/v1/saas/plans/public')
      .then((r) => r.ok ? r.json() : [])
      .then((data) => setPlans(Array.isArray(data) ? data.filter((p: Plan) => p.plan_key !== 'enterprise') : []))
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
      if (res.status === 409) { setError('Email ini sudah terdaftar.'); return }
      if (!res.ok) { setError('Pendaftaran gagal. Silakan coba lagi.'); return }
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
          <h1 className="mt-4 text-xl font-bold">Pendaftaran diterima!</h1>
          <p className="mt-3 text-sm leading-relaxed text-[var(--text-2)]">
            Tim kami akan menghubungi Anda di <strong>{successEmail}</strong> dalam 1×24 jam untuk proses aktivasi.
          </p>
          {successId && <p className="mt-3 text-xs text-[var(--text-3)]">Nomor referensi: #{successId}</p>}
          <Link to="/welcome" className="mt-6 inline-flex rounded-[var(--radius)] bg-[var(--accent)] px-5 py-2.5 text-sm font-semibold text-white">
            Kembali ke Beranda
          </Link>
        </div>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <div className="mb-8">
        <Link to="/welcome" className="text-sm text-[var(--text-3)] hover:text-[var(--text)]">← Kembali</Link>
        <h1 className="mt-4 text-3xl font-bold">Daftar ARAS</h1>
        <p className="mt-1 text-sm text-[var(--text-2)]">Mulai gratis, tanpa kartu kredit.</p>
      </div>

      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-semibold" htmlFor="full_name">Nama Lengkap</label>
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
              <label className="block text-sm font-semibold" htmlFor="email">Email</label>
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
              <label className="block text-sm font-semibold" htmlFor="company_name">Nama Usaha</label>
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
              <label className="block text-sm font-semibold" htmlFor="phone">Nomor HP</label>
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
            <label className="block text-sm font-semibold" htmlFor="plan_key">Pilih Paket</label>
            <select
              id="plan_key"
              value={form.plan_key}
              onChange={(e) => setForm({ ...form, plan_key: e.target.value })}
              className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-4 py-2.5 text-sm outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
            >
              <option value="">-- Pilih paket --</option>
              {plans.map((p) => (
                <option key={p.id} value={p.plan_key}>
                  {p.name} — {formatPrice(p.price)}
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
            {submitting ? 'Mengirim...' : 'Daftar Sekarang'}
          </button>

          <p className="text-center text-xs text-[var(--text-3)]">
            Sudah punya akun?{' '}
            <Link to="/portal" className="text-[var(--accent)] hover:underline">Masuk di sini</Link>
          </p>
        </form>

        {/* Plan summary sidebar */}
        <aside>
          {selectedPlan ? (
            <div className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-5">
              <p className="text-xs font-semibold uppercase text-[var(--text-3)]">Paket Dipilih</p>
              <h3 className="mt-2 text-xl font-bold">{selectedPlan.name}</h3>
              <p className="text-2xl font-bold text-[var(--accent)]">
                {formatPrice(selectedPlan.price)}
              </p>

              <div className="mt-4 flex flex-wrap gap-1">
                {selectedPlan.active_modules.map((m) => (
                  <span key={m} className="rounded-full border border-[var(--line)] bg-[var(--surface-2)] px-2 py-0.5 text-xs font-medium text-[var(--text-2)]">
                    {MODULE_LABELS[m] ?? m}
                  </span>
                ))}
              </div>

              <ul className="mt-4 space-y-2">
                {(selectedPlan.features?.included ?? []).slice(0, 5).map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-[var(--text-2)]">
                    <span className="mt-0.5 text-[var(--accent)]">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="rounded-[var(--radius-lg)] border border-dashed border-[var(--line)] p-5 text-center text-sm text-[var(--text-3)]">
              Pilih paket untuk melihat detailnya
            </div>
          )}
        </aside>
      </div>
    </main>
  )
}

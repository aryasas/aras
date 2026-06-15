import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, CheckCircle2, Mail, MessageSquareText } from 'lucide-react'
import api from '../lib/api'

const initialForm = {
  name: '',
  email: '',
  subject: '',
  message: '',
}

export default function ContactView() {
  const [form, setForm] = useState(initialForm)
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    setSuccess(false)

    try {
      await api.post('/web/contact', form)
      setForm(initialForm)
      setSuccess(true)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Could not send your message.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="arc arc-bg min-h-screen">
      <section className="mx-auto max-w-5xl px-6 py-14">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div>
            <Link to="/welcome" className="inline-flex items-center gap-2 text-sm text-[var(--text-3)] hover:text-[var(--accent)]">
              <ArrowLeft size={15} />
              Back to home
            </Link>
            <p className="arc-id mt-6"><b>arc</b>/public/<b>contact</b></p>
            <h1 className="mt-2 text-4xl font-semibold tracking-tight text-[var(--text)]">Talk to us</h1>
            <p className="mt-3 max-w-2xl text-base leading-7 text-[var(--text-2)]">
              Reach out for enterprise plans, onboarding questions, custom implementation work, or anything you want to clarify before getting started.
            </p>
          </div>

          <aside className="arc-card h-fit bg-[var(--surface)] p-5">
            <div className="flex items-center gap-3">
              <div
                className="flex h-11 w-11 items-center justify-center rounded-[var(--radius)] text-[var(--accent)]"
                style={{ background: 'color-mix(in oklch, var(--accent) 14%, var(--surface))' }}
              >
                <MessageSquareText size={20} />
              </div>
              <div>
                <p className="text-sm font-semibold text-[var(--text)]">Need a direct response?</p>
                <p className="text-sm text-[var(--text-2)]">Share your company details and what you&apos;re evaluating.</p>
              </div>
            </div>
            <div className="mt-5 space-y-3 text-sm text-[var(--text-2)]">
              <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-3">
                Typical reply window: within 1 business day.
              </div>
              <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-3 py-3">
                Best for: enterprise pricing, implementation, custom deployment, onboarding.
              </div>
            </div>
          </aside>
        </div>

        <form onSubmit={handleSubmit} className="mt-10 max-w-3xl space-y-5">
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="name">Name</label>
              <input
                id="name"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                required
                className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-4 py-2.5 text-sm outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
                placeholder="Your name"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="email">Email</label>
              <div className="relative mt-2">
                <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
                <input
                  id="email"
                  type="email"
                  value={form.email}
                  onChange={(event) => setForm({ ...form, email: event.target.value })}
                  required
                  className="w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] py-2.5 pr-4 pl-9 text-sm outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
                  placeholder="name@company.com"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="subject">Subject</label>
            <input
              id="subject"
              value={form.subject}
              onChange={(event) => setForm({ ...form, subject: event.target.value })}
              className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-4 py-2.5 text-sm outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
              placeholder="What would you like to discuss?"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="message">Message</label>
            <textarea
              id="message"
              value={form.message}
              onChange={(event) => setForm({ ...form, message: event.target.value })}
              required
              rows={7}
              className="mt-2 w-full resize-y rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-4 py-3 text-sm outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
              placeholder="Tell us about your use case, company size, or anything you want help with."
            />
          </div>

          {success && (
            <div className="flex items-center gap-2 rounded-[var(--radius)] border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
              <CheckCircle2 size={16} />
              <span>Thanks. Your message has been sent and our team will follow up soon.</span>
            </div>
          )}

          {error && (
            <div
              className="rounded-[var(--radius)] border px-4 py-3 text-sm font-medium"
              style={{
                background: 'color-mix(in oklch, var(--danger) 8%, var(--surface))',
                borderColor: 'color-mix(in oklch, var(--danger) 25%, var(--line))',
                color: 'var(--danger)',
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="arc-btn primary"
            style={{ height: 44 }}
          >
            {submitting ? 'Sending message…' : 'Send message'}
          </button>
        </form>
      </section>
    </main>
  )
}

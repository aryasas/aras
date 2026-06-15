import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { Mail, ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react'
import { ArasLogo } from '../components/ArasLogo'

const ForgotPassword = () => {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await api.post('/auth/forgot-password', { email })
      setSubmitted(true)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <main className="arc arc-bg arc-dotgrid min-h-screen px-4 py-10">
        <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-md items-center">
          <section className="arc-card w-full overflow-hidden bg-[var(--surface)] shadow-[var(--shadow-card-lift)]">
            <div className="px-8 py-8 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[var(--radius-lg)] bg-emerald-50 text-emerald-600">
                <CheckCircle size={30} />
              </div>
              <p className="arc-id mt-5"><b>arc</b>/auth/<b>forgot-password</b></p>
              <h2 className="mt-2 text-[28px] font-semibold tracking-tight text-[var(--text)]">Check your email</h2>
              <p className="mt-3 text-sm leading-6 text-[var(--text-2)]">
                If an account exists for {email}, we&apos;ve sent a reset link with the next steps.
              </p>
            </div>
            <div className="border-t border-[var(--line)] px-8 py-6">
              <Link
                to="/login"
                className="arc-btn primary flex w-full items-center justify-center"
                style={{ height: 44 }}
              >
                <ArrowLeft size={16} />
                Back to login
              </Link>
            </div>
          </section>
        </div>
      </main>
    )
  }

  return (
    <main className="arc arc-bg arc-dotgrid min-h-screen px-4 py-10">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-md items-center">
        <section className="arc-card w-full overflow-hidden bg-[var(--surface)] shadow-[var(--shadow-card-lift)]">
          <div className="px-8 pt-8 pb-2 flex items-start gap-4">
            <ArasLogo size="lg" />
            <div className="flex-1 min-w-0">
              <div className="arc-id"><b>arc</b>/auth/<b>forgot-password</b></div>
              <h1 className="mt-1 text-[26px] font-semibold tracking-tight text-[var(--text)]">Forgot your password?</h1>
              <p className="mt-1 text-sm leading-6 text-[var(--text-2)]">
                Enter your workspace email and we&apos;ll send you a secure reset link.
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="px-8 py-6 flex flex-col gap-5">
            {error && (
              <div
                className="flex items-center gap-2 rounded-[var(--radius)] border px-3 py-2 text-[12.5px]"
                style={{
                  background: 'color-mix(in oklch, var(--danger) 10%, var(--surface))',
                  borderColor: 'color-mix(in oklch, var(--danger) 30%, var(--line))',
                  color: 'var(--danger)',
                }}
              >
                <AlertCircle size={15} />
                <span>{error}</span>
              </div>
            )}

            <label className="flex flex-col gap-1.5">
              <span className="arc-id">email</span>
              <span className="relative">
                <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="arc-input"
                  style={{ paddingLeft: 32 }}
                  placeholder="name@example.com"
                  autoFocus
                />
              </span>
            </label>

            <button
              type="submit"
              disabled={loading}
              className="arc-btn primary w-full justify-center"
              style={{ height: 44 }}
            >
              <Mail size={15} />
              <span>{loading ? 'Sending link…' : 'Send reset link'}</span>
            </button>
          </form>

          <div className="border-t border-[var(--line)] px-8 pb-8 pt-4 text-[11.5px] flex flex-col gap-1.5 text-[var(--text-3)]">
            <Link to="/login" className="inline-flex items-center gap-2 text-[var(--text-3)] hover:text-[var(--accent)]">
              <ArrowLeft size={15} />
              Back to login
            </Link>
          </div>
        </section>
      </div>
    </main>
  )
}

export default ForgotPassword

import React, { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import api from '../lib/api'
import { Lock, CheckCircle, AlertCircle, ArrowLeft } from 'lucide-react'
import { ArasLogo } from '../components/ArasLogo'

const ResetPassword = () => {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!token) {
      setError('Invalid or missing reset token.')
    }
  }, [token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setError('')
    setLoading(true)

    try {
      await api.post('/auth/reset-password', { token, new_password: password })
      setSubmitted(true)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to reset password. The link may be expired.')
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
              <p className="arc-id mt-5"><b>arc</b>/auth/<b>reset-password</b></p>
              <h2 className="mt-2 text-[28px] font-semibold tracking-tight text-[var(--text)]">Password updated</h2>
              <p className="mt-3 text-sm leading-6 text-[var(--text-2)]">
                Your password has been reset successfully. You can now sign in with the new one.
              </p>
            </div>
            <div className="border-t border-[var(--line)] px-8 py-6">
              <Link to="/login" className="arc-btn primary flex w-full items-center justify-center" style={{ height: 44 }}>
                Go to login
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
              <div className="arc-id"><b>arc</b>/auth/<b>reset-password</b></div>
              <h1 className="mt-1 text-[26px] font-semibold tracking-tight text-[var(--text)]">Reset your password</h1>
              <p className="mt-1 text-sm leading-6 text-[var(--text-2)]">Set a new password for your workspace access.</p>
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
              <span className="arc-id">new-pass</span>
              <span className="relative">
                <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="arc-input"
                  style={{ paddingLeft: 32 }}
                  placeholder="At least 8 characters"
                />
              </span>
            </label>

            <label className="flex flex-col gap-1.5">
              <span className="arc-id">confirm-pass</span>
              <span className="relative">
                <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="arc-input"
                  style={{ paddingLeft: 32 }}
                  placeholder="Repeat your password"
                />
              </span>
            </label>

            <button type="submit" disabled={loading || !token} className="arc-btn primary w-full justify-center" style={{ height: 44 }}>
              <span>{loading ? 'Resetting password…' : 'Reset password'}</span>
            </button>
          </form>

          <div className="border-t border-[var(--line)] px-8 pb-8 pt-4 text-[11.5px]">
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

export default ResetPassword

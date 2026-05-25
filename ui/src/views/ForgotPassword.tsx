import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { Mail, ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react'

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
      <div className="min-h-screen bg-[var(--app-panel-soft)] flex items-center justify-center p-4 font-sans">
        <div className="max-w-md w-full bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] shadow-xl p-8 flex flex-col items-center text-center">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-[var(--app-radius-lg)] flex items-center justify-center mb-6">
            <CheckCircle size={32} />
          </div>
          <h2 className="text-2xl font-bold text-[var(--app-text)]">Check your email</h2>
          <p className="text-[var(--app-muted)] mt-4 mb-8">
            If an account exists for {email}, we've sent instructions to reset your password.
          </p>
          <Link 
            to="/login"
            className="w-full py-4 bg-[var(--app-accent)] text-white rounded-[var(--app-radius-lg)] font-bold text-lg shadow-lg hover:bg-indigo-700 transition-all flex items-center justify-center gap-2"
          >
            <ArrowLeft size={20} />
            Back to Login
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[var(--app-panel-soft)] flex items-center justify-center p-4 font-sans">
      <div className="max-w-md w-full bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] shadow-xl shadow-slate-200 border border-[var(--app-border)] overflow-hidden">
        <div className="p-8 pb-0 flex flex-col items-center">
          <div className="w-16 h-16 bg-[var(--app-accent)] rounded-[var(--app-radius-lg)] flex items-center justify-center shadow-lg shadow-indigo-200 mb-6">
            <span className="text-white font-black text-3xl">A</span>
          </div>
          <h1 className="text-2xl font-bold text-[var(--app-text)]">Forgot Password?</h1>
          <p className="text-[var(--app-muted)] mt-2 text-center">Enter your email and we'll send you a link to reset your password.</p>
        </div>

        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-[var(--app-radius)] flex items-center gap-3 text-sm">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-semibold text-[var(--app-text)] ml-1">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--app-muted)]" size={18} />
              <input 
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-[var(--app-panel-soft)] border border-[var(--app-border)] rounded-[var(--app-radius)] focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                placeholder="name@example.com"
              />
            </div>
          </div>

          <button 
            type="submit"
            disabled={loading}
            className={`w-full py-4 bg-[var(--app-accent)] text-white rounded-[var(--app-radius-lg)] font-bold text-lg shadow-lg shadow-indigo-100 hover:bg-indigo-700 transition-all transform hover:-translate-y-1 active:translate-y-0
              ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
          >
            {loading ? 'Sending link...' : 'Send Reset Link'}
          </button>

          <div className="text-center mt-4">
            <Link to="/login" className="text-[var(--app-accent)] font-semibold hover:text-indigo-700 flex items-center justify-center gap-2">
              <ArrowLeft size={16} />
              Back to Login
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ForgotPassword

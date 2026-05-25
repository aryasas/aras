import React, { useState, useEffect } from 'react'
import api from '../lib/api'
import { User, Mail, Shield, Lock, Save, AlertCircle, CheckCircle } from 'lucide-react'
import { useAras } from '../aras-core/hooks/useAras'
import { useUIStore } from '../store/uiStore'

const Profile = () => {
  const [userInfo, setUserInfo] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const setPageTitle = useUIStore((state) => state.setPageTitle)

  useEffect(() => {
    setPageTitle('Your Profile', 'Manage your account details and security settings.', 'PROFILE')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])
  
  // Password change state
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passLoading, setPassLoading] = useState(false)
  const [passError, setPassError] = useState('')
  const [passSuccess, setPassSuccess] = useState('')
  const { notify } = useAras()

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await api.get('/auth/me')
        setUserInfo(res.data)
      } catch (err: any) {
        notify(err.message || 'Failed to fetch user info', 'error')
      } finally {
        setLoading(false)
      }
    }
    fetchUser()
  }, [notify])

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPassError('')
    setPassSuccess('')

    if (newPassword !== confirmPassword) {
      setPassError('New passwords do not match')
      notify('New passwords do not match', 'error')
      return
    }

    setPassLoading(true)
    try {
      await api.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword
      })
      setPassSuccess('Password updated successfully')
      setOldPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err: any) {
      const message = err.response?.data?.message || 'Failed to update password'
      setPassError(message)
      notify(message, 'error')
    } finally {
      setPassLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Profile Info */}
        <div className="md:col-span-1 space-y-6">
          <div className="bg-[var(--app-panel)] p-6 rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-sm">
            <h3 className="text-lg font-bold text-[var(--app-text)] mb-6 flex items-center gap-2">
              <User size={18} className="text-[var(--app-accent)]" />
              Account Details
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-[var(--app-muted)] uppercase tracking-wider">Username</label>
                <p className="text-[var(--app-text)] font-medium">{userInfo?.username}</p>
              </div>
              <div>
                <label className="text-xs font-bold text-[var(--app-muted)] uppercase tracking-wider">Email Address</label>
                <p className="text-[var(--app-text)] font-medium flex items-center gap-2">
                  <Mail size={14} className="text-[var(--app-muted)]" />
                  {userInfo?.email}
                </p>
              </div>
              <div>
                <label className="text-xs font-bold text-[var(--app-muted)] uppercase tracking-wider">Role</label>
                <p className="text-[var(--app-text)] font-medium flex items-center gap-2">
                  <Shield size={14} className="text-[var(--app-muted)]" />
                  {userInfo?.is_admin ? 'Administrator' : 'User'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Change Password Form */}
        <div className="md:col-span-2">
          <div className="bg-[var(--app-panel)] p-8 rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-sm">
            <h3 className="text-lg font-bold text-[var(--app-text)] mb-6 flex items-center gap-2">
              <Lock size={18} className="text-[var(--app-accent)]" />
              Change Password
            </h3>

            {passError && (
              <div className="mb-6 bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-[var(--app-radius)] flex items-center gap-3 text-sm">
                <AlertCircle size={18} />
                <span>{passError}</span>
              </div>
            )}

            {passSuccess && (
              <div className="mb-6 bg-emerald-50 border border-emerald-100 text-emerald-600 px-4 py-3 rounded-[var(--app-radius)] flex items-center gap-3 text-sm">
                <CheckCircle size={18} />
                <span>{passSuccess}</span>
              </div>
            )}

            <form onSubmit={handleChangePassword} className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-[var(--app-text)] ml-1">Current Password</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--app-muted)]" size={18} />
                  <input 
                    type="password"
                    required
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 bg-[var(--app-panel-soft)] border border-[var(--app-border)] rounded-[var(--app-radius)] focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-[var(--app-text)] ml-1">New Password</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--app-muted)]" size={18} />
                    <input 
                      type="password"
                      required
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full pl-12 pr-4 py-3 bg-[var(--app-panel-soft)] border border-[var(--app-border)] rounded-[var(--app-radius)] focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                      placeholder="••••••••"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-[var(--app-text)] ml-1">Confirm New Password</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--app-muted)]" size={18} />
                    <input 
                      type="password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full pl-12 pr-4 py-3 bg-[var(--app-panel-soft)] border border-[var(--app-border)] rounded-[var(--app-radius)] focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
              </div>

              <div className="pt-2">
                <button 
                  type="submit"
                  disabled={passLoading}
                  className={`flex items-center justify-center gap-2 px-8 py-3 bg-[var(--app-accent)] text-white rounded-[var(--app-radius)] font-bold shadow-lg shadow-indigo-100 hover:bg-indigo-700 transition-all transform hover:-translate-y-1 active:translate-y-0
                    ${passLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
                >
                  <Save size={18} />
                  {passLoading ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Profile

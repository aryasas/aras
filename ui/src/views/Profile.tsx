// claude-opus-4-7
// ARC profile: account meta on left, password form on right. Submit on the LEFT.
import React, { useState, useEffect } from 'react'
import api from '../lib/api'
import { Mail, Shield, Lock, Save, AlertCircle, CheckCircle, User, Edit3, X } from 'lucide-react'
import { useAras } from '../aras-core/hooks/useAras'
import { useUIStore } from '../store/uiStore'

const Profile = () => {
  const [userInfo, setUserInfo] = useState<any>(null)
  const [profileForm, setProfileForm] = useState({ full_name: '', email: '' })
  const [editingProfile, setEditingProfile] = useState(false)
  const [profileSaving, setProfileSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const setPageTitle = useUIStore((state) => state.setPageTitle)

  useEffect(() => {
    setPageTitle('Your Profile', 'Manage your account details and security settings.', 'PROFILE')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

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
        setProfileForm({ full_name: res.data.full_name || '', email: res.data.email || '' })
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
      await api.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword })
      setPassSuccess('Password updated successfully')
      setOldPassword(''); setNewPassword(''); setConfirmPassword('')
    } catch (err: any) {
      const message = err.response?.data?.message || 'Failed to update password'
      setPassError(message); notify(message, 'error')
    } finally {
      setPassLoading(false)
    }
  }

  const handleSaveProfile = async () => {
    setProfileSaving(true)
    try {
      const res = await api.patch('/user/me', profileForm)
      const nextUser = { ...userInfo, ...(res.data || profileForm) }
      setUserInfo(nextUser)
      setProfileForm({ full_name: nextUser.full_name || '', email: nextUser.email || '' })
      setEditingProfile(false)
      notify('Profile updated', 'success')
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Failed to update profile', 'error')
    } finally {
      setProfileSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="arc arc-card p-8 flex items-center justify-center">
        <div className="arc-id">loading…</div>
      </div>
    )
  }

  const initial = (userInfo?.full_name || userInfo?.username || 'A')[0].toUpperCase()

  return (
    <div className="arc grid grid-cols-1 md:grid-cols-3 gap-5 max-w-5xl mx-auto">
      {/* Account meta */}
      <aside className="arc-card p-5 flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="arc-av" style={{ width: 40, height: 40, fontSize: 14, background: 'color-mix(in oklch, var(--accent) 16%, var(--surface))', color: 'var(--accent)', borderColor: 'var(--accent)' }}>
            {initial}
          </div>
          <div className="min-w-0">
            <div className="arc-id"><b>user</b>/{userInfo?.id ?? '—'}</div>
            <div className="text-[14px] font-medium text-[var(--text)] truncate">{userInfo?.full_name || userInfo?.username}</div>
          </div>
          <button
            type="button"
            onClick={() => setEditingProfile(true)}
            className="ml-auto grid h-7 w-7 place-items-center rounded-full border border-[var(--line)] text-[var(--text-3)] hover:text-[var(--text)]"
            title="Edit profile"
          >
            <Edit3 size={13} />
          </button>
        </div>

        <div className="flex flex-col gap-3 pt-3 border-t border-[var(--line)]">
          <div className="flex items-start gap-2">
            <User size={13} className="text-[var(--text-3)] mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="arc-id arc-dim2">username</div>
              <div className="arc-mono text-[12.5px] text-[var(--text)] truncate">{userInfo?.username}</div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Mail size={13} className="text-[var(--text-3)] mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="arc-id arc-dim2">email</div>
              <div className="text-[12.5px] text-[var(--text)] truncate">{userInfo?.email}</div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Shield size={13} className="text-[var(--text-3)] mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="arc-id arc-dim2">role</div>
              <div className="text-[12.5px]"><span className={`arc-chip ${userInfo?.is_admin ? 'active' : ''}`}>{userInfo?.is_admin ? 'admin' : 'user'}</span></div>
            </div>
          </div>
        </div>

        {editingProfile && (
          <div className="flex flex-col gap-3 border-t border-[var(--line)] pt-3">
            <label className="flex flex-col gap-1.5">
              <span className="arc-id">name</span>
              <input className="arc-input" value={profileForm.full_name} onChange={(e) => setProfileForm((prev) => ({ ...prev, full_name: e.target.value }))} />
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="arc-id">email</span>
              <input type="email" className="arc-input" value={profileForm.email} onChange={(e) => setProfileForm((prev) => ({ ...prev, email: e.target.value }))} />
            </label>
            <div className="flex items-center gap-2">
              <button type="button" onClick={handleSaveProfile} disabled={profileSaving} className="arc-btn primary">
                <Save size={14} /> {profileSaving ? 'Saving...' : 'Save'}
              </button>
              <button type="button" onClick={() => { setEditingProfile(false); setProfileForm({ full_name: userInfo?.full_name || '', email: userInfo?.email || '' }) }} className="arc-btn">
                <X size={14} /> Cancel
              </button>
            </div>
          </div>
        )}
      </aside>

      {/* Password form */}
      <section className="md:col-span-2 arc-card p-5 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="arc-id"><b>auth</b>/change-password</div>
            <h3 className="text-[15px] font-semibold text-[var(--text)] mt-0.5 flex items-center gap-2">
              <Lock size={14} className="text-[var(--accent)]" /> Change password
            </h3>
          </div>
        </div>

        {passError && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-[var(--radius)] border text-[12.5px]"
               style={{ background: 'color-mix(in oklch, var(--danger) 10%, var(--surface))', borderColor: 'color-mix(in oklch, var(--danger) 28%, var(--line))', color: 'var(--danger)' }}>
            <AlertCircle size={14} /><span>{passError}</span>
          </div>
        )}
        {passSuccess && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-[var(--radius)] border text-[12.5px]"
               style={{ background: 'color-mix(in oklch, #10B981 12%, var(--surface))', borderColor: 'color-mix(in oklch, #10B981 28%, var(--line))', color: '#10B981' }}>
            <CheckCircle size={14} /><span>{passSuccess}</span>
          </div>
        )}

        <form onSubmit={handleChangePassword} className="flex flex-col gap-3">
          <label className="flex flex-col gap-1.5">
            <span className="arc-id">old.password</span>
            <input type="password" required value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} className="arc-input" placeholder="••••••••" />
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="flex flex-col gap-1.5">
              <span className="arc-id">new.password</span>
              <input type="password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="arc-input" placeholder="••••••••" />
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="arc-id">confirm</span>
              <input type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="arc-input" placeholder="••••••••" />
            </label>
          </div>

          {/* Submit on the LEFT */}
          <div className="flex items-center gap-2 pt-2">
            <button type="submit" disabled={passLoading} className="arc-btn primary">
              <Save size={14} />
              {passLoading ? 'Updating…' : 'Update password'}
            </button>
            <span className="flex-1" />
            <span className="arc-kbd">⌘↵</span>
          </div>
        </form>
      </section>
    </div>
  )
}

export default Profile

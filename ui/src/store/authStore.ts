import { create } from 'zustand'

interface User {
  username: string
  email: string
  full_name: string
  is_admin: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('aras_token'),
  setUser: (user) => set({ user }),
  setToken: (token) => {
    if (token) localStorage.setItem('aras_token', token)
    else localStorage.removeItem('aras_token')
    set({ token })
  },
  logout: () => {
    localStorage.removeItem('aras_token')
    set({ user: null, token: null })
  },
}))

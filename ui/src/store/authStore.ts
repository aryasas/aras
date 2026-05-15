import { create } from 'zustand'

interface User {
  username: string
  email: string
  full_name: string
  is_admin: boolean
}

export interface Company {
  id: number
  name: string
}

interface AuthState {
  user: User | null
  token: string | null
  companies: Company[]
  activeCompanyId: number | null
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  setCompanies: (companies: Company[]) => void
  setActiveCompany: (id: number | null) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('aras_token'),
  companies: [],
  activeCompanyId: Number(localStorage.getItem('aras_company_id')) || null,
  setUser: (user) => set({ user }),
  setToken: (token) => {
    if (token) localStorage.setItem('aras_token', token)
    else localStorage.removeItem('aras_token')
    set({ token })
  },
  setCompanies: (companies) => set((state) => {
    const activeCompanyStillAllowed = state.activeCompanyId !== null && companies.some((company) => company.id === state.activeCompanyId)
    const autoSelect = !activeCompanyStillAllowed && companies.length > 0 ? companies[0].id : null

    if (autoSelect !== null) {
      localStorage.setItem('aras_company_id', String(autoSelect))
    } else if (state.activeCompanyId !== null && !activeCompanyStillAllowed) {
      localStorage.removeItem('aras_company_id')
    }

    return {
      companies,
      activeCompanyId: activeCompanyStillAllowed ? state.activeCompanyId : (autoSelect ?? null),
    }
  }),
  setActiveCompany: (id) => {
    if (id === null) localStorage.removeItem('aras_company_id')
    else localStorage.setItem('aras_company_id', String(id))
    set({ activeCompanyId: id })
  },
  logout: () => {
    localStorage.removeItem('aras_token')
    localStorage.removeItem('aras_company_id')
    set({ user: null, token: null, companies: [], activeCompanyId: null })
  },
}))

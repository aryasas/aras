import { create } from 'zustand'

interface User {
  username: string
  email: string
  full_name: string
  is_admin: boolean
}

export interface Organization {
  id: number
  name: string
  profile?: string
  unit_type?: string
}

interface AuthState {
  user: User | null
  token: string | null
  organizations: Organization[]
  activeOrgId: number | null
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  setOrganizations: (organizations: Organization[]) => void
  setActiveOrg: (id: number | null) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('aras_token'),
  organizations: [],
  activeOrgId: Number(localStorage.getItem('org_id')) || null,
  setUser: (user) => set({ user }),
  setToken: (token) => {
    if (token) localStorage.setItem('aras_token', token)
    else localStorage.removeItem('aras_token')
    set({ token })
  },
  setOrganizations: (organizations) => set((state) => {
    const activeOrgStillAllowed = state.activeOrgId !== null && organizations.some((organization) => organization.id === state.activeOrgId)
    const autoSelect = !activeOrgStillAllowed && organizations.length > 0 ? organizations[0].id : null

    if (autoSelect !== null) {
      localStorage.setItem('org_id', String(autoSelect))
    } else if (state.activeOrgId !== null && !activeOrgStillAllowed) {
      localStorage.removeItem('org_id')
    }

    return {
      organizations,
      activeOrgId: activeOrgStillAllowed ? state.activeOrgId : (autoSelect ?? null),
    }
  }),
  setActiveOrg: (id) => {
    if (id === null) localStorage.removeItem('org_id')
    else localStorage.setItem('org_id', String(id))
    set({ activeOrgId: id })
  },
  logout: () => {
    localStorage.removeItem('aras_token')
    localStorage.removeItem('org_id')
    set({ user: null, token: null, organizations: [], activeOrgId: null })
  },
}))

import { create } from 'zustand'

const TOKEN_KEY = 'aras_token'
export const ALL_ORGS = -1

function getSessionStorage() {
  return typeof globalThis !== 'undefined' && 'sessionStorage' in globalThis ? globalThis.sessionStorage : null
}

function getLocalStorage() {
  return typeof globalThis !== 'undefined' && 'localStorage' in globalThis ? globalThis.localStorage : null
}

function getStoredToken() {
  const sessionStorageRef = getSessionStorage()
  const localStorageRef = getLocalStorage()
  const sessionToken = sessionStorageRef?.getItem(TOKEN_KEY)
  if (sessionToken) return sessionToken

  const legacyToken = localStorageRef?.getItem(TOKEN_KEY)
  if (legacyToken) {
    sessionStorageRef?.setItem(TOKEN_KEY, legacyToken)
    localStorageRef?.removeItem(TOKEN_KEY)
  }
  return legacyToken || null
}

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
  is_group?: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  organizations: Organization[]
  activeOrgId: number | null
  activeApps: string[]
  // field_name → required_app_name, merged from all active apps' optional_features
  optionalFeatures: Record<string, string>
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  setOrganizations: (organizations: Organization[]) => void
  setActiveOrg: (id: number | null) => void
  setCapabilities: (activeApps: string[], optionalFeatures: Record<string, string>) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: getStoredToken(),
  organizations: [],
  activeOrgId: Number(getLocalStorage()?.getItem('org_id')) || null,
  activeApps: [],
  optionalFeatures: {},
  setUser: (user) => set({ user }),
  setToken: (token) => {
    const localStorageRef = getLocalStorage()
    const sessionStorageRef = getSessionStorage()
    localStorageRef?.removeItem(TOKEN_KEY)
    if (token) sessionStorageRef?.setItem(TOKEN_KEY, token)
    else sessionStorageRef?.removeItem(TOKEN_KEY)
    set({ token })
  },
  setOrganizations: (organizations) => set((state) => {
    const activeOrgStillAllowed = state.activeOrgId !== null && (
      state.activeOrgId === ALL_ORGS ||
      organizations.some((organization) => organization.id === state.activeOrgId)
    )
    const autoSelect = !activeOrgStillAllowed && organizations.length > 0 ? organizations[0].id : null

    if (autoSelect !== null) {
      getLocalStorage()?.setItem('org_id', String(autoSelect))
    } else if (state.activeOrgId !== null && !activeOrgStillAllowed) {
      getLocalStorage()?.removeItem('org_id')
    }

    return {
      organizations,
      activeOrgId: activeOrgStillAllowed ? state.activeOrgId : (autoSelect ?? null),
    }
  }),
  setActiveOrg: (id) => {
    if (id === null) getLocalStorage()?.removeItem('org_id')
    else getLocalStorage()?.setItem('org_id', String(id))
    set({ activeOrgId: id })
  },
  setCapabilities: (activeApps, optionalFeatures) => set({ activeApps, optionalFeatures }),
  logout: () => {
    getSessionStorage()?.removeItem(TOKEN_KEY)
    getLocalStorage()?.removeItem(TOKEN_KEY)
    getLocalStorage()?.removeItem('org_id')
    set({ user: null, token: null, organizations: [], activeOrgId: null, activeApps: [], optionalFeatures: {} })
  },
}))

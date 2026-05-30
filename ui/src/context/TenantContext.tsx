import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

export const TENANT_STORAGE_KEY = 'tenant_id'
const LEGACY_TENANT_STORAGE_KEY = 'aras_tenant_id'

type TenantStorage = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>

interface TenantContextValue {
  tenantId: string
  setTenantId: (tenantId: string) => void
}

const TenantContext = createContext<TenantContextValue | null>(null)

export function migrateLegacyTenantStorage(storage: TenantStorage = localStorage) {
  const legacy = storage.getItem(LEGACY_TENANT_STORAGE_KEY)
  if (legacy && !storage.getItem(TENANT_STORAGE_KEY)) {
    storage.setItem(TENANT_STORAGE_KEY, legacy)
  }
  storage.removeItem(LEGACY_TENANT_STORAGE_KEY)
}

function readStoredTenantId() {
  migrateLegacyTenantStorage()
  return localStorage.getItem(TENANT_STORAGE_KEY) || ''
}

export function TenantProvider({ children }: { children: ReactNode }) {
  const [tenantId, setTenantIdState] = useState(readStoredTenantId)

  const value = useMemo<TenantContextValue>(() => ({
    tenantId,
    setTenantId: (nextTenantId) => {
      const normalizedTenantId = nextTenantId.trim()
      if (normalizedTenantId) {
        localStorage.setItem(TENANT_STORAGE_KEY, normalizedTenantId)
      } else {
        localStorage.removeItem(TENANT_STORAGE_KEY)
      }
      setTenantIdState(normalizedTenantId)
    },
  }), [tenantId])

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  )
}

export function useTenant() {
  const context = useContext(TenantContext)
  if (!context) {
    throw new Error('useTenant must be used inside TenantProvider')
  }
  return context
}

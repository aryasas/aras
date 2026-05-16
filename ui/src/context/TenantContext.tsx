import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

const TENANT_STORAGE_KEY = 'aras_tenant_id'

interface TenantContextValue {
  tenantId: string
  setTenantId: (tenantId: string) => void
}

const TenantContext = createContext<TenantContextValue | null>(null)

function readStoredTenantId() {
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

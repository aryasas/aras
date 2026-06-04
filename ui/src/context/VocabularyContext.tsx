import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type React from 'react'
import api from '../lib/api'
import { vocabularyApi, type VocabularyProfile } from '../lib/api'
import { useAuthStore } from '../store/authStore'

export type VocabularyKey = 'trx_in' | 'trx_out' | 'party' | 'pot'

export interface VocabularyLabels {
  trx_in: string
  trx_out: string
  party: string
  pot: string
}

interface VocabularyContextValue extends VocabularyLabels {
  profile: string
  get: (key: VocabularyKey | string) => string
}

const GENERAL_PROFILE_FALLBACK: VocabularyProfile = {
  key: 'general',
  display_name: 'General',
  description: 'Generic inflow and outflow vocabulary.',
  labels: { trx_in: 'Inflow', trx_out: 'Outflow', party: 'Party', pot: 'Transaction Point' },
}

const VOCABULARY_KEYS = new Set<VocabularyKey>(['trx_in', 'trx_out', 'party', 'pot'])
export const vocabularyCache = new Map<number, Partial<VocabularyLabels>>()
let profileCatalogCache: VocabularyProfile[] | null = null
let profileCatalogPromise: Promise<VocabularyProfile[]> | null = null

const VocabularyContext = createContext<VocabularyContextValue | null>(null)

// claude-opus-4-8
const normalizeProfileCatalog = (profiles: VocabularyProfile[] | null | undefined) =>
  profiles && profiles.length > 0 ? profiles : [GENERAL_PROFILE_FALLBACK]

// claude-opus-4-8
const getProfileDefaults = (profiles: VocabularyProfile[], profile: string): VocabularyLabels =>
  profiles.find((item) => item.key === profile)?.labels || profiles.find((item) => item.key === 'general')?.labels || GENERAL_PROFILE_FALLBACK.labels

// claude-opus-4-8
export function invalidateVocabularyCache(orgId?: number) {
  if (typeof orgId === 'number') {
    vocabularyCache.delete(orgId)
    return
  }
  vocabularyCache.clear()
}

// claude-opus-4-8
export function invalidateVocabularyProfileCatalog() {
  profileCatalogCache = null
  profileCatalogPromise = null
}

// claude-opus-4-8
function loadVocabularyProfiles() {
  if (profileCatalogCache) return Promise.resolve(profileCatalogCache)
  if (profileCatalogPromise) return profileCatalogPromise

  profileCatalogPromise = vocabularyApi.listProfiles()
    .then((profiles) => {
      profileCatalogCache = normalizeProfileCatalog(profiles)
      return profileCatalogCache
    })
    .catch((error) => {
      profileCatalogCache = [GENERAL_PROFILE_FALLBACK]
      throw error
    })
    .finally(() => {
      profileCatalogPromise = null
    })

  return profileCatalogPromise
}

// claude-opus-4-8
export function useVocabularyProfiles() {
  const [profiles, setProfiles] = useState<VocabularyProfile[]>(() => normalizeProfileCatalog(profileCatalogCache))
  const [loading, setLoading] = useState(() => !profileCatalogCache)

  useEffect(() => {
    let cancelled = false

    if (profileCatalogCache) {
      setProfiles(normalizeProfileCatalog(profileCatalogCache))
      setLoading(false)
      return
    }

    setLoading(true)
    loadVocabularyProfiles()
      .then((catalog) => {
        if (!cancelled) setProfiles(normalizeProfileCatalog(catalog))
      })
      .catch((error) => {
        console.error('Failed to load vocabulary profiles', error)
        if (!cancelled) setProfiles([GENERAL_PROFILE_FALLBACK])
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  return {
    profiles,
    loading,
    refresh: async () => {
      invalidateVocabularyProfileCatalog()
      try {
        const catalog = await loadVocabularyProfiles()
        setProfiles(normalizeProfileCatalog(catalog))
        return catalog
      } catch (error) {
        setProfiles([GENERAL_PROFILE_FALLBACK])
        throw error
      } finally {
        setLoading(false)
      }
    },
  }
}

const normalizeVocabulary = (data: unknown): Partial<VocabularyLabels> => {
  if (!data) return {}
  if (Array.isArray(data)) {
    return data.reduce<Partial<VocabularyLabels>>((acc, item) => {
      const row = item as { key?: string; label?: string }
      if (row && row.key && row.label && VOCABULARY_KEYS.has(row.key as VocabularyKey)) acc[row.key as VocabularyKey] = row.label
      return acc
    }, {})
  }
  if (typeof data === 'object') {
    const source = (data as { vocabulary?: unknown }).vocabulary ?? data
    if (Array.isArray(source)) return normalizeVocabulary(source)
    return Object.entries(source as Record<string, unknown>).reduce<Partial<VocabularyLabels>>((acc, [key, value]) => {
      if (VOCABULARY_KEYS.has(key as VocabularyKey) && typeof value === 'string') {
        acc[key as VocabularyKey] = value
      }
      return acc
    }, {})
  }
  return {}
}

export const translateVocabularyText = (text: string, vocabulary: VocabularyLabels) => {
  if (typeof text !== 'string') return text || ''
  return text
    .replace(/\bPoint of Sale\b/g, vocabulary.pot)
    .replace(/\bPOS\b/g, 'POT')
    .replace(/\bSales\b/g, vocabulary.trx_in)
    .replace(/\bSale\b/g, vocabulary.trx_in)
    .replace(/\bPurchases\b/g, vocabulary.trx_out)
    .replace(/\bPurchase\b/g, vocabulary.trx_out)
    .replace(/\bPurchasing\b/g, vocabulary.trx_out)
    .replace(/\bCustomers\b/g, `${vocabulary.party}s`)
    .replace(/\bCustomer\b/g, vocabulary.party)
    .replace(/\bSuppliers\b/g, 'Parties')
    .replace(/\bSupplier\b/g, 'Party')
    .replace(/\bCompany\b/g, 'Organization')
    .replace(/\bcompany\b/g, 'organization')
}

export function VocabularyProvider({ children }: { children: React.ReactNode }) {
  const { activeOrgId, organizations, token } = useAuthStore()
  const activeOrganization = organizations.find((organization) => organization.id === activeOrgId)
  const profile = activeOrganization?.profile || 'general'
  const [overrides, setOverrides] = useState<Partial<VocabularyLabels>>({})
  const { profiles } = useVocabularyProfiles()

  useEffect(() => {
    let cancelled = false

    if (!token || !activeOrgId || activeOrgId <= 0) {
      setOverrides({})
      return
    }

    const cached = vocabularyCache.get(activeOrgId)
    if (cached) {
      setOverrides(cached)
      return
    }

    api.get(`/accounting/organizations/${activeOrgId}/vocabulary`)
      .then((res) => {
        const normalized = normalizeVocabulary(res.data)
        vocabularyCache.set(activeOrgId, normalized)
        if (!cancelled) setOverrides(normalized)
      })
      .catch((error) => {
        console.error('Failed to load vocabulary for organization', activeOrgId, error)
        vocabularyCache.set(activeOrgId, {})
        if (!cancelled) setOverrides({})
      })

    return () => {
      cancelled = true
    }
  }, [activeOrgId, profile, token])

  const value = useMemo<VocabularyContextValue>(() => {
    const defaults = getProfileDefaults(profiles, profile)
    const labels = { ...defaults, ...overrides }

    return {
      ...labels,
      profile,
      get: (key) => {
        if (VOCABULARY_KEYS.has(key as VocabularyKey)) return labels[key as VocabularyKey]
        return translateVocabularyText(key, labels)
      },
    }
  }, [overrides, profile, profiles])

  return (
    <VocabularyContext.Provider value={value}>
      {children}
    </VocabularyContext.Provider>
  )
}

export const useVocabulary = () => {
  const context = useContext(VocabularyContext)
  if (!context) {
    const labels = GENERAL_PROFILE_FALLBACK.labels
    return {
      ...labels,
      profile: 'general',
      get: (key: VocabularyKey | string) => VOCABULARY_KEYS.has(key as VocabularyKey) ? labels[key as VocabularyKey] : translateVocabularyText(key, labels),
    }
  }
  return context
}

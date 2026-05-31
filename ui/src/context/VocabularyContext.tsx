import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type React from 'react'
import api from '../lib/api'
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

export const PROFILE_DEFAULTS: Record<string, VocabularyLabels> = {
  general: { trx_in: 'Inflow', trx_out: 'Outflow', party: 'Party', pot: 'Transaction Point' },
  retail: { trx_in: 'Sales', trx_out: 'Purchase', party: 'Customer', pot: 'Point of Sale' },
  school: { trx_in: 'Tuition', trx_out: 'Expenditure', party: 'Student', pot: 'Payment Counter' },
  coop: { trx_in: 'Savings', trx_out: 'Loan', party: 'Member', pot: 'Teller' },
  npo: { trx_in: 'Donation', trx_out: 'Program Cost', party: 'Donor', pot: 'Collection Point' },
  library: { trx_in: 'Membership', trx_out: 'Procurement', party: 'Member', pot: 'Circulation Desk' },
  hospital: { trx_in: 'Patient Bill', trx_out: 'Procurement', party: 'Patient', pot: 'Registration' },
  government: { trx_in: 'Revenue', trx_out: 'Expenditure', party: 'Citizen', pot: 'Service Counter' },
}

const VOCABULARY_KEYS = new Set<VocabularyKey>(['trx_in', 'trx_out', 'party', 'pot'])
export const vocabularyCache = new Map<number, Partial<VocabularyLabels>>()

const VocabularyContext = createContext<VocabularyContextValue | null>(null)

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

    api.get(`/config/organizations/${activeOrgId}/vocabulary`)
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
    const defaults = PROFILE_DEFAULTS[profile] || PROFILE_DEFAULTS.general
    const labels = { ...defaults, ...overrides }

    return {
      ...labels,
      profile,
      get: (key) => {
        if (VOCABULARY_KEYS.has(key as VocabularyKey)) return labels[key as VocabularyKey]
        return translateVocabularyText(key, labels)
      },
    }
  }, [overrides, profile])

  return (
    <VocabularyContext.Provider value={value}>
      {children}
    </VocabularyContext.Provider>
  )
}

export const useVocabulary = () => {
  const context = useContext(VocabularyContext)
  if (!context) {
    const labels = PROFILE_DEFAULTS.general
    return {
      ...labels,
      profile: 'general',
      get: (key: VocabularyKey | string) => VOCABULARY_KEYS.has(key as VocabularyKey) ? labels[key as VocabularyKey] : translateVocabularyText(key, labels),
    }
  }
  return context
}

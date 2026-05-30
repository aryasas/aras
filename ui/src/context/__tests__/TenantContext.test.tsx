// @ts-nocheck
import { describe, it, expect } from 'vitest'
import { migrateLegacyTenantStorage } from '../TenantContext'

const LEGACY_TENANT_STORAGE_KEY = 'aras_tenant_id'
const TENANT_STORAGE_KEY = 'tenant_id'

function createStorage(initial: Record<string, string> = {}) {
  const values = new Map(Object.entries(initial))

  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => {
      values.set(key, value)
    },
    removeItem: (key: string) => {
      values.delete(key)
    },
  }
}

describe('TenantContext storage migration', () => {
  it('migrates a legacy tenant id to the new key', () => {
    const storage = createStorage({ [LEGACY_TENANT_STORAGE_KEY]: '42' })

    migrateLegacyTenantStorage(storage)

    expect(storage.getItem(TENANT_STORAGE_KEY)).toBe('42')
    expect(storage.getItem(LEGACY_TENANT_STORAGE_KEY)).toBeNull()
  })

  it('prefers the new tenant id when both keys exist', () => {
    const storage = createStorage({
      [LEGACY_TENANT_STORAGE_KEY]: '42',
      [TENANT_STORAGE_KEY]: '99',
    })

    migrateLegacyTenantStorage(storage)

    expect(storage.getItem(TENANT_STORAGE_KEY)).toBe('99')
    expect(storage.getItem(LEGACY_TENANT_STORAGE_KEY)).toBeNull()
  })

  it('does not create tenant keys when storage is empty', () => {
    const storage = createStorage()

    migrateLegacyTenantStorage(storage)

    expect(storage.getItem(TENANT_STORAGE_KEY)).toBeNull()
    expect(storage.getItem(LEGACY_TENANT_STORAGE_KEY)).toBeNull()
  })
})

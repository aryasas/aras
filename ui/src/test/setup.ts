// claude-sonnet-4-6
// Global test setup: jest-dom matchers + per-test DOM cleanup.
import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})

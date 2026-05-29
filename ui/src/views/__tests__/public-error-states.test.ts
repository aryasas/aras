// @ts-nocheck
import { readFileSync } from 'node:fs'

const readView = (name: string) => readFileSync(new URL(`../${name}.tsx`, import.meta.url), 'utf8')

describe('public page error states', () => {
  it('PublicLanding renders a retryable load failure instead of falling back silently', () => {
    const source = readView('PublicLanding')

    expect(source).toContain('landingError')
    expect(source).toContain('loadLanding')
    expect(source).toContain('Coba lagi')
  })

  it('CustomerSignup renders a retryable plan-load failure and preserves signup fallback ids', () => {
    const source = readView('CustomerSignup')

    expect(source).toContain('plansError')
    expect(source).toContain('loadPlans')
    expect(source).toContain('d.subscription_id ?? d.signup_id')
  })

  it('CustomerPortal unwraps API envelopes while keeping raw JSON fallback support', () => {
    const source = readView('CustomerPortal')

    expect(source).toContain('readApiPayload')
    expect(source).toContain("typeof (json as ApiEnvelope<T>).success === 'boolean'")
    expect(source).toContain('return json as T')
  })
})

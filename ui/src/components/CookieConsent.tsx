import { useEffect, useMemo, useState } from 'react'
import { consentApi, type ConsentPolicy } from '../lib/api'
import { useLanguage } from '../context/LanguageContext'

const COOKIE_CONSENT_KEY = 'aras_cookie_consent'

type ConsentChoice = 'accepted_all' | 'rejected_non_essential' | 'preferences'

interface StoredCookieConsent {
  version: string
  choice: ConsentChoice
  preferences: {
    essential: true
    analytics: boolean
  }
  updated_at: string
}

// gpt-5.4
function readStoredConsent() {
  try {
    const raw = localStorage.getItem(COOKIE_CONSENT_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<StoredCookieConsent>
    if (
      typeof parsed.version !== 'string' ||
      typeof parsed.choice !== 'string' ||
      !parsed.preferences ||
      typeof parsed.preferences.analytics !== 'boolean'
    ) {
      return null
    }

    return {
      version: parsed.version,
      choice: parsed.choice as ConsentChoice,
      preferences: {
        essential: true as const,
        analytics: parsed.preferences.analytics,
      },
      updated_at: typeof parsed.updated_at === 'string' ? parsed.updated_at : new Date().toISOString(),
    } satisfies StoredCookieConsent
  } catch {
    return null
  }
}

// gpt-5.4
function applyConsent(record: StoredCookieConsent | null) {
  const consentState = record ? (record.preferences.analytics ? 'granted' : 'essential') : 'pending'
  document.documentElement.dataset.cookieConsent = consentState
  window.dispatchEvent(
    new CustomEvent('aras:cookie-consent-changed', {
      detail: record,
    }),
  )
}

// gpt-5.4
function writeStoredConsent(record: StoredCookieConsent) {
  localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(record))
  applyConsent(record)
}

// gpt-5.4
function getLocalizedPolicyText(policy: ConsentPolicy | null, lang: 'en' | 'id') {
  if (!policy) return ''
  return policy.text[lang] || policy.text.en || policy.text.id || ''
}

// gpt-5.4
export default function CookieConsent() {
  const { lang, t } = useLanguage()
  const [policy, setPolicy] = useState<ConsentPolicy | null>(null)
  const [visible, setVisible] = useState(false)
  const [preferencesOpen, setPreferencesOpen] = useState(false)
  const [analyticsEnabled, setAnalyticsEnabled] = useState(false)

  useEffect(() => {
    let cancelled = false

    consentApi
      .getPolicy()
      .then((nextPolicy) => {
        if (cancelled) return

        setPolicy(nextPolicy)
        const stored = readStoredConsent()
        if (!stored || stored.version !== nextPolicy.version) {
          applyConsent(null)
          setVisible(true)
          setPreferencesOpen(false)
          setAnalyticsEnabled(false)
          return
        }

        setAnalyticsEnabled(stored.preferences.analytics)
        setVisible(false)
        applyConsent(stored)
      })
      .catch(() => {
        if (cancelled) return
        setVisible(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  const localizedPolicyText = useMemo(() => getLocalizedPolicyText(policy, lang), [lang, policy])

  if (!policy || !visible) return null

  const saveChoice = (choice: ConsentChoice, analytics: boolean) => {
    writeStoredConsent({
      version: policy.version,
      choice,
      preferences: {
        essential: true,
        analytics,
      },
      updated_at: new Date().toISOString(),
    })
    setAnalyticsEnabled(analytics)
    setVisible(false)
    setPreferencesOpen(false)
  }

  return (
    <div className={`fixed inset-0 z-[90] flex items-end ${preferencesOpen ? 'bg-black/18' : 'pointer-events-none'}`}>
      <div
        className="w-full pb-4"
        style={{
          insetInline: '1rem',
          position: 'fixed',
          bottom: 0,
          pointerEvents: 'auto',
        }}
      >
        <section
          className="mx-auto w-full max-w-4xl rounded-[calc(var(--radius-lg)+2px)] border border-[var(--line)] py-5 shadow-2xl backdrop-blur-xl"
          style={{ paddingInline: '1.25rem', background: 'color-mix(in oklch, var(--surface) 92%, white)' }}
        >
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--accent)]">
                  {t('cookie.eyebrow', 'Privacy controls')}
                </p>
                <h2 className="text-lg font-semibold text-[var(--text)]">
                  {t('cookie.title', 'Choose how ARAS uses cookies')}
                </h2>
                <p className="text-sm leading-6 text-[var(--text-2)]">
                  {t('cookie.description', 'We use essential cookies to keep the app secure. Analytics and other non-essential cookies stay off until you choose.')}
                </p>
              </div>
              <span className="rounded-full bg-[var(--surface-2)] py-1 text-xs font-medium text-[var(--text-2)]" style={{ paddingInline: '0.75rem' }}>
                {t('cookie.policyVersion', 'Policy version')}: {policy.version}
              </span>
            </div>

            {preferencesOpen ? (
              <div className="grid gap-3 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] py-4" style={{ paddingInline: '1rem' }}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-[var(--text)]">{t('cookie.essentialTitle', 'Essential cookies')}</p>
                    <p className="text-sm text-[var(--text-2)]">{t('cookie.essentialDescription', 'Required for authentication, routing, and security. Always on.')}</p>
                  </div>
                  <span className="rounded-full bg-emerald-100 py-1 text-xs font-semibold text-emerald-700" style={{ paddingInline: '0.75rem' }}>
                    {t('cookie.alwaysActive', 'Always active')}
                  </span>
                </div>

                <label className="flex items-start justify-between gap-3 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] py-3" style={{ paddingInline: '1rem' }}>
                  <div>
                    <p className="text-sm font-semibold text-[var(--text)]">{t('cookie.analyticsTitle', 'Analytics cookies')}</p>
                    <p className="text-sm text-[var(--text-2)]">{t('cookie.analyticsDescription', 'Help us understand product usage after you opt in.')}</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={analyticsEnabled}
                    onChange={(event) => setAnalyticsEnabled(event.target.checked)}
                    className="mt-1 h-4 w-4 rounded border-[var(--line)] text-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
                  />
                </label>

                <div className="rounded-[var(--radius)] border border-dashed border-[var(--line)] py-3 text-sm leading-6 text-[var(--text-2)]" style={{ paddingInline: '1rem' }}>
                  <p className="font-medium text-[var(--text)]">{t('cookie.policyExcerptTitle', 'Marketing consent text')}</p>
                  <p className="mt-2 whitespace-pre-wrap">{localizedPolicyText}</p>
                </div>
              </div>
            ) : null}

            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <button
                type="button"
                onClick={() => setPreferencesOpen((current) => !current)}
                className="rounded-[var(--radius)] border border-[var(--line)] py-2 text-sm font-medium text-[var(--text)] hover:bg-[var(--surface-2)]"
                style={{ paddingInline: '1rem' }}
              >
                {preferencesOpen ? t('cookie.hidePreferences', 'Hide preferences') : t('cookie.preferences', 'Preferences')}
              </button>

              <div className="flex flex-col gap-2 sm:flex-row">
                <button
                  type="button"
                  onClick={() => saveChoice('rejected_non_essential', false)}
                  className="rounded-[var(--radius)] border border-[var(--line)] py-2 text-sm font-medium text-[var(--text)] hover:bg-[var(--surface-2)]"
                  style={{ paddingInline: '1rem' }}
                >
                  {t('cookie.reject', 'Reject non-essential')}
                </button>
                {preferencesOpen ? (
                  <button
                    type="button"
                    onClick={() => saveChoice('preferences', analyticsEnabled)}
                    className="rounded-[var(--radius)] bg-[var(--surface-3)] py-2 text-sm font-semibold text-[var(--text)] hover:opacity-90"
                    style={{ paddingInline: '1rem' }}
                  >
                    {t('cookie.savePreferences', 'Save preferences')}
                  </button>
                ) : null}
                <button
                  type="button"
                  onClick={() => saveChoice('accepted_all', true)}
                  className="rounded-[var(--radius)] bg-[var(--accent)] py-2 text-sm font-semibold text-white hover:bg-[var(--aras-accent-strong)]"
                  style={{ paddingInline: '1rem' }}
                >
                  {t('cookie.accept', 'Accept all')}
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

const DEFAULT_DEV_API_ORIGIN = 'http://localhost:8000'

export function getBackendOrigin() {
  const configured = import.meta.env.VITE_API_ORIGIN || import.meta.env.VITE_API_BASE_URL
  if (configured) {
    try {
      return new URL(configured, window.location.origin).origin
    } catch {
      return DEFAULT_DEV_API_ORIGIN
    }
  }

  if (window.location.hostname === 'localhost' && window.location.port === '5173') {
    return DEFAULT_DEV_API_ORIGIN
  }

  return window.location.origin
}

export function getApiDocsUrl() {
  return `${getBackendOrigin()}/docs`
}

export function getOpenApiJsonUrl() {
  return `${getBackendOrigin()}/openapi.json`
}

export function openApiDocs() {
  window.open(getApiDocsUrl(), '_blank', 'noopener,noreferrer')
}

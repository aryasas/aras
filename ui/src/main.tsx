import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { NotificationProvider } from './aras-core/contexts/NotificationContext'
import { ConfirmProvider } from './aras-core/contexts/ConfirmContext'
import { ErrorBoundary } from './aras-core/components/ErrorBoundary'
import { TenantProvider } from './context/TenantContext'
import { LanguageProvider } from './context/LanguageContext'
import { connectArasWebSocket } from './lib/ws'

connectArasWebSocket()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <NotificationProvider>
        <ConfirmProvider>
          <TenantProvider>
            <LanguageProvider>
              <App />
            </LanguageProvider>
          </TenantProvider>
        </ConfirmProvider>
      </NotificationProvider>
    </ErrorBoundary>
  </StrictMode>,
)

if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((error) => {
      console.error('Service worker registration failed', error)
    })
  })
}

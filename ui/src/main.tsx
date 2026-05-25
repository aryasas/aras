import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { NotificationProvider } from './aras-core/contexts/NotificationContext'
import { ConfirmProvider } from './aras-core/contexts/ConfirmContext'
import { ErrorBoundary } from './aras-core/components/ErrorBoundary'
import { TenantProvider } from './context/TenantContext'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <NotificationProvider>
        <ConfirmProvider>
          <TenantProvider>
            <App />
          </TenantProvider>
        </ConfirmProvider>
      </NotificationProvider>
    </ErrorBoundary>
  </StrictMode>,
)

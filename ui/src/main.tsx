import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { FormattingService } from './aras-core/services/FormattingService'
import { NotificationProvider } from './aras-core/contexts/NotificationContext'
import { ConfirmProvider } from './aras-core/contexts/ConfirmContext'
import { ErrorBoundary } from './aras-core/components/ErrorBoundary'

// Initialize Global Services
FormattingService.init().then(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <ErrorBoundary>
        <NotificationProvider>
          <ConfirmProvider>
            <App />
          </ConfirmProvider>
        </NotificationProvider>
      </ErrorBoundary>
    </StrictMode>,
  )
})

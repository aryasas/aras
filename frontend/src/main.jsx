import './index.css'
import React, { StrictMode, Component as ReactComponent } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ArasListView from './components/ArasListView.jsx'
import ArasFormView from './components/ArasFormView.jsx'
import ReactAppShell from './components/ReactAppShell.jsx'

class ErrorBoundary extends ReactComponent {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', color: 'red', fontFamily: 'sans-serif' }}>
          <h2>Something went wrong.</h2>
          <pre>{this.state.error?.toString()}</pre>
        </div>
      )
    }
    return this.props.children
  }
}

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

function mountApp() {
  const mountPoint = document.getElementById('root')
  if (!mountPoint) return;

  const rawProps = mountPoint.dataset.arasProps
  let props = {}
  if (rawProps) {
    try {
      props = JSON.parse(rawProps)
    } catch (e) {
      try {
        props = JSON.parse(rawProps.replace(/'/g, '"'))
      } catch (e2) {
        console.error('Failed to parse props', e2)
      }
    }
  }

  createRoot(mountPoint).render(
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="*" element={<ReactAppShell {...props} />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

document.addEventListener('DOMContentLoaded', mountApp)
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  mountApp()
}

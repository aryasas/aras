import './index.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

// Add new components here as you build them
const registry = {
  ArasListView: () => import('./components/ArasListView'),
  ArasFormView: () => import('./components/ArasFormView'),
}

async function mountAll() {
  const mounts = document.querySelectorAll('[data-aras-mount]')
  for (const el of mounts) {
    const name = el.dataset.arasMount
    const loader = registry[name]
    if (!loader) {
      console.warn(`[aras] unknown component: ${name}`)
      continue
    }
    const mod = await loader()
    const Component = mod.default
    const props = el.dataset.arasProps ? JSON.parse(el.dataset.arasProps) : {}
    createRoot(el).render(
      <StrictMode>
        <QueryClientProvider client={queryClient}>
          <Component {...props} />
        </QueryClientProvider>
      </StrictMode>
    )
  }
}

mountAll()

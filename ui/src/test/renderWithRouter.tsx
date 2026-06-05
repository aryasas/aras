// claude-sonnet-4-6
// Render helper that wraps a component in a MemoryRouter so framework components
// using useNavigate/useLocation (Combobox, useAras, etc.) work under test.
import type { ReactElement } from 'react'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

export function renderWithRouter(ui: ReactElement, { route = '/' } = {}) {
  return render(<MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>)
}

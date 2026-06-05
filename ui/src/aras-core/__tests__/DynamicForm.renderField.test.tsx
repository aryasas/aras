// claude-sonnet-4-6
// renderField is DynamicForm's per-field renderer: label (vocabulary-mapped), the
// schema-resolved input, error text + aria wiring, visibility gating. It's the unit
// every form field flows through, so it's tested in isolation from the form's data
// fetching. We mock the design wrapper to a plain div to avoid store coupling.
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

vi.mock('../components/design/DesignElement', () => ({
  DesignElement: ({ children, ...rest }: any) => <div {...rest}>{children}</div>,
}))
// DynamicForm pulls many app deps at module load; stub the heavy ones so importing
// renderField doesn't drag in stores/api. Only renderField is under test here.
vi.mock('../../lib/api', () => ({ default: { get: vi.fn() } }))
vi.mock('../../store/authStore', () => ({ useAuthStore: () => ({}) }))
vi.mock('../../store/uiStore', () => ({ useUIStore: () => ({}) }))

import { renderField } from '../components/DynamicForm'

const field = (over: any = {}) => ({ name: 'qty', label: 'Quantity', type: 'string', ...over })

describe('renderField', () => {
  it('renders the field label through vocabularyGet', () => {
    render(<>{renderField({ field: field(), value: '', onChange: () => {}, formData: {},
      vocabularyGet: (l: string) => l.toUpperCase() })}</>)
    expect(screen.getByText('QUANTITY')).toBeInTheDocument()
  })

  it('renders an input wired to onChange', () => {
    const onChange = vi.fn()
    render(<>{renderField({ field: field(), value: '', onChange, formData: {} })}</>)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: '7' } })
    expect(onChange).toHaveBeenCalledWith('7')
  })

  it('renders error text in a linked errorId element when error is present', () => {
    render(<>{renderField({ field: field(), value: '', onChange: () => {}, formData: {},
      error: 'Required' })}</>)
    const err = screen.getByText('Required')
    expect(err).toBeInTheDocument()
    // renderField wires the error into id="error-<name>" (aria-describedby target).
    expect(err).toHaveAttribute('id', 'error-qty')
    // The scalar input forwards aria-invalid + aria-describedby to the real <input>,
    // so assistive tech links the error to the field.
    const input = screen.getByRole('textbox')
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(input).toHaveAttribute('aria-describedby', 'error-qty')
  })

  it('returns null when the field is not visible', () => {
    const { container } = render(
      <>{renderField({ field: field(), value: '', onChange: () => {}, formData: {},
        isVisible: () => false })}</>,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('propagates disabled to the resolved input', () => {
    render(<>{renderField({ field: field(), value: '', onChange: () => {}, formData: {},
      disabled: true })}</>)
    expect(screen.getByRole('textbox')).toBeDisabled()
  })
})

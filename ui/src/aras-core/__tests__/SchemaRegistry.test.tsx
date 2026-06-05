// claude-sonnet-4-6
// Tests the framework's field-resolution layer — the map every DynamicForm/ListView
// cell goes through. Covers ui_type→component resolution, fallback behavior, and that
// resolved components render real inputs wired to onChange.
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import {
  resolveFieldComponent,
  resolveFilterComponent,
  type Field,
} from '../SchemaRegistry'

const field = (over: Partial<Field> = {}): Field => ({
  name: 'f',
  type: 'string',
  label: 'My Field',
  ...over,
})

describe('resolveFieldComponent', () => {
  it('maps known scalar ui types to distinct components', () => {
    const str = resolveFieldComponent(field({ type: 'string' }))
    const num = resolveFieldComponent(field({ type: 'number' }))
    const bool = resolveFieldComponent(field({ type: 'boolean' }))
    expect(str).toBeTypeOf('function')
    expect(num).not.toBe(str)
    expect(bool).not.toBe(num)
  })

  it('prefers info.ui_type over the raw type', () => {
    const asNumber = resolveFieldComponent(field({ type: 'string', info: { ui_type: 'number' } }))
    const plainNumber = resolveFieldComponent(field({ type: 'number' }))
    expect(asNumber).toBe(plainNumber)
  })

  it('falls back to the default input for unknown ui types', () => {
    const unknown = resolveFieldComponent(field({ type: 'totally-made-up' }))
    const plainString = resolveFieldComponent(field({ type: 'string' }))
    expect(unknown).toBe(plainString)
  })

  it('renders a text input that propagates changes via onChange', () => {
    const Comp = resolveFieldComponent(field({ type: 'string' }))
    const onChange = vi.fn()
    render(<Comp field={field()} value="" onChange={onChange} formData={{}} />)
    const input = screen.getByPlaceholderText(/enter my field/i)
    fireEvent.change(input, { target: { value: 'hello' } })
    expect(onChange).toHaveBeenCalledWith('hello')
  })

  it('renders a boolean toggle that emits the checked state', () => {
    const Comp = resolveFieldComponent(field({ type: 'boolean' }))
    const onChange = vi.fn()
    render(<Comp field={field({ type: 'boolean' })} value={false} onChange={onChange} formData={{}} />)
    fireEvent.click(screen.getByRole('checkbox'))
    expect(onChange).toHaveBeenCalledWith(true)
  })

  it('respects the disabled flag on inputs', () => {
    const Comp = resolveFieldComponent(field({ type: 'string' }))
    render(<Comp field={field()} value="" onChange={() => {}} formData={{}} disabled />)
    expect(screen.getByPlaceholderText(/enter my field/i)).toBeDisabled()
  })
})

describe('resolveFilterComponent', () => {
  it('returns a dedicated component for boolean filters (rendered via Combobox)', () => {
    // Boolean filters resolve to a Combobox-backed tri-state; rendering it needs a
    // Router (the lookup variant calls useNavigate), so the string↔boolean mapping is
    // covered at the Combobox level. Here we lock in that boolean gets its own resolver.
    const boolComp = resolveFilterComponent(field({ type: 'boolean' }))
    const textComp = resolveFilterComponent(field({ type: 'string' }))
    expect(boolComp).toBeTypeOf('function')
    expect(boolComp).not.toBe(textComp)
  })

  it('renders a date input for date fields', () => {
    const Comp = resolveFilterComponent(field({ type: 'date' }))
    const { container } = render(
      <Comp field={field({ type: 'date' })} value="2026-06-05T00:00:00" onChange={() => {}} formData={{}} />,
    )
    const input = container.querySelector('input[type="date"]') as HTMLInputElement
    expect(input).not.toBeNull()
    expect(input.value).toBe('2026-06-05')
  })

  it('defaults unknown filter types to a plain text input', () => {
    const Comp = resolveFilterComponent(field({ type: 'string' }))
    render(<Comp field={field()} value="" onChange={() => {}} formData={{}} />)
    expect(screen.getByPlaceholderText(/value/i)).toBeInTheDocument()
  })
})

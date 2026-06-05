// claude-sonnet-4-6
// Tests for the pure helpers extracted from DynamicForm: StatusBadge rendering and
// the recursive display-token finder.
import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { StatusBadge, findDisplayToken } from '../components/dynamicForm.helpers'

describe('StatusBadge', () => {
  it('renders nothing for empty/null values', () => {
    const { container: c1 } = render(<StatusBadge value={null} />)
    const { container: c2 } = render(<StatusBadge value="" />)
    expect(c1).toBeEmptyDOMElement()
    expect(c2).toBeEmptyDOMElement()
  })

  it('uses the configured label override when present', () => {
    const { container } = render(<StatusBadge value="in_review" />)
    expect(container.textContent).toContain('In review')
  })

  it('humanizes underscored statuses without an override', () => {
    const { container } = render(<StatusBadge value="in_progress" />)
    expect(container.textContent).toContain('in progress')
  })
})

describe('findDisplayToken', () => {
  it('returns a top-level display_token', () => {
    expect(findDisplayToken({ display_token: 'INV-1' })).toBe('INV-1')
  })

  it('recurses into data/result wrappers', () => {
    expect(findDisplayToken({ data: { display_token: 'X' } })).toBe('X')
    expect(findDisplayToken({ result: { data: { display_token: 'Y' } } })).toBe('Y')
  })

  it('returns null when no token exists', () => {
    expect(findDisplayToken({ foo: 1 })).toBeNull()
    expect(findDisplayToken(null)).toBeNull()
    expect(findDisplayToken('str')).toBeNull()
  })
})

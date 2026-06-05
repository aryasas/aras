// claude-sonnet-4-6
// Combobox is the framework's universal picker (select/lookup/fk). These tests cover
// the static-options path (no network): open, filter-by-search, select→onChange(id),
// clear→onChange(null), and that a preset value renders its label.
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, within } from '@testing-library/react'
import { renderWithRouter } from '../../test/renderWithRouter'
import Combobox from '../components/Combobox'

// api is only hit on the resource (lookup) path; stub it so an accidental fetch is inert.
vi.mock('../../lib/api', () => ({
  default: { get: vi.fn().mockResolvedValue({ data: { items: [] } }) },
}))

const OPTIONS = [
  { label: 'Apple', value: 'a' },
  { label: 'Banana', value: 'b' },
  { label: 'Cherry', value: 'c' },
]

describe('Combobox (static options)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows the placeholder when no value is selected', () => {
    renderWithRouter(<Combobox options={OPTIONS} value={null} onChange={() => {}} placeholder="Pick one" />)
    expect(screen.getByText('Pick one')).toBeInTheDocument()
  })

  it('renders the label of a preset value', () => {
    renderWithRouter(<Combobox options={OPTIONS} value="b" onChange={() => {}} />)
    expect(screen.getByText('Banana')).toBeInTheDocument()
  })

  it('opens the dropdown and lists all options', () => {
    renderWithRouter(<Combobox options={OPTIONS} value={null} onChange={() => {}} placeholder="Pick" />)
    fireEvent.click(screen.getByText('Pick'))
    expect(screen.getByText('Apple')).toBeInTheDocument()
    expect(screen.getByText('Banana')).toBeInTheDocument()
    expect(screen.getByText('Cherry')).toBeInTheDocument()
  })

  it('filters options by the search term', () => {
    renderWithRouter(<Combobox options={OPTIONS} value={null} onChange={() => {}} placeholder="Pick" />)
    fireEvent.click(screen.getByText('Pick'))
    const searchBox = screen.getByRole('textbox')
    fireEvent.change(searchBox, { target: { value: 'ban' } })
    expect(screen.getByText('Banana')).toBeInTheDocument()
    expect(screen.queryByText('Apple')).not.toBeInTheDocument()
    expect(screen.queryByText('Cherry')).not.toBeInTheDocument()
  })

  it('emits the option value (not label) on select', () => {
    const onChange = vi.fn()
    renderWithRouter(<Combobox options={OPTIONS} value={null} onChange={onChange} placeholder="Pick" />)
    fireEvent.click(screen.getByText('Pick'))
    fireEvent.click(screen.getByText('Cherry'))
    expect(onChange).toHaveBeenCalledWith('c')
  })

  it('clears the selection via onChange(null)', () => {
    const onChange = vi.fn()
    renderWithRouter(<Combobox options={OPTIONS} value="a" onChange={onChange} />)
    // the clear (X) button appears once a value is selected; it fires on mouseDown
    const clearBtn = screen.getByTitle('Clear')
    fireEvent.mouseDown(clearBtn)
    expect(onChange).toHaveBeenCalledWith(null)
  })

  it('does not open when disabled', () => {
    renderWithRouter(<Combobox options={OPTIONS} value={null} onChange={() => {}} placeholder="Pick" disabled />)
    fireEvent.click(screen.getByText('Pick'))
    expect(screen.queryByText('Apple')).not.toBeInTheDocument()
  })

  it('selects with the keyboard (ArrowDown + Enter)', () => {
    const onChange = vi.fn()
    renderWithRouter(<Combobox options={OPTIONS} value={null} onChange={onChange} placeholder="Pick" />)
    const trigger = screen.getByText('Pick').closest('div')!
    fireEvent.keyDown(trigger, { key: 'ArrowDown' }) // open
    const live = within(document.body)
    fireEvent.keyDown(live.getByRole('textbox'), { key: 'ArrowDown' }) // highlight first
    fireEvent.keyDown(live.getByRole('textbox'), { key: 'Enter' }) // select
    expect(onChange).toHaveBeenCalledWith('a')
  })
})

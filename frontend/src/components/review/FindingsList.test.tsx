import { describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { clickAsync, selectAsync } from '../../test/act'
import FindingsList from './FindingsList'
import { makeFinding } from '../../test/fixtures'

const findings = [
  makeFinding({ id: 'f1', title: 'Passive voice', severity: 'medium', category: 'grammar' }),
  makeFinding({
    id: 'f2',
    title: 'Unsourced claim',
    severity: 'critical',
    category: 'citations',
    source: 'ai',
    status: 'accepted',
  }),
  makeFinding({
    id: 'f3',
    title: 'Repeated sentence',
    severity: 'low',
    category: 'repetition',
    is_stale: true,
  }),
]

describe('FindingsList', () => {
  it('renders every finding with severity and source', () => {
    render(<FindingsList findings={findings} onStatusChange={vi.fn()} />)
    expect(screen.getByText('Passive voice')).toBeInTheDocument()
    expect(screen.getByText('Unsourced claim')).toBeInTheDocument()
    expect(screen.getByText('Repeated sentence')).toBeInTheDocument()
    expect(screen.getByText('AI suggestion')).toBeInTheDocument()
    expect(screen.getAllByText('Checked automatically')).toHaveLength(2)
    expect(screen.getByText('Stale')).toBeInTheDocument()
  })

  it('filters by severity and updates the visible count', async () => {
    const user = userEvent.setup()
    render(<FindingsList findings={findings} onStatusChange={vi.fn()} />)

    await selectAsync(user, screen.getByLabelText('Filter by severity'), 'critical')

    expect(screen.getByText('Unsourced claim')).toBeInTheDocument()
    expect(screen.queryByText('Passive voice')).not.toBeInTheDocument()
    expect(screen.getByText('1 of 3')).toBeInTheDocument()
  })

  it('filters by status so accepted findings can be hidden', async () => {
    const user = userEvent.setup()
    render(<FindingsList findings={findings} onStatusChange={vi.fn()} />)

    await selectAsync(user, screen.getByLabelText('Filter by status'), 'accepted')

    expect(screen.getByText('Unsourced claim')).toBeInTheDocument()
    expect(screen.queryByText('Passive voice')).not.toBeInTheDocument()
  })

  it('reports the requested status change', async () => {
    const onStatusChange = vi.fn()
    const user = userEvent.setup()
    render(<FindingsList findings={[findings[0]]} onStatusChange={onStatusChange} />)

    const card = screen.getByTestId('finding-f1')
    await clickAsync(user, within(card).getByRole('button', { name: 'rejected' }))

    expect(onStatusChange).toHaveBeenCalledWith('f1', 'rejected')
  })

  it('shows explanation and suggested text in the details panel', async () => {
    const user = userEvent.setup()
    render(<FindingsList findings={[findings[0]]} onStatusChange={vi.fn()} />)

    expect(screen.queryByText(/Consider naming the actor/)).not.toBeInTheDocument()
    await clickAsync(user, screen.getByRole('button', { name: 'Details' }))

    expect(screen.getByText(/Consider naming the actor/)).toBeInTheDocument()
    expect(screen.getByText('The auditor reviews the policy.')).toBeInTheDocument()
  })

  it('offers an AI fix only when a section is known', async () => {
    const onRequestEdit = vi.fn()
    const user = userEvent.setup()
    render(
      <FindingsList
        findings={[findings[0], makeFinding({ id: 'f4', title: 'Global note', section_id: null })]}
        onStatusChange={vi.fn()}
        onRequestEdit={onRequestEdit}
      />,
    )

    const withSection = screen.getByTestId('finding-f1')
    await clickAsync(user, within(withSection).getByRole('button', { name: 'Fix with AI' }))
    expect(onRequestEdit).toHaveBeenCalledWith(expect.objectContaining({ id: 'f1' }))

    const withoutSection = screen.getByTestId('finding-f4')
    expect(within(withoutSection).queryByRole('button', { name: 'Fix with AI' })).toBeNull()
  })

  it('renders an empty state instead of a bare list', () => {
    render(<FindingsList findings={[]} onStatusChange={vi.fn()} />)
    expect(screen.getByText('No findings')).toBeInTheDocument()
  })
})

import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { clickAsync } from '../../test/act'
import SuggestedChange from './SuggestedChange'
import { makeProposal } from '../../test/fixtures'

describe('SuggestedChange', () => {
  it('highlights removed and added text inline', () => {
    const { container } = render(
      <SuggestedChange proposal={makeProposal()} onApply={vi.fn()} onReject={vi.fn()} />,
    )

    const diff = screen.getByTestId('proposal-diff')
    const removed = Array.from(diff.querySelectorAll('del'))
      .map((node) => node.textContent)
      .join('')
    const added = Array.from(diff.querySelectorAll('ins'))
      .map((node) => node.textContent)
      .join('')

    // Inline diffs interleave tokens, so assert on each side's own fragments.
    expect(removed).toContain('is reviewed')
    expect(added).toContain('auditor')
    expect(added).toContain('policy.')
    expect(container.textContent).toContain('Suggested change')
  })

  it('can switch to a side-by-side view', async () => {
    render(<SuggestedChange proposal={makeProposal()} onApply={vi.fn()} onReject={vi.fn()} />)
    const user = userEvent.setup()

    await clickAsync(user, screen.getByRole('button', { name: 'Show side by side' }))

    expect(screen.getByText('Original')).toBeInTheDocument()
    expect(screen.getByText('Proposed')).toBeInTheDocument()
    expect(screen.getByText('The auditor reviews the policy.')).toBeInTheDocument()
    expect(screen.queryByTestId('proposal-diff')).not.toBeInTheDocument()
  })

  it('warns when a suggestion only changes spacing or case', () => {
    render(
      <SuggestedChange
        proposal={makeProposal({
          original_text: 'the policy is clear.',
          proposed_text: 'The policy  is clear.',
        })}
        onApply={vi.fn()}
        onReject={vi.fn()}
      />,
    )
    expect(screen.getByText(/only changes capitalisation or spacing/)).toBeInTheDocument()
  })

  it('warns about citation re-checks from the proposal impact', () => {
    render(
      <SuggestedChange
        proposal={makeProposal({
          impact: { verification_recheck_required: true, notes: 'Two claims need re-verification.' },
        })}
        onApply={vi.fn()}
        onReject={vi.fn()}
      />,
    )
    expect(screen.getByText('Two claims need re-verification.')).toBeInTheDocument()
  })

  it('calls apply and reject with the proposal', async () => {
    const onApply = vi.fn()
    const onReject = vi.fn()
    const proposal = makeProposal()
    render(<SuggestedChange proposal={proposal} onApply={onApply} onReject={onReject} />)
    const user = userEvent.setup()

    await clickAsync(user, screen.getByRole('button', { name: 'Accept change' }))
    await clickAsync(user, screen.getByRole('button', { name: 'Reject' }))

    expect(onApply).toHaveBeenCalledWith(proposal)
    expect(onReject).toHaveBeenCalledWith(proposal)
  })

  it('shows the error from a failed apply', async () => {
    const onApply = vi.fn().mockRejectedValue(new Error('The document changed'))
    render(<SuggestedChange proposal={makeProposal()} onApply={onApply} onReject={vi.fn()} />)
    const user = userEvent.setup()

    await clickAsync(user, screen.getByRole('button', { name: 'Accept change' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The document changed')
  })
})

import type { ComponentProps } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { clickAsync, selectAsync } from '../../test/act'
import ReviewPanel from './ReviewPanel'
import { api } from '../../api/client'
import { makeFinding, makeProposal, makeReport } from '../../test/fixtures'

vi.mock('../../api/client', () => ({
  api: {
    startReview: vi.fn(),
    updateFinding: vi.fn(),
    proposeEdit: vi.fn(),
    applyProposal: vi.fn(),
    rejectProposal: vi.fn(),
  },
}))

const mockedApi = api as unknown as {
  startReview: ReturnType<typeof vi.fn>
  updateFinding: ReturnType<typeof vi.fn>
  proposeEdit: ReturnType<typeof vi.fn>
  applyProposal: ReturnType<typeof vi.fn>
  rejectProposal: ReturnType<typeof vi.fn>
}

const sections = [{ id: 'section-1', title: 'Introduction' }]

function renderPanel(overrides: Partial<ComponentProps<typeof ReviewPanel>> = {}) {
  const onReportChange = vi.fn()
  const onDocumentUpdated = vi.fn()
  render(
    <ReviewPanel
      documentId="doc-1"
      sections={sections}
      report={null}
      onReportChange={onReportChange}
      onDocumentUpdated={onDocumentUpdated}
      {...overrides}
    />,
  )
  return { onReportChange, onDocumentUpdated }
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ReviewPanel', () => {
  it('starts a full-document review and hands the report back', async () => {
    const report = makeReport([makeFinding()])
    mockedApi.startReview.mockResolvedValue(report)
    const { onReportChange } = renderPanel()
    const user = userEvent.setup()

    await clickAsync(user, screen.getByRole('button', { name: 'Run review' }))

    expect(mockedApi.startReview).toHaveBeenCalledWith('doc-1', {
      mode: 'full',
      scope: 'document',
      categories: undefined,
      section_id: undefined,
    })
    await waitFor(() => expect(onReportChange).toHaveBeenCalledWith(report))
  })

  it('sends the chosen mode', async () => {
    mockedApi.startReview.mockResolvedValue(makeReport([]))
    renderPanel()
    const user = userEvent.setup()

    await clickAsync(user, screen.getByText('Academic Review'))
    await clickAsync(user, screen.getByRole('button', { name: 'Run review' }))

    expect(mockedApi.startReview).toHaveBeenCalledWith(
      'doc-1',
      expect.objectContaining({ mode: 'academic' }),
    )
  })

  it('blocks a custom review until at least one category is picked', async () => {
    mockedApi.startReview.mockResolvedValue(makeReport([]))
    renderPanel()
    const user = userEvent.setup()

    await clickAsync(user, screen.getByText('Custom Review'))
    const run = screen.getByRole('button', { name: 'Run review' })
    expect(run).toBeDisabled()

    await clickAsync(user, screen.getByText('Citations'))
    expect(run).toBeEnabled()

    await clickAsync(user, run)
    expect(mockedApi.startReview).toHaveBeenCalledWith(
      'doc-1',
      expect.objectContaining({ mode: 'custom', categories: ['citations'] }),
    )
  })

  it('requires a section when the scope is a single section', async () => {
    renderPanel()
    const user = userEvent.setup()

    await selectAsync(user, screen.getByLabelText('Scope'), 'section')

    expect(screen.getByRole('button', { name: 'Run review' })).toBeDisabled()
    expect(screen.getByRole('option', { name: 'Introduction' })).toBeInTheDocument()
  })

  it('surfaces a failed review instead of pretending it worked', async () => {
    mockedApi.startReview.mockRejectedValue(new Error('Document is too large to review'))
    const { onReportChange } = renderPanel()
    const user = userEvent.setup()

    await clickAsync(user, screen.getByRole('button', { name: 'Run review' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Document is too large to review')
    expect(onReportChange).not.toHaveBeenCalled()
  })

  it('summarises an existing report', () => {
    renderPanel({
      report: makeReport([
        makeFinding({ id: 'f1', severity: 'critical', category: 'citations' }),
        makeFinding({ id: 'f2', severity: 'low', category: 'grammar', status: 'accepted' }),
      ]),
    })

    expect(screen.getByText('2 findings')).toBeInTheDocument()
    expect(screen.getByText(/1 open/)).toBeInTheDocument()
    expect(screen.getByText('Critical: 1')).toBeInTheDocument()
    expect(screen.getByText(/AI findings are suggestions/)).toBeInTheDocument()
  })

  it('updates a finding status locally after the API accepts it', async () => {
    const report = makeReport([makeFinding()])
    mockedApi.updateFinding.mockResolvedValue(makeFinding({ status: 'ignored' }))
    const { onReportChange } = renderPanel({ report })
    const user = userEvent.setup()

    await clickAsync(user, screen.getByRole('button', { name: 'ignored' }))

    expect(mockedApi.updateFinding).toHaveBeenCalledWith('finding-1', 'ignored')
    await waitFor(() =>
      expect(onReportChange).toHaveBeenCalledWith(
        expect.objectContaining({
          findings: [expect.objectContaining({ id: 'finding-1', status: 'ignored' })],
        }),
      ),
    )
  })

  it('generates and applies a section suggestion from a finding', async () => {
    const report = makeReport([makeFinding()])
    const proposal = makeProposal()
    mockedApi.proposeEdit.mockResolvedValue(proposal)
    mockedApi.applyProposal.mockResolvedValue({})
    const { onDocumentUpdated } = renderPanel({ report })
    const user = userEvent.setup()

    await clickAsync(user, screen.getByRole('button', { name: 'Fix with AI' }))
    expect(mockedApi.proposeEdit).toHaveBeenCalledWith('doc-1', {
      operation: 'fix_grammar',
      target_type: 'section',
      section_id: 'section-1',
    })

    await clickAsync(user, await screen.findByRole('button', { name: 'Accept change' }))

    await waitFor(() => expect(mockedApi.applyProposal).toHaveBeenCalledWith('proposal-1'))
    await waitFor(() => expect(onDocumentUpdated).toHaveBeenCalled())
  })

  it('keeps the proposal open when applying fails', async () => {
    const report = makeReport([makeFinding()])
    mockedApi.proposeEdit.mockResolvedValue(makeProposal())
    mockedApi.applyProposal.mockRejectedValue(new Error('The text changed since this suggestion was made'))
    renderPanel({ report })
    const user = userEvent.setup()

    await clickAsync(user, screen.getByRole('button', { name: 'Fix with AI' }))
    await clickAsync(user, await screen.findByRole('button', { name: 'Accept change' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The text changed since this suggestion was made',
    )
    expect(screen.getByRole('button', { name: 'Accept change' })).toBeInTheDocument()
  })

  it('shows an empty state before any review has run', () => {
    renderPanel()
    expect(screen.getByText('No review yet')).toBeInTheDocument()
  })
})

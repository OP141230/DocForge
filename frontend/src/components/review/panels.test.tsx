import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { clickAsync } from '../../test/act'
import CompliancePanel from './CompliancePanel'
import VersionHistoryPanel from './VersionHistoryPanel'
import { api } from '../../api/client'
import { makeCompliance, makeVersion } from '../../test/fixtures'

vi.mock('../../api/client', () => ({
  api: {
    checkCompliance: vi.fn(),
    compareVersions: vi.fn(),
    restoreVersionSnapshot: vi.fn(),
  },
}))

const mockedApi = api as unknown as {
  checkCompliance: ReturnType<typeof vi.fn>
  compareVersions: ReturnType<typeof vi.fn>
  restoreVersionSnapshot: ReturnType<typeof vi.fn>
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('CompliancePanel', () => {
  it('runs a check and shows requirement statuses with their method', async () => {
    mockedApi.checkCompliance.mockResolvedValue(makeCompliance())
    const onReportChange = vi.fn()
    const { rerender } = render(
      <CompliancePanel documentId="doc-1" report={null} onReportChange={onReportChange} />,
    )
    const user = userEvent.setup()

    await clickAsync(user, screen.getByRole('button', { name: 'Check compliance' }))

    expect(mockedApi.checkCompliance).toHaveBeenCalledWith('doc-1')
    await waitFor(() => expect(onReportChange).toHaveBeenCalled())

    rerender(<CompliancePanel documentId="doc-1" report={makeCompliance()} onReportChange={onReportChange} />)
    expect(screen.getByTestId('compliance-overall')).toHaveTextContent('Partially Met')
    expect(screen.getByText('Word count between 500 and 1200')).toBeInTheDocument()
    expect(screen.getByText('Include a risk assessment section')).toBeInTheDocument()
    expect(screen.getAllByText('Measured automatically')).toHaveLength(2)
    expect(screen.getByText(/Add a section titled/)).toBeInTheDocument()
  })

  it('explains that an unlinked document has nothing to check', () => {
    render(
      <CompliancePanel
        documentId="doc-1"
        report={makeCompliance({ brief_id: null, brief_title: null, results: [], overall: 'not_applicable' })}
        onReportChange={vi.fn()}
      />,
    )
    expect(screen.getByText(/not linked to a brief/)).toBeInTheDocument()
    expect(screen.getByTestId('compliance-overall')).toHaveTextContent('Not Applicable')
  })

  it('surfaces a failed check', async () => {
    mockedApi.checkCompliance.mockRejectedValue(new Error('No brief for this document'))
    render(<CompliancePanel documentId="doc-1" report={null} onReportChange={vi.fn()} />)
    const user = userEvent.setup()

    await clickAsync(user, screen.getByRole('button', { name: 'Check compliance' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('No brief for this document')
  })
})

describe('VersionHistoryPanel', () => {
  const versions = [
    makeVersion({ version_number: 1, origin: 'manual', summary: 'Initial draft' }),
    makeVersion({ version_number: 2, origin: 'ai_accepted', summary: 'Clarified introduction', word_count: 861 }),
  ]

  it('lists versions with origin and word counts', () => {
    render(
      <VersionHistoryPanel
        documentId="doc-1"
        versions={versions}
        onReload={vi.fn()}
        onRefreshVersions={vi.fn()}
      />,
    )
    expect(screen.getByText('v1')).toBeInTheDocument()
    expect(screen.getByText('v2')).toBeInTheDocument()
    expect(screen.getByText('AI-assisted')).toBeInTheDocument()
    expect(screen.getByText('861 words')).toBeInTheDocument()
  })

  it('requires confirmation before restoring, then reloads', async () => {
    mockedApi.restoreVersionSnapshot.mockResolvedValue({})
    const onReload = vi.fn()
    const onRefreshVersions = vi.fn()
    render(
      <VersionHistoryPanel
        documentId="doc-1"
        versions={versions}
        onReload={onReload}
        onRefreshVersions={onRefreshVersions}
      />,
    )
    const user = userEvent.setup()

    await clickAsync(user, screen.getAllByRole('button', { name: 'Restore' })[0])
    expect(mockedApi.restoreVersionSnapshot).not.toHaveBeenCalled()

    await clickAsync(user, screen.getByRole('button', { name: 'Yes, restore' }))

    expect(mockedApi.restoreVersionSnapshot).toHaveBeenCalledWith('doc-1', 1)
    await waitFor(() => expect(onReload).toHaveBeenCalled())
    await waitFor(() => expect(onRefreshVersions).toHaveBeenCalled())
  })

  it('compares two selected versions', async () => {
    mockedApi.compareVersions.mockResolvedValue({
      document_id: 'doc-1',
      from_version: 1,
      to_version: 2,
      from_title: 'Audit',
      to_title: 'Audit',
      from_word_count: 840,
      to_word_count: 861,
      diff: ['--- v1', '+++ v2', '-old line', '+new line'],
      changed_sections: ['Introduction'],
    })
    render(
      <VersionHistoryPanel
        documentId="doc-1"
        versions={versions}
        onReload={vi.fn()}
        onRefreshVersions={vi.fn()}
      />,
    )
    const user = userEvent.setup()

    await clickAsync(user, screen.getByRole('button', { name: 'Use version 1 as comparison base' }))
    await clickAsync(user, screen.getByRole('button', { name: 'Use version 2 as comparison target' }))
    await clickAsync(user, screen.getByRole('button', { name: 'Compare' }))

    expect(mockedApi.compareVersions).toHaveBeenCalledWith('doc-1', 1, 2)
    expect(await screen.findByText('-old line')).toBeInTheDocument()
    expect(screen.getByText('+new line')).toBeInTheDocument()
    expect(screen.getByText(/changed: Introduction/)).toBeInTheDocument()
  })

  it('shows an empty state when nothing has been versioned', () => {
    render(
      <VersionHistoryPanel
        documentId="doc-1"
        versions={[]}
        onReload={vi.fn()}
        onRefreshVersions={vi.fn()}
      />,
    )
    expect(screen.getByText('No versions yet')).toBeInTheDocument()
  })
})

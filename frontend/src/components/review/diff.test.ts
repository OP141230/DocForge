import { describe, expect, it } from 'vitest'
import { diffWords, isTrivialChange } from './diff'

describe('diffWords', () => {
  it('marks identical text as fully equal', () => {
    const segments = diffWords('The auditor reviews the policy.', 'The auditor reviews the policy.')
    expect(segments).toHaveLength(1)
    expect(segments[0].op).toBe('equal')
  })

  it('detects a replaced word', () => {
    const segments = diffWords('The policy is bad.', 'The policy is sound.')
    const removed = segments.filter((segment) => segment.op === 'removed').map((s) => s.text).join('')
    const added = segments.filter((segment) => segment.op === 'added').map((s) => s.text).join('')
    expect(removed.trim()).toBe('bad.')
    expect(added.trim()).toBe('sound.')
  })

  it('reconstructs both sides from the segments', () => {
    const before = 'One two three four five.'
    const after = 'One three four five six.'
    const segments = diffWords(before, after)
    const left = segments.filter((s) => s.op !== 'added').map((s) => s.text).join('')
    const right = segments.filter((s) => s.op !== 'removed').map((s) => s.text).join('')
    expect(left).toBe(before)
    expect(right).toBe(after)
  })

  it('handles empty input without throwing', () => {
    expect(diffWords('', '')).toEqual([])
    expect(diffWords('', 'new text')[0].op).toBe('added')
  })

  it('falls back to whole-text replacement for very long passages', () => {
    const before = Array.from({ length: 1500 }, (_, i) => `w${i}`).join(' ')
    const after = Array.from({ length: 1500 }, (_, i) => `x${i}`).join(' ')
    const segments = diffWords(before, after)
    expect(segments.map((segment) => segment.op)).toEqual(['removed', 'added'])
  })
})

describe('isTrivialChange', () => {
  it('flags case and whitespace-only differences', () => {
    expect(isTrivialChange('the policy.', 'The  policy.')).toBe(true)
  })

  it('does not flag real edits', () => {
    expect(isTrivialChange('the policy.', 'the standard.')).toBe(false)
  })
})

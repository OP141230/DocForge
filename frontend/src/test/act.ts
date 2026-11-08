import { act } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'

/**
 * Click an element whose handler is async, and let the handler's whole promise
 * chain settle inside a single act() scope.
 *
 * Awaiting user.click() and flushing afterwards is not enough: the awaited API
 * call resumes (and calls setLoading(false)) in a microtask that runs before the
 * next line of the test, i.e. outside act(). Nesting the click keeps every
 * update attributed to act(), which is what React requires.
 */
export async function clickAsync(user: UserEvent, element: Element) {
  await act(async () => {
    await user.click(element)
    await new Promise((resolve) => setTimeout(resolve, 0))
  })
}

/** Same containment for <select> changes. */
export async function selectAsync(user: UserEvent, element: Element, value: string) {
  await act(async () => {
    await user.selectOptions(element, value)
    await new Promise((resolve) => setTimeout(resolve, 0))
  })
}

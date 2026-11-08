import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Unmount between tests so queries never match leftovers from a previous render.
afterEach(() => {
  cleanup()
})

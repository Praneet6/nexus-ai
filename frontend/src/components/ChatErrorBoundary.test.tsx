import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ChatErrorBoundary } from './ChatErrorBoundary'

const ThrowError = () => {
  throw new Error('Test Error')
  return null
}

describe('ChatErrorBoundary', () => {
  it('renders children when there is no error', () => {
    render(
      <ChatErrorBoundary>
        <div>Safe Content</div>
      </ChatErrorBoundary>
    )
    expect(screen.getByText('Safe Content')).toBeInTheDocument()
  })

  it('renders error message and "Reload chat" button when an error is caught', () => {
    // Suppress console.error for this test
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <ChatErrorBoundary>
        <ThrowError />
      </ChatErrorBoundary>
    )

    expect(screen.getByText('Chat failed to load')).toBeInTheDocument()
    expect(screen.getByText('Test Error')).toBeInTheDocument()
    expect(screen.getByText('Reload chat')).toBeInTheDocument()

    consoleError.mockRestore()
  })
})

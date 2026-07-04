import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { StyleMirror } from './StyleMirror'
import { useChatStore } from '../store/chatStore'

vi.mock('../store/chatStore')

describe('StyleMirror', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('is hidden when styleProfile is null', () => {
    vi.mocked(useChatStore).mockImplementation((selector: any) => {
      const state = { styleProfile: null }
      return selector(state)
    })

    const { container } = render(<StyleMirror />)
    expect(container.firstChild).toBeNull()
  })

  it('shows chips for non-default traits', () => {
    vi.mocked(useChatStore).mockImplementation((selector: any) => {
      const state = {
        styleProfile: {
          formality: 'formal',
          verbosity: 'verbose',
          punctuation: 'standard',
          emotional_tone: 'neutral',
          vocab_grade: 'high'
        }
      }
      return selector(state)
    })

    render(<StyleMirror />)
    expect(screen.getByText('Style Mirror')).toBeInTheDocument()
    expect(screen.getByText('formal')).toBeInTheDocument()
    expect(screen.getByText('verbose')).toBeInTheDocument()
    expect(screen.queryByText('neutral')).not.toBeInTheDocument()
  })
})

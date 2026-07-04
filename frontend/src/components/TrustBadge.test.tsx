import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { TrustBadge } from './TrustBadge'
import { useChatStore } from '../store/chatStore'

vi.mock('../store/chatStore')

describe('TrustBadge', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders correct color/label for score 100', () => {
    vi.mocked(useChatStore).mockImplementation((selector: any) => {
      const state = { trustBalance: 100, trustHealth: 'excellent', trustCredit: null }
      return selector(state)
    })

    render(<TrustBadge />)
    expect(screen.getByText('100')).toHaveClass('text-emerald-400')
    expect(screen.getByText('excellent')).toBeInTheDocument()
  })

  it('renders correct color/label for score 50', () => {
    vi.mocked(useChatStore).mockImplementation((selector: any) => {
      const state = { trustBalance: 50, trustHealth: 'at_risk', trustCredit: null }
      return selector(state)
    })

    render(<TrustBadge />)
    expect(screen.getByText('50')).toHaveClass('text-amber-400')
    expect(screen.getByText('at risk')).toBeInTheDocument()
  })

  it('renders correct color/label for score 0', () => {
    vi.mocked(useChatStore).mockImplementation((selector: any) => {
      const state = { trustBalance: 0, trustHealth: 'critical', trustCredit: null }
      return selector(state)
    })

    render(<TrustBadge />)
    expect(screen.getByText('0')).toHaveClass('text-red-400')
    expect(screen.getByText('critical')).toBeInTheDocument()
  })
})

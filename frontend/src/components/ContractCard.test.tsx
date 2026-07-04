import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ContractCard } from './ContractCard'
import { useChatStore } from '../store/chatStore'

vi.mock('../store/chatStore')

describe('ContractCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('is hidden when contract is null', () => {
    vi.mocked(useChatStore).mockImplementation((selector: any) => {
      const state = { contract: null }
      return selector(state)
    })

    const { container } = render(<ContractCard />)
    expect(container.firstChild).toBeNull()
  })

  it('renders action items when populated', () => {
    vi.mocked(useChatStore).mockImplementation((selector: any) => {
      const state = {
        contract: {
          session_id: '123',
          proposed_plan: 'Do something',
          status: 'proposed',
          steps: [
            { id: 1, description: 'Test step 1', status: 'pending' },
            { id: 2, description: 'Test step 2', status: 'in_progress' }
          ]
        }
      }
      return selector(state)
    })

    render(<ContractCard />)
    expect(screen.getByText("Nexus's Plan")).toBeInTheDocument()
    expect(screen.getByText('Step 1: Test step 1')).toBeInTheDocument()
    expect(screen.getByText('Step 2: Test step 2')).toBeInTheDocument()
  })
})

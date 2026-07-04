import { vi } from 'vitest'

let storeState = {
  messages: [],
  sessionId: 'test-session',
  customerId: 'test-customer',
  isConnected: true,
  isTyping: false,
  contract: null,
  silenceState: 'confident',
  trustBalance: 100,
  trustHealth: 'excellent',
  trustCredit: null,
  styleProfile: null,
  collectiveMatchCount: 0,
  token: null,
  customerName: 'Guest',
  customerRole: 'user',
  
  // Actions
  addMessage: vi.fn(),
  appendToLastMessage: vi.fn(),
  setStreaming: vi.fn(),
  setContract: vi.fn(),
  setSilenceState: vi.fn(),
  setTrustBalance: vi.fn(),
  setTrustCredit: vi.fn(),
  setStyleProfile: vi.fn(),
  setConnected: vi.fn(),
  setTyping: vi.fn(),
  setAuth: vi.fn(),
  logout: vi.fn(),
  reset: vi.fn(),
}

export const useChatStore = vi.fn((selector) => {
  if (!selector) return storeState
  return selector(storeState)
}) as any

useChatStore.getState = () => storeState
useChatStore.setState = (newState: any) => {
  storeState = { ...storeState, ...newState }
}

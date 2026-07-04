import { create } from 'zustand'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  silenceState?: string
  isStreaming?: boolean
  timestamp: Date
}

export interface ContractStep {
  id: number
  description: string
  status: 'pending' | 'in_progress' | 'done' | 'failed'
  result?: string
}

export interface Contract {
  session_id: string
  proposed_plan: string
  status: string
  steps: ContractStep[]
  user_amendment?: string
  outcome_report?: string
}

export interface StyleProfile {
  formality: string
  verbosity: string
  punctuation: string
  emotional_tone: string
  vocab_grade: string
}

export interface TrustCredit {
  coupon_code: string
  inr_value: number
  message: string
}

type SilenceState = 'confident' | 'confused' | 'distressed'

interface ChatStore {
  // Core
  messages: Message[]
  sessionId: string
  customerId: string
  isConnected: boolean
  isTyping: boolean

  // Feature states
  contract: Contract | null
  silenceState: SilenceState
  trustBalance: number
  trustHealth: string
  trustCredit: TrustCredit | null
  styleProfile: StyleProfile | null
  collectiveMatchCount: number

  // Auth
  token: string | null
  customerName: string
  customerRole: string

  // Actions
  addMessage: (msg: Omit<Message, 'id' | 'timestamp'>) => void
  appendToLastMessage: (content: string) => void
  setStreaming: (streaming: boolean) => void
  setContract: (c: Contract) => void
  setSilenceState: (s: SilenceState) => void
  setTrustBalance: (b: number, health: string) => void
  setTrustCredit: (c: TrustCredit | null) => void
  setStyleProfile: (p: StyleProfile) => void
  setConnected: (c: boolean) => void
  setTyping: (t: boolean) => void
  setAuth: (token: string, customerId: string, name: string, role?: string) => void
  logout: () => void
  reset: () => void
}

function generateUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  sessionId: localStorage.getItem('nexus_session') || generateUUID(),
  customerId: 'demo-customer',
  isConnected: false,
  isTyping: false,
  contract: null,
  silenceState: 'confident',
  trustBalance: 100,
  trustHealth: 'excellent',
  trustCredit: null,
  styleProfile: null,
  collectiveMatchCount: 0,
  token: localStorage.getItem('nexus_token'),
  customerName: localStorage.getItem('nexus_name') || 'Guest',
  customerRole: localStorage.getItem('nexus_role') || 'user',

  addMessage: (msg) =>
    set((state) => ({
      messages: [
        ...state.messages,
        { ...msg, id: crypto.randomUUID(), timestamp: new Date() },
      ],
    })),

  appendToLastMessage: (content) =>
    set((state) => {
      const msgs = [...state.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, content: last.content + content }
      }
      return { messages: msgs }
    }),

  setStreaming: (streaming) =>
    set((state) => {
      const msgs = [...state.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, isStreaming: streaming }
      }
      return { messages: msgs }
    }),

  setContract: (c) => set({ contract: c }),
  setSilenceState: (s) => set({ silenceState: s }),
  setTrustBalance: (b, health) => set({ trustBalance: b, trustHealth: health }),
  setTrustCredit: (c) => set({ trustCredit: c }),
  setStyleProfile: (p) => set({ styleProfile: p }),
  setConnected: (c) => set({ isConnected: c }),
  setTyping: (t) => set({ isTyping: t }),

  setAuth: (token, customerId, name, role = 'user') => {
    localStorage.setItem('nexus_token', token)
    localStorage.setItem('nexus_name', name)
    localStorage.setItem('nexus_role', role)
    if (!localStorage.getItem('nexus_session')) {
      localStorage.setItem('nexus_session', get().sessionId)
    }
    set({ token, customerId, customerName: name, customerRole: role })
  },

  logout: () => {
    localStorage.removeItem('nexus_token')
    localStorage.removeItem('nexus_name')
    localStorage.removeItem('nexus_role')
    set({ token: null, customerId: 'demo-customer', customerName: 'Guest', customerRole: 'user' })
  },

  reset: () =>
    set({
      messages: [],
      sessionId: generateUUID(),
      contract: null,
      silenceState: 'confident',
      trustBalance: 100,
      trustHealth: 'excellent',
      trustCredit: null,
      styleProfile: null,
    }),
}))

import { useRef, useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Wifi, WifiOff, Zap, Sparkles, Shield, LogOut, Wand2 } from 'lucide-react'
import { useChatStore } from '../store/chatStore'
import { useKeystrokeTracker } from '../hooks/useKeystrokeTracker'
import { useStyleProfile } from '../hooks/useStyleProfile'
import { MessageBubble } from './MessageBubble'
import { ContractCard } from './ContractCard'
import { SilenceIndicator } from './SilenceIndicator'
import { TrustBadge } from './TrustBadge'
import { ReplayViewer } from './ReplayViewer'
import { useNavigate } from 'react-router-dom'
import clsx from 'clsx'
import { StyleMirror } from './StyleMirror'

const QUICK_PROMPTS = [
  'Where is my order?',
  'I need a refund',
  'Reset my password',
  'Apply a discount',
]

type ToastType = { message: string; type: 'info' | 'success' | 'error' } | null;

interface ChatWindowProps {
  sendMessage: (content: string, keydata?: object[]) => boolean;
  toast: ToastType;
}

export function ChatWindow({ sendMessage, toast }: ChatWindowProps) {
  const messages = useChatStore((s) => s.messages)
  const isConnected = useChatStore((s) => s.isConnected)
  const isTyping = useChatStore((s) => s.isTyping)
  const contract = useChatStore((s) => s.contract)
  const customerName = useChatStore((s) => s.customerName)
  const logout = useChatStore((s) => s.logout)
  const reset = useChatStore((s) => s.reset)

  const navigate = useNavigate()

  const [input, setInput] = useState('')
  const [inputActive, setInputActive] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const { flushEvents } = useKeystrokeTracker(inputActive)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(() => {
    const text = input.trim()
    if (!text || isTyping) return

    const keydata = flushEvents()
    const sent = sendMessage(text, keydata)
    if (sent) setInput('')
  }, [input, isTyping, flushEvents, sendMessage])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleQuickPrompt = (prompt: string) => {
    const sent = sendMessage(prompt, [])
    if (sent) setInput('')
  }

  return (
    <div className="flex h-screen bg-transparent overflow-hidden relative">
      {/* Toast Notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -20, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: -20, x: '-50%' }}
            className={clsx(
              "absolute top-6 left-1/2 z-50 px-4 py-2 rounded-xl text-sm font-medium shadow-lg backdrop-blur-md border",
              toast.type === 'error' ? 'bg-red-500/10 border-red-500/20 text-red-400' :
              toast.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
              'bg-amber-500/10 border-amber-500/20 text-amber-400'
            )}
          >
            {toast.message}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Left sidebar ────────────────────────────────────────────── */}
      <div className="hidden lg:flex flex-col w-72 flex-shrink-0 p-4 gap-4 border-r border-white/5 overflow-y-auto">
        {/* Brand */}
        <div className="flex items-center gap-3 px-1 py-2">
          <div className="w-10 h-10 rounded-2xl nexus-gradient flex items-center justify-center nexus-glow">
            <Zap size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold gradient-text">Nexus AI</h1>
            <p className="text-xs text-gray-500">Customer Care</p>
          </div>
        </div>

        {/* Connection status */}
        <div className={clsx(
          'flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium border',
          isConnected
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
            : 'bg-red-500/10 border-red-500/20 text-red-400'
        )}>
          {isConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
          {isConnected ? 'Connected' : 'Reconnecting...'}
        </div>

        {/* F02 Silence Indicator */}
        <SilenceIndicator />

        {/* F04 Style Mirror */}
        <StyleMirror />

        {/* F06 Trust Badge */}
        <TrustBadge />

        {/* F01 Contract */}
        {contract && <ContractCard />}

        {/* F03 Replay */}
        <ReplayViewer />

        {/* Navigation & Actions */}
        <div className="flex flex-col gap-1.5 mt-2">
          <button
            onClick={() => navigate('/admin')}
            className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium text-gray-400 hover:text-white hover:bg-white/5 border border-transparent hover:border-white/10 transition-all duration-200"
          >
            <Shield size={13} />
            Admin Dashboard
          </button>
          <button
            onClick={() => {
              logout()
              reset()
              navigate('/login')
            }}
            className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium text-red-400/80 hover:text-red-400 hover:bg-red-500/5 border border-transparent hover:border-red-500/10 transition-all duration-200"
          >
            <LogOut size={13} />
            Sign Out
          </button>
        </div>

        {/* Session info */}
        <div className="mt-auto pt-4 border-t border-white/5">
          <p className="text-xs text-gray-600">Logged in as</p>
          <p className="text-sm text-gray-400 font-medium mt-0.5">{customerName}</p>
        </div>
      </div>

      {/* ── Main chat area ────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar (mobile) */}
        <div className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-white/5 bg-gray-950/80 backdrop-blur-md z-30">
          <div className="w-8 h-8 rounded-xl nexus-gradient flex items-center justify-center">
            <Zap size={16} className="text-white" />
          </div>
          <span className="font-semibold text-white text-sm">Nexus AI</span>
          <div className="ml-auto flex items-center gap-2">
            <SilenceIndicator />
            <button
              onClick={() => navigate('/admin')}
              className="p-2 rounded-xl bg-white/5 text-gray-400 hover:text-white border border-white/5 transition-all"
              title="Admin Dashboard"
            >
              <Shield size={13} />
            </button>
            <button
              onClick={() => {
                logout()
                reset()
                navigate('/login')
              }}
              className="p-2 rounded-xl bg-red-500/5 text-red-400/80 hover:text-red-400 border border-red-500/10 transition-all"
              title="Sign Out"
            >
              <LogOut size={13} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {/* Empty state */}
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center h-full gap-6 text-center"
            >
              <div className="w-20 h-20 rounded-3xl nexus-gradient flex items-center justify-center nexus-glow">
                <Sparkles size={36} className="text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold gradient-text mb-2">How can I help?</h2>
                <p className="text-gray-500 text-sm max-w-xs">
                  I read between the lines — your words, your hesitation, your style. Let's solve this together.
                </p>
              </div>

              {/* Feature pills */}
              <div className="flex flex-wrap gap-2 justify-center max-w-sm">
                {[
                  { label: 'Transparent Plans', icon: '📋' },
                  { label: 'Reads Hesitation', icon: '🧠' },
                  { label: 'Full Audit Trail', icon: '🔍' },
                  { label: 'Adapts to You', icon: '🪞' },
                  { label: 'Learns from All', icon: '🌐' },
                  { label: 'Pays When It Fails', icon: '🎁' },
                ].map(f => (
                  <span key={f.label} className="badge bg-white/5 border border-white/10 text-gray-400">
                    {f.icon} {f.label}
                  </span>
                ))}
              </div>

              {/* Quick prompts */}
              <div className="grid grid-cols-2 gap-2 w-full max-w-sm">
                {QUICK_PROMPTS.map(p => (
                  <button
                    key={p}
                    onClick={() => handleQuickPrompt(p)}
                    className="text-xs text-left p-3 rounded-xl glass border border-white/5
                               hover:border-nexus-500/30 hover:bg-nexus-600/5
                               text-gray-300 hover:text-white transition-all duration-200"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Message list */}
          <AnimatePresence>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </AnimatePresence>

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="px-4 pb-4 pt-2 border-t border-white/5">
          {/* Mobile: quick feature indicators */}
          <div className="lg:hidden flex gap-2 mb-2 overflow-x-auto pb-1">
            <SilenceIndicator />
          </div>

          <div className={clsx(
            'flex items-end gap-3 p-3 rounded-2xl border transition-all duration-200',
            inputActive
              ? 'border-nexus-500/50 bg-white/5 nexus-glow'
              : 'border-white/10 bg-white/3'
          )}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setInputActive(true)}
              onBlur={() => setInputActive(false)}
              placeholder="Type your message... (Shift+Enter for new line)"
              rows={1}
              className="flex-1 bg-transparent text-white placeholder-gray-600 text-sm
                         resize-none outline-none leading-relaxed max-h-32 min-h-[24px]"
              style={{ scrollbarWidth: 'none' }}
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSend}
              disabled={!input.trim() || isTyping || !isConnected}
              className={clsx(
                'flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200',
                input.trim() && !isTyping && isConnected
                  ? 'bg-nexus-600 hover:bg-nexus-500 text-white shadow-lg shadow-nexus-900/40'
                  : 'bg-white/5 text-gray-600 cursor-not-allowed'
              )}
            >
              <Send size={15} />
            </motion.button>
          </div>

          <p className="text-center text-xs text-gray-700 mt-2">
            Nexus AI · Transparency by design
          </p>
        </div>
      </div>
    </div>
  )
}

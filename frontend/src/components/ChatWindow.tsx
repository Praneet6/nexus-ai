import { useRef, useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Wifi, WifiOff, Shield, LogOut, Wand2, Activity, ClipboardList, History, ChevronDown, ChevronRight, Mic, TrendingUp, AlertTriangle } from 'lucide-react'
import { useChatStore } from '../store/chatStore'
import { useKeystrokeTracker } from '../hooks/useKeystrokeTracker'
import { MessageBubble } from './MessageBubble'
import { ContractCard } from './ContractCard'
import { SilenceIndicator } from './SilenceIndicator'
import { TrustBadge } from './TrustBadge'
import { ReplayViewer } from './ReplayViewer'
import { SentimentTimeline } from './SentimentTimeline'
import { useNavigate } from 'react-router-dom'
import clsx from 'clsx'
import { StyleMirror } from './StyleMirror'

const SUGGESTIONS = [
  'Track my order 📦',
  'Request a refund 💳',
  'Report an issue 🔧',
  'Talk to an agent 👤',
]

type ToastType = { message: string; type: 'info' | 'success' | 'error' } | null;

interface ChatWindowProps {
  sendMessage: (content: string, keydata?: object[]) => boolean;
  toast: ToastType;
}

function CollapsibleSection({ title, icon: Icon, defaultOpen = false, children }: { title: string, icon: any, defaultOpen?: boolean, children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  
  return (
    <div className="bg-white rounded-xl shadow-sm border border-surface-border overflow-hidden">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon size={16} className="text-zenta-600" />
          <span className="text-sm font-semibold text-black" style={{ color: 'black' }}>{title}</span>
        </div>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown size={16} className="text-gray-400" />
        </motion.div>
      </button>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-3 border-t border-surface-border bg-white">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export function ChatWindow({ sendMessage, toast }: ChatWindowProps) {
  const messages = useChatStore((s) => s.messages)
  const isConnected = useChatStore((s) => s.isConnected)
  const isTyping = useChatStore((s) => s.isTyping)
  const contract = useChatStore((s) => s.contract)
  const customerName = useChatStore((s) => s.customerName)
  const trustBalance = useChatStore((s) => s.trustBalance)
  const logout = useChatStore((s) => s.logout)
  const reset = useChatStore((s) => s.reset)
  const addMessage = useChatStore((s) => s.addMessage)

  const navigate = useNavigate()

  const [input, setInput] = useState('')
  const [inputActive, setInputActive] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [escalationShown, setEscalationShown] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const { flushEvents } = useKeystrokeTracker(inputActive)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback((textOverride?: string) => {
    const text = textOverride ?? input.trim()
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

  const handleVoiceInput = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert("Voice not supported")
      return
    }
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-IN'
    recognition.onstart = () => setIsRecording(true)
    recognition.onend = () => setIsRecording(false)
    recognition.onresult = (e: any) => {
      const text = e.results[0][0].transcript
      handleSend(text)
    }
    recognition.start()
  }

  return (
    <div className="flex flex-col h-screen bg-surface overflow-hidden">
      {/* Toast Notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -20, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: -20, x: '-50%' }}
            className={clsx(
              "absolute top-6 left-1/2 z-50 px-4 py-2 rounded-xl text-sm font-medium shadow-lg border bg-white",
              toast.type === 'error' ? 'border-red-200 text-red-600' :
              toast.type === 'success' ? 'border-emerald-200 text-emerald-600' :
              'border-amber-200 text-amber-600'
            )}
          >
            {toast.message}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Header ────────────────────────────────────────────── */}
      <header className="h-[56px] flex-shrink-0 bg-white border-b border-surface-border px-6 flex items-center justify-between z-10">
        <div className="flex items-center">
          <div className="bg-gradient-to-br from-[#2563EB] to-[#1D4ED8] rounded-xl w-10 h-10 flex items-center justify-center shadow-sm">
             <span style={{ fontFamily: 'Georgia, serif', fontStyle: 'italic', fontWeight: 900, fontSize: '1.8rem', color: 'white', lineHeight: 1 }}>Z</span>
          </div>
          <span className="ml-2 text-[#0F172A]" style={{ fontFamily: '"Plus Jakarta Sans", sans-serif', fontWeight: 600, fontSize: '1.5rem', letterSpacing: '-0.025em' }}>Zenta</span>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <motion.div
              animate={{ scale: isConnected ? [1, 1.3, 1] : 1 }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              className={clsx("w-2 h-2 rounded-full", isConnected ? "bg-emerald-500" : "bg-red-500 animate-pulse")}
            />
            <span className="text-xs font-medium text-text-secondary hidden sm:block">
              {isConnected ? 'Connected' : 'Reconnecting...'}
            </span>
          </div>
          <div className="h-4 w-px bg-surface-border mx-2" />
          <span className="text-sm font-medium text-text-primary">{customerName}</span>
          <button
            onClick={() => {
              logout()
              reset()
              navigate('/login')
            }}
            className="text-text-secondary hover:text-zenta-600 transition-colors p-1"
            title="Sign Out"
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* ── Left sidebar ────────────────────────────────────────────── */}
        <div 
          className="hidden lg:flex flex-col w-[280px] flex-shrink-0 bg-sidebar border-r border-surface-border p-4 gap-2 overflow-y-auto h-full"
          style={{ scrollbarWidth: 'thin', scrollbarColor: '#E2E8F0 transparent' }}
        >
          <CollapsibleSection title="Service Score" icon={Shield} defaultOpen={true}>
            <TrustBadge />
          </CollapsibleSection>
          
          <CollapsibleSection title="Silence Indicator" icon={Activity}>
            <SilenceIndicator />
          </CollapsibleSection>

          <CollapsibleSection title="Sentiment Timeline" icon={TrendingUp} defaultOpen={false}>
            <SentimentTimeline />
          </CollapsibleSection>
          
          <CollapsibleSection title="Style Mirror" icon={Wand2}>
            <StyleMirror />
          </CollapsibleSection>
          
          {contract && (
            <CollapsibleSection title="Contract" icon={ClipboardList}>
              <ContractCard />
            </CollapsibleSection>
          )}
          
          <CollapsibleSection title="Replay Viewer" icon={History}>
            <ReplayViewer />
          </CollapsibleSection>

          {/* Admin Navigation */}
          <div className="mt-auto pt-4">
            <button
              onClick={() => navigate('/admin')}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-sm font-medium text-text-secondary hover:text-zenta-600 hover:bg-white border border-transparent hover:border-surface-border transition-all duration-200 shadow-sm"
            >
              <Shield size={16} />
              Admin Dashboard
            </button>
          </div>
        </div>

        {/* ── Main chat area ────────────────────────────────────────────── */}
        <div className="flex-1 flex flex-col min-w-0 bg-white relative"
             style={{ backgroundImage: 'radial-gradient(circle, #e2e8f0 1px, transparent 1px)', backgroundSize: '24px 24px' }}>
          
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 sm:px-8 py-6 space-y-4">
            <AnimatePresence>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="px-4 sm:px-8 pb-6 pt-2 bg-white">
            
            {/* Empty State */}
            {messages.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center justify-center mb-8 mt-12 gap-4 text-center"
              >
                <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-[#2563EB] to-[#1D4ED8] flex items-center justify-center shadow-md animate-pulse">
                  <span style={{ fontFamily: 'Georgia, serif', fontStyle: 'italic', fontWeight: 900, fontSize: '3rem', color: 'white', lineHeight: 1 }}>Z</span>
                </div>
                <div>
                  <h2 className="text-[28px] font-bold text-[#0F172A]">Hi, I'm Zenta</h2>
                  <p className="text-[#64748B] text-[16px] max-w-sm mt-2 mx-auto">
                    Your intelligent customer care assistant.<br/>How can I help you today?
                  </p>
                </div>
              </motion.div>
            )}

            {/* Chat Suggestions */}
            {messages.length === 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {SUGGESTIONS.map((sugg, i) => (
                  <motion.button
                    key={sugg}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1, duration: 0.3 }}
                    onClick={() => handleSend(sugg)}
                    className="px-4 py-1.5 rounded-full bg-white border border-zenta-600 text-zenta-600 text-sm font-medium hover:bg-zenta-50 hover:scale-105 transition-all duration-200 shadow-sm"
                  >
                    {sugg}
                  </motion.button>
                ))}
              </div>
            )}

            {/* Smart Escalation Banner */}
            {!escalationShown && trustBalance < 60 && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4 shadow-sm flex flex-col gap-3">
                <div className="flex items-center gap-2 text-amber-800 font-medium text-sm">
                  <AlertTriangle size={16} />
                  ⚠️ We notice you're having a tough time. Would you like to speak with a human agent?
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setEscalationShown(true)
                      sendMessage("Escalating to human agent...")
                      addMessage({
                        role: 'assistant',
                        content: `**Escalation Initiated**\n\nA human agent will contact you within 2 minutes.\nReference ID: ZEN-${Math.floor(1000 + Math.random() * 9000)}`
                      })
                    }}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-colors"
                  >
                    Yes, connect me
                  </button>
                  <button
                    onClick={() => setEscalationShown(true)}
                    className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-1.5 rounded-lg text-sm font-medium transition-colors"
                  >
                    No, continue
                  </button>
                </div>
              </div>
            )}

            <div className={clsx(
              'flex items-end gap-3 p-3 rounded-2xl border transition-all duration-200 bg-white shadow-sm',
              inputActive
                ? 'border-[#E2E8F0] ring-2 ring-zenta-500/20'
                : 'border-[#E2E8F0]'
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
                className="flex-1 bg-transparent text-text-primary placeholder-gray-400 text-sm
                           resize-none outline-none leading-relaxed max-h-32 min-h-[24px]"
                style={{ scrollbarWidth: 'none' }}
              />
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleVoiceInput}
                title={isRecording ? "Listening..." : "Use Voice Input"}
                className={clsx(
                  'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 shadow-sm',
                  isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                )}
              >
                <Mic size={18} />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => handleSend()}
                disabled={!input.trim() || isTyping || !isConnected}
                className={clsx(
                  'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 shadow-sm',
                  input.trim() && !isTyping && isConnected
                    ? 'bg-zenta-600 hover:bg-zenta-700 text-white'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                )}
              >
                <Send size={18} />
              </motion.button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

import React from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw, Zap } from 'lucide-react'
import { ChatWindow } from '../components/ChatWindow'
import { useChatStore } from '../store/chatStore'

import { ChatErrorBoundary } from '../components/ChatErrorBoundary'
import { useWebSocket } from '../hooks/useWebSocket'
// ── Connection skeleton ───────────────────────────────────────────────────────

function ConnectionSkeleton() {
  return (
    <div className="flex h-screen items-center justify-center bg-transparent">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col items-center gap-5"
      >
        {/* Animated logo */}
        <motion.div
          animate={{ scale: [1, 1.08, 1], opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className="w-16 h-16 rounded-xl bg-gradient-to-br from-[#2563EB] to-[#1D4ED8] flex items-center justify-center shadow-md"
        >
          <span style={{ fontFamily: 'Georgia, serif', fontStyle: 'italic', fontWeight: 900, fontSize: '3rem', color: 'white', lineHeight: 1 }}>Z</span>
        </motion.div>

        {/* Skeleton bars */}
        <div className="space-y-2 w-56">
          {[80, 56, 72].map((w, i) => (
            <motion.div
              key={i}
              className="h-2.5 rounded-full bg-surface-border"
              style={{ width: `${w}%` }}
              animate={{ opacity: [0.4, 0.8, 0.4] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
            />
          ))}
        </div>

        <p className="text-xs text-text-secondary tracking-wide">Connecting to Zenta…</p>
      </motion.div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

function ChatInner() {
  const isConnected = useChatStore((s) => s.isConnected)
  const messages = useChatStore((s) => s.messages)
  const { sendMessage, toast } = useWebSocket()

  // Show skeleton only on the very first connection attempt — once we've
  // received any message or connected, never show it again.
  const [seenConnected, setSeenConnected] = React.useState(false)
  const [hasTimedOut, setHasTimedOut] = React.useState(false)

  React.useEffect(() => {
    if (isConnected || messages.length > 0) setSeenConnected(true)
  }, [isConnected, messages.length])

  React.useEffect(() => {
    if (seenConnected) return
    const timer = setTimeout(() => {
      if (!isConnected) {
        setHasTimedOut(true)
      }
    }, 10000)
    return () => clearTimeout(timer)
  }, [seenConnected, isConnected])

  if (!seenConnected && !isConnected) {
    if (hasTimedOut) {
      return (
        <div className="flex h-screen items-center justify-center bg-transparent">
          <div className="flex flex-col items-center gap-5">
            <div className="w-16 h-16 rounded-3xl bg-red-500/10 flex items-center justify-center border border-red-500/20">
              <AlertTriangle size={28} className="text-red-400" />
            </div>
            <p className="text-sm text-red-400 font-medium">Connection failed</p>
            <button
              onClick={() => window.location.reload()}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white text-sm transition-all"
            >
              <RefreshCw size={14} /> Retry
            </button>
          </div>
        </div>
      )
    }
    return <ConnectionSkeleton />
  }

  return <ChatWindow sendMessage={sendMessage} toast={toast} />
}

export default function Chat() {
  return (
    <ChatErrorBoundary>
      <ChatInner />
    </ChatErrorBoundary>
  )
}

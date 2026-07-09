import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { Message } from '../store/chatStore'
import { Bot, User } from 'lucide-react'
import clsx from 'clsx'

interface Props {
  message: Message
}

const EMOJIS = ['👍', '❤️', '😮', '😢', '🎉']

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  const isStreaming = message.isStreaming
  const [reaction, setReaction] = useState<string | null>(null)

  return (
    <motion.div
      initial={{ opacity: 0, x: isUser ? 20 : -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={clsx('flex gap-3 group relative', isUser ? 'flex-row-reverse' : 'flex-row')}
    >
      {/* Avatar */}
      <div className={clsx(
        'flex-shrink-0 flex items-center justify-center mt-1 shadow-sm',
        isUser
          ? 'bg-zenta-600 w-8 h-8 rounded-full'
          : 'bg-gradient-to-br from-[#2563EB] to-[#1D4ED8] w-8 h-8 rounded-xl',
        !isUser && isStreaming && !message.content ? 'animate-pulse' : ''
      )}>
        {isUser
          ? <User size={16} className="text-white" />
          : <span style={{ fontFamily: 'Georgia, serif', fontStyle: 'italic', fontWeight: 900, fontSize: '1.2rem', color: 'white', lineHeight: 1 }}>Z</span>
        }
      </div>

      {/* Bubble */}
      <div className="flex flex-col relative max-w-[75%]">
        <div className={clsx(
          'px-4 py-3 rounded-2xl text-sm leading-relaxed relative shadow-sm',
          isUser
            ? 'bg-[#EFF6FF] text-[#0F172A] rounded-tr-sm'
            : 'bg-sidebar text-text-primary rounded-tl-sm',
          !isStreaming && !isUser && message.content ? 'animate-message-pulse' : ''
        )}>
          {message.content || isStreaming ? (
            <div className="prose prose-sm max-w-none">
              {message.content && <ReactMarkdown>{message.content}</ReactMarkdown>}
              {!message.content && isStreaming && <TypingDots />}
              {isStreaming && message.content && (
                <motion.span
                  animate={{ opacity: [1, 0, 1] }}
                  transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
                  className="inline-block w-[3px] h-[1em] bg-zenta-600 align-middle ml-1"
                />
              )}
            </div>
          ) : null}

          {/* Floating Emoji */}
          <AnimatePresence>
            {reaction && (
              <motion.div
                initial={{ opacity: 0, y: 0, scale: 1 }}
                animate={{ opacity: 1, y: -60, scale: [1, 1.5, 0] }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                onAnimationComplete={() => setReaction(null)}
                className="absolute -top-4 right-0 z-20 pointer-events-none text-2xl"
              >
                {reaction}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Reaction Bar (Hover) */}
        {!isUser && !isStreaming && (
          <div className="absolute -top-10 left-4 opacity-0 group-hover:opacity-100 transition-opacity bg-white border border-surface-border rounded-full shadow-md px-2 py-1 flex gap-1 z-10 pointer-events-auto">
            {EMOJIS.map(emoji => (
              <button
                key={emoji}
                onClick={() => setReaction(emoji)}
                className="hover:scale-125 transition-transform p-1 leading-none"
              >
                {emoji}
              </button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}

function TypingDots() {
  return (
    <div className="flex items-center gap-2 py-1">
      <span className="text-sm text-text-secondary font-medium">Zenta is thinking...</span>
      <div className="flex items-center gap-1">
        <div className="w-1.5 h-1.5 rounded-full bg-zenta-600 typing-dot" />
        <div className="w-1.5 h-1.5 rounded-full bg-zenta-600 typing-dot" />
        <div className="w-1.5 h-1.5 rounded-full bg-zenta-600 typing-dot" />
      </div>
    </div>
  )
}

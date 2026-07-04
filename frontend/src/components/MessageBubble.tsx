import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { Message } from '../store/chatStore'
import { Bot, User } from 'lucide-react'
import clsx from 'clsx'

interface Props {
  message: Message
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  const isStreaming = message.isStreaming

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className={clsx('flex gap-3 message-enter', isUser ? 'flex-row-reverse' : 'flex-row')}
    >
      {/* Avatar */}
      <div className={clsx(
        'flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center mt-1',
        isUser
          ? 'bg-nexus-600/30 border border-nexus-500/30'
          : 'bg-gradient-to-br from-nexus-600 to-indigo-600 nexus-glow'
      )}>
        {isUser
          ? <User size={14} className="text-nexus-300" />
          : <Bot size={14} className="text-white" />
        }
      </div>

      {/* Bubble */}
      <div className={clsx(
        'max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed',
        isUser
          ? 'bg-nexus-700/50 border border-nexus-600/30 text-nexus-50 rounded-tr-sm'
          : 'glass text-gray-100 rounded-tl-sm'
      )}>
        {message.content ? (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        ) : isStreaming ? (
          <TypingDots />
        ) : null}

        {isStreaming && message.content && (
          <span className="inline-block w-0.5 h-4 bg-nexus-400 ml-0.5 animate-pulse align-middle" />
        )}
      </div>
    </motion.div>
  )
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1 py-1">
      <div className="w-1.5 h-1.5 rounded-full bg-nexus-400 typing-dot" />
      <div className="w-1.5 h-1.5 rounded-full bg-nexus-400 typing-dot" />
      <div className="w-1.5 h-1.5 rounded-full bg-nexus-400 typing-dot" />
    </div>
  )
}

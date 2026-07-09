import { motion, AnimatePresence } from 'framer-motion'
import { useChatStore } from '../store/chatStore'
import { Brain } from 'lucide-react'
import clsx from 'clsx'

const STATE_CONFIG = {
  confident: {
    label: 'Confident',
    color: 'text-[#2563EB]',
    bg: 'bg-[#2563EB]/10 border-[#2563EB]/20',
    dot: 'bg-[#2563EB]',
    hint: null,
  },
  confused: {
    label: 'Hesitant',
    color: 'text-amber-400',
    bg: 'bg-amber-400/10 border-amber-400/20',
    dot: 'bg-amber-400',
    hint: 'Nexus sensed uncertainty — asking a clarifying question',
  },
  distressed: {
    label: 'Distressed',
    color: 'text-red-400',
    bg: 'bg-red-400/10 border-red-400/20',
    dot: 'bg-red-400',
    hint: 'Nexus sensed difficulty — responding with extra care',
  },
}

export function SilenceIndicator() {
  const silenceState = useChatStore((s) => s.silenceState)
  const config = STATE_CONFIG[silenceState]

  return (
    <div className={clsx(
      'flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-medium transition-all duration-500',
      config.bg
    )}>
      {/* Animated dot */}
      <span className="relative flex h-2 w-2">
        <span className={clsx(
          'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
          config.dot
        )} />
        <span className={clsx('relative inline-flex rounded-full h-2 w-2', config.dot)} />
      </span>

      <Brain size={12} className={config.color} />
      <span className={config.color}>Tone: {config.label}</span>

      <AnimatePresence>
        {config.hint && (
          <motion.span
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: 'auto' }}
            exit={{ opacity: 0, width: 0 }}
            className="text-gray-400 overflow-hidden whitespace-nowrap"
          >
            — {config.hint}
          </motion.span>
        )}
      </AnimatePresence>
    </div>
  )
}

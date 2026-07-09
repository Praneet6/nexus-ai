import React, { useEffect, useState } from 'react'
import { useChatStore } from '../store/chatStore'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'

interface StateEntry {
  id: string;
  time: string;
  state: string;
  message_count: number;
}

export function SentimentTimeline() {
  const silenceState = useChatStore((s) => s.silenceState)
  const messages = useChatStore((s) => s.messages)
  const [history, setHistory] = useState<StateEntry[]>([])

  useEffect(() => {
    setHistory(prev => {
      const last = prev[prev.length - 1]
      if (last && last.state === silenceState) {
        return prev;
      }
      const now = new Date();
      const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const newEntry: StateEntry = {
        id: Math.random().toString(36).substr(2, 9),
        time: timeString,
        state: silenceState,
        message_count: messages.length
      }
      const updated = [...prev, newEntry]
      if (updated.length > 8) return updated.slice(updated.length - 8)
      return updated
    })
  }, [silenceState, messages.length])

  return (
    <div className="flex flex-col gap-2">
      <AnimatePresence>
        {history.map((entry, index) => (
          <motion.div
            key={entry.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-stretch gap-3 text-sm"
          >
            <div className="flex flex-col items-center pt-1.5">
              <div className={clsx(
                "w-2.5 h-2.5 rounded-full shadow-sm flex-shrink-0",
                entry.state === 'confident' ? 'bg-emerald-500' :
                entry.state === 'hesitant' || entry.state === 'confused' ? 'bg-amber-500' :
                'bg-red-500'
              )} />
              {index < history.length - 1 && (
                <div className="w-px h-full bg-surface-border my-1 min-h-[20px]" />
              )}
            </div>
            <div className="flex flex-col pb-3">
              <span className="text-xs text-text-secondary leading-none mb-1">{entry.time} • msg {entry.message_count}</span>
              <span className="font-medium text-text-primary capitalize leading-none">{entry.state}</span>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}

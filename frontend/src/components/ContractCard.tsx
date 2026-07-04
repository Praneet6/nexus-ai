import { motion, AnimatePresence } from 'framer-motion'
import { useChatStore, Contract, ContractStep } from '../store/chatStore'
import { CheckCircle, Circle, Clock, XCircle, FileText, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

const statusIcon = (status: ContractStep['status']) => {
  switch (status) {
    case 'done':       return <CheckCircle size={16} className="text-emerald-400" />
    case 'in_progress':return <Clock size={16} className="text-nexus-400 animate-spin" />
    case 'failed':     return <XCircle size={16} className="text-red-400" />
    default:           return <Circle size={16} className="text-gray-600" />
  }
}

export function ContractCard() {
  const contract = useChatStore((s) => s.contract)
  const [expanded, setExpanded] = useState(true)

  if (!contract) return null

  const statusColors: Record<string, string> = {
    proposed:    'text-amber-400 bg-amber-400/10 border-amber-400/20',
    accepted:    'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    in_progress: 'text-nexus-400 bg-nexus-400/10 border-nexus-400/20',
    completed:   'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    failed:      'text-red-400 bg-red-400/10 border-red-400/20',
    amended:     'text-blue-400 bg-blue-400/10 border-blue-400/20',
  }

  const completedCount = contract.steps.filter(s => s.status === 'done').length

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-4 border-nexus-500/20"
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between gap-2 mb-2"
      >
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-nexus-600/30 flex items-center justify-center">
            <FileText size={14} className="text-nexus-400" />
          </div>
          <span className="text-sm font-semibold text-white">Nexus's Plan</span>
          <span className={clsx(
            'badge border text-xs',
            statusColors[contract.status] || 'text-gray-400 bg-gray-400/10 border-gray-400/20'
          )}>
            {contract.status.replace('_', ' ')}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {contract.steps.length > 0 && (
            <span className="text-xs text-gray-500">{completedCount}/{contract.steps.length}</span>
          )}
          {expanded ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            {/* Progress bar */}
            {contract.steps.length > 0 && (
              <div className="mb-3">
                <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-nexus-600 to-indigo-500 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${(completedCount / contract.steps.length) * 100}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>
            )}

            {/* Steps */}
            <div className="space-y-2">
              {contract.steps.map((step, i) => (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className={clsx(
                    'flex items-start gap-2.5 p-2.5 rounded-xl text-sm transition-colors',
                    step.status === 'in_progress' ? 'bg-nexus-600/10 border border-nexus-500/20' :
                    step.status === 'done'        ? 'bg-emerald-500/5' :
                    step.status === 'failed'      ? 'bg-red-500/5' : ''
                  )}
                >
                  <div className="mt-0.5 flex-shrink-0">{statusIcon(step.status)}</div>
                  <div className="flex-1 min-w-0">
                    <span className={clsx(
                      'font-medium',
                      step.status === 'done'        ? 'text-gray-300 line-through decoration-emerald-500/50' :
                      step.status === 'in_progress' ? 'text-white' :
                      step.status === 'failed'      ? 'text-red-300' : 'text-gray-400'
                    )}>
                      Step {step.id}: {step.description}
                    </span>
                    {step.result && (
                      <p className="text-xs text-gray-500 mt-0.5 truncate">{step.result}</p>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Outcome report */}
            {contract.outcome_report && (
              <div className="mt-3 p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <p className="text-xs text-emerald-300">{contract.outcome_report}</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

import { motion, AnimatePresence } from 'framer-motion'
import { useChatStore } from '../store/chatStore'
import { Shield, AlertTriangle, TrendingDown, Gift, X } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

const HEALTH_CONFIG = {
  excellent: { color: 'text-[#2563EB]', bar: 'bg-[#2563EB]', bg: 'bg-[#2563EB]/10 border-[#2563EB]/20', icon: <Shield size={14} className="text-[#2563EB]" /> },
  good:      { color: 'text-teal-400',    bar: 'from-teal-500 to-teal-400',       bg: 'bg-teal-400/10 border-teal-400/20',       icon: <Shield size={14} className="text-teal-400" /> },
  at_risk:   { color: 'text-amber-400',   bar: 'from-amber-500 to-amber-400',     bg: 'bg-amber-400/10 border-amber-400/20',     icon: <AlertTriangle size={14} className="text-amber-400" /> },
  critical:  { color: 'text-red-400',     bar: 'from-red-600 to-red-400',         bg: 'bg-red-400/10 border-red-400/20',         icon: <TrendingDown size={14} className="text-red-400" /> },
}

export function TrustBadge() {
  const trustBalance = useChatStore((s) => s.trustBalance)
  const trustHealth = useChatStore((s) => s.trustHealth)
  const trustCredit = useChatStore((s) => s.trustCredit)
  const setTrustCredit = useChatStore((s) => s.setTrustCredit)

  const config = HEALTH_CONFIG[trustHealth as keyof typeof HEALTH_CONFIG] || HEALTH_CONFIG.excellent
  const pct = Math.max(0, Math.min(100, trustBalance))

  return (
    <div className="space-y-2">
      {/* Main badge */}
      <div className={clsx('glass-card p-3 border', config.bg)}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {config.icon}
            <span className="text-xs font-semibold text-black" style={{ color: 'black' }}>Service Score</span>
          </div>
          <span className={clsx('text-lg font-bold tabular-nums', config.color)}>
            {trustBalance}
          </span>
        </div>
        <div className="text-[10.5px] text-gray-500 mb-3 leading-tight">
          Zenta's service quality score for this session.<br/>Drops if issues go unresolved or response is delayed.
        </div>

        {/* Bar */}
        <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <motion.div
            className={clsx('h-full rounded-full', config.bar)}
            initial={{ width: '100%' }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </div>

        <div className="flex justify-between mt-1.5">
          <span
            className={clsx('text-xs font-medium capitalize', config.color)}
            title="This score reflects how well Zenta has served you today"
          >
            {trustHealth === 'excellent' ? 'Perfect Session ✨' : trustHealth.replace('_', ' ')}
          </span>
          <span className="text-xs text-gray-600">/ 100</span>
        </div>
      </div>

      {/* Credit notification */}
      <AnimatePresence>
        {trustCredit && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -4 }}
            className="glass-card p-3 border border-[#2563EB]/30 bg-[#2563EB]/5"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-start gap-2">
                <Gift size={14} className="text-[#2563EB] mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-semibold text-[#2563EB]">Credit Issued!</p>
                  <p className="text-xs text-gray-300 mt-0.5">₹{trustCredit.inr_value} credit</p>
                  <code className="text-xs font-mono text-[#2563EB] bg-[#2563EB]/10 px-1.5 py-0.5 rounded mt-1 block">
                    {trustCredit.coupon_code}
                  </code>
                </div>
              </div>
              <button
                onClick={() => setTrustCredit(null)}
                className="text-gray-600 hover:text-gray-400 transition-colors flex-shrink-0"
              >
                <X size={12} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

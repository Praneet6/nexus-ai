import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Shield, Users, TrendingDown, Gift,
  AlertTriangle, BarChart2, RefreshCw, Zap, Lock
} from 'lucide-react'
import clsx from 'clsx'
import { useChatStore } from '../store/chatStore'

interface AdminData {
  avg_trust_balance: number
  at_risk_count: number
  total_credits_issued_inr: number
  top_failure_reasons: { reason: string; count: number }[]
  health: string
}

const HEALTH_COLOR: Record<string, string> = {
  excellent: 'text-emerald-400',
  good: 'text-teal-400',
  at_risk: 'text-amber-400',
  critical: 'text-red-400',
}

const REASON_LABELS: Record<string, string> = {
  escalation_to_human: 'Escalated to Human',
  unresolved_after_3_turns: 'Unresolved (3 turns)',
  wait_over_2_min: 'Long Wait',
  wrong_answer_corrected: 'Wrong Answer',
  session_abandoned: 'Session Abandoned',
}

function StatCard({ icon, label, value, sub, color = 'text-nexus-400' }: {
  icon: React.ReactNode; label: string; value: string | number; sub?: string; color?: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-4"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 mb-1">{label}</p>
          <p className={clsx('text-2xl font-bold tabular-nums', color)}>{value}</p>
          {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
        </div>
        <div className="w-9 h-9 rounded-xl bg-white/5 flex items-center justify-center">
          {icon}
        </div>
      </div>
    </motion.div>
  )
}

export function AdminDashboard() {
  const [data, setData] = useState<AdminData | null>(null)
  const [loading, setLoading] = useState(true)
  const [accessDenied, setAccessDenied] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const token = useChatStore((s) => s.token)

  const load = async () => {
    setLoading(true)
    setAccessDenied(false)
    try {
      const res = await fetch('/api/trust/admin/summary', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (res.status === 403) {
        setAccessDenied(true)
        return
      }
      if (res.ok) {
        const json = await res.json()
        setData(json)
        setLastRefresh(new Date())
      }
    } catch (e) {
      console.error('Admin load failed:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, 30000) // refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const healthColor = data ? HEALTH_COLOR[data.health] || 'text-gray-400' : 'text-gray-400'

  // ── Access denied state ────────────────────────────────────
  if (accessDenied) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center py-32 gap-6 text-center px-6"
      >
        <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
          <Lock size={28} className="text-red-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-red-400 mb-2">Access Denied</h2>
          <p className="text-sm text-gray-500 max-w-xs">
            Your account does not have admin privileges.
            Contact your system administrator to request access.
          </p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/5 border border-red-500/10 text-xs text-red-400 font-mono">
          HTTP 403 Forbidden
        </div>
      </motion.div>
    )
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Admin Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Trust Economy Overview · Last updated {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 btn-ghost text-sm"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {loading && !data ? (
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 rounded-full border-2 border-nexus-500 border-t-transparent animate-spin" />
            <p className="text-sm text-gray-500">Loading dashboard...</p>
          </div>
        </div>
      ) : data ? (
        <>
          {/* Stats grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              icon={<Shield size={18} className={healthColor} />}
              label="Avg Trust Balance"
              value={data.avg_trust_balance.toFixed(1)}
              sub={data.health.replace('_', ' ')}
              color={healthColor}
            />
            <StatCard
              icon={<Users size={18} className="text-amber-400" />}
              label="At-Risk Customers"
              value={data.at_risk_count}
              sub="balance < 60"
              color="text-amber-400"
            />
            <StatCard
              icon={<Gift size={18} className="text-emerald-400" />}
              label="Credits Issued"
              value={`₹${data.total_credits_issued_inr.toLocaleString()}`}
              sub="total compensation"
              color="text-emerald-400"
            />
            <StatCard
              icon={<Zap size={18} className="text-nexus-400" />}
              label="Trust Health"
              value={data.health.replace('_', ' ')}
              sub="system-wide"
              color={healthColor}
            />
          </div>

          {/* Trust health bar */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <BarChart2 size={16} className="text-nexus-400" />
              <h2 className="text-sm font-semibold text-white">System Trust Health</h2>
            </div>
            <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-nexus-600 to-indigo-500"
                initial={{ width: 0 }}
                animate={{ width: `${data.avg_trust_balance}%` }}
                transition={{ duration: 1, ease: 'easeOut' }}
              />
            </div>
            <div className="flex justify-between mt-2 text-xs text-gray-500">
              <span>0 — Critical</span>
              <span className={clsx('font-semibold', healthColor)}>
                {data.avg_trust_balance.toFixed(1)} avg
              </span>
              <span>100 — Excellent</span>
            </div>
          </div>

          {/* Top failure reasons */}
          {data.top_failure_reasons.length > 0 && (
            <div className="glass-card p-5">
              <div className="flex items-center gap-2 mb-4">
                <TrendingDown size={16} className="text-red-400" />
                <h2 className="text-sm font-semibold text-white">Top Failure Reasons</h2>
              </div>
              <div className="space-y-3">
                {data.top_failure_reasons.map((r, i) => {
                  const maxCount = data.top_failure_reasons[0].count
                  const pct = (r.count / maxCount) * 100
                  return (
                    <motion.div
                      key={r.reason}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.07 }}
                      className="space-y-1"
                    >
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-300">
                          {REASON_LABELS[r.reason] || r.reason}
                        </span>
                        <span className="text-gray-500 tabular-nums">{r.count}×</span>
                      </div>
                      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full rounded-full bg-gradient-to-r from-red-600 to-red-400"
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 0.7, delay: i * 0.07 }}
                        />
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Debit rules reference */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle size={16} className="text-amber-400" />
              <h2 className="text-sm font-semibold text-white">Trust Debit Rules</h2>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {[
                ['Escalation to Human', '−20 pts'],
                ['Unresolved after 3 turns', '−10 pts'],
                ['Wait over 2 min', '−5 pts'],
                ['Wrong answer corrected', '−8 pts'],
                ['Session abandoned', '−15 pts'],
              ].map(([rule, pts]) => (
                <div key={rule} className="flex justify-between p-2 rounded-lg bg-white/3">
                  <span className="text-gray-400">{rule}</span>
                  <span className="text-red-400 font-mono font-semibold">{pts}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Credit tiers */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <Gift size={16} className="text-emerald-400" />
              <h2 className="text-sm font-semibold text-white">Auto-Credit Tiers</h2>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {[
                ['0–14 pts debt', 'NEXUS5', '₹50'],
                ['15–29 pts debt', 'NEXUS10', '₹100'],
                ['30–49 pts debt', 'NEXUS20', '₹200'],
                ['50+ pts debt', 'NEXUS50', '₹500'],
              ].map(([range, code, value]) => (
                <div key={range} className="p-2.5 rounded-xl bg-emerald-500/5 border border-emerald-500/10 space-y-0.5">
                  <p className="text-gray-500">{range}</p>
                  <p className="font-mono text-emerald-400 font-semibold">{code}</p>
                  <p className="text-emerald-300 font-bold">{value}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-20 text-gray-500 text-sm">
          Failed to load dashboard. Is the backend running?
        </div>
      )}
    </div>
  )
}

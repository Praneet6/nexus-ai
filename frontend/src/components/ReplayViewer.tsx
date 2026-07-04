import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Download, ChevronDown, ChevronUp, CheckCircle, XCircle, Clock } from 'lucide-react'
import { useChatStore } from '../store/chatStore'
import clsx from 'clsx'

interface TraceStep {
  trace_id: string
  tool_name: string
  tool_input: Record<string, unknown>
  tool_result: Record<string, unknown>
  duration_ms: number
  success: boolean
  timestamp: string
}

const TOOL_LABELS: Record<string, string> = {
  check_order_status: 'Checked order status',
  process_refund: 'Processed refund',
  reset_password: 'Reset password',
  apply_coupon: 'Applied coupon',
  escalate_to_human: 'Escalated to human',
  send_email_confirmation: 'Sent confirmation email',
}

export function ReplayViewer() {
  const sessionId = useChatStore((s) => s.sessionId)
  const [traces, setTraces] = useState<TraceStep[]>([])
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [pdfUrl, setPdfUrl] = useState('')

  const loadReplay = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/replay/${sessionId}`)
      const data = await res.json()
      setTraces(data.steps || [])
      setSummary(data.summary_text || '')
      setPdfUrl(data.pdf_url || '')
      setExpanded(true)
    } catch (e) {
      console.error('Replay load failed:', e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-600/30 flex items-center justify-center">
            <Search size={14} className="text-indigo-400" />
          </div>
          <span className="text-sm font-semibold text-white">Resolution Replay</span>
          {traces.length > 0 && (
            <span className="badge bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              {traces.length} action{traces.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {traces.length > 0 && pdfUrl && (
            <a
              href={pdfUrl}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-xs text-nexus-400 hover:text-nexus-300 transition-colors"
            >
              <Download size={12} />
              PDF
            </a>
          )}
          <button
            onClick={traces.length > 0 ? () => setExpanded(!expanded) : loadReplay}
            disabled={loading}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
          >
            {loading ? (
              <Clock size={12} className="animate-spin" />
            ) : traces.length > 0 ? (
              expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />
            ) : (
              'Load'
            )}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {expanded && traces.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden space-y-2"
          >
            {traces.map((trace, i) => (
              <motion.div
                key={trace.trace_id || i}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="flex items-start gap-2.5 p-2.5 rounded-xl bg-white/3 border border-white/5 text-xs"
              >
                <div className="mt-0.5">
                  {trace.success
                    ? <CheckCircle size={13} className="text-emerald-400" />
                    : <XCircle size={13} className="text-red-400" />
                  }
                </div>
                <div className="flex-1 min-w-0">
                  <span className="font-medium text-gray-200">
                    {TOOL_LABELS[trace.tool_name] || trace.tool_name}
                  </span>
                  {trace.tool_result && (
                    <p className="text-gray-500 mt-0.5 truncate">
                      {Object.entries(trace.tool_result)
                        .filter(([k]) => !k.startsWith('_'))
                        .slice(0, 2)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(' · ')}
                    </p>
                  )}
                </div>
                <span className="text-gray-600 flex-shrink-0">{trace.duration_ms?.toFixed(0)}ms</span>
              </motion.div>
            ))}

            {pdfUrl && (
              <a
                href={pdfUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-center gap-2 w-full py-2 mt-1 rounded-xl
                           border border-nexus-500/30 text-nexus-400 hover:bg-nexus-500/10
                           text-xs font-medium transition-all duration-200"
              >
                <Download size={12} />
                Download Full PDF Receipt
              </a>
            )}
          </motion.div>
        )}

        {expanded && traces.length === 0 && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-xs text-gray-500 text-center py-2"
          >
            No actions recorded yet in this session.
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  )
}

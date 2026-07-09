import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ChevronRight, MessageSquare, Shield, Zap } from 'lucide-react'
import { AdminDashboard } from '../components/AdminDashboard'
import { useChatStore } from '../store/chatStore'

export default function Admin() {
  const customerName = useChatStore((s) => s.customerName)
  const customerRole = useChatStore((s) => s.customerRole)

  return (
    <div className="min-h-screen bg-transparent">
      {/* ── Sticky header ────────────────────────────────────────────────── */}
      <header className="border-b border-white/5 bg-gray-950/60 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between gap-4">

          {/* Left: logo + breadcrumb */}
          <div className="flex items-center gap-3 min-w-0">
            {/* Logo mark */}
            <div className="w-8 h-8 rounded-full bg-zenta-600 flex items-center justify-center flex-shrink-0 shadow-sm">
              <span className="text-white text-lg font-bold">Z</span>
            </div>

            {/* Breadcrumb */}
            <nav className="flex items-center gap-1 text-xs text-gray-500 min-w-0">
              <Link
                to="/"
                className="hover:text-zenta-600 transition-colors font-medium truncate"
                title="Back to chat"
              >
                Zenta
              </Link>
              <ChevronRight size={12} className="flex-shrink-0 text-gray-700" />
              <span className="text-gray-300 font-semibold truncate">Admin Dashboard</span>
            </nav>
          </div>

          {/* Right: user pill + back link */}
          <div className="flex items-center gap-3 flex-shrink-0">
            {/* Role badge */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/8">
              <Shield
                size={12}
                className={customerRole === 'admin' ? 'text-nexus-400' : 'text-gray-500'}
              />
              <span className="text-xs text-gray-400 font-medium truncate max-w-[140px]">
                {customerName}
              </span>
              {customerRole === 'admin' && (
                <span className="badge text-[10px] bg-nexus-600/20 border-nexus-500/30 text-nexus-300 px-1.5 py-0.5">
                  admin
                </span>
              )}
            </div>

            {/* Back to chat button */}
            <Link
              to="/"
              className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl
                         bg-nexus-600 hover:bg-nexus-500 text-white shadow-lg shadow-nexus-900/20
                         transition-all duration-200 active:scale-95"
            >
              <MessageSquare size={13} />
              <span className="hidden sm:inline">Back to Chat</span>
              <span className="sm:hidden">Chat</span>
            </Link>
          </div>
        </div>
      </header>

      {/* ── Page content ─────────────────────────────────────────────────── */}
      <motion.main
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="pb-12"
      >
        <AdminDashboard />
      </motion.main>
    </div>
  )
}

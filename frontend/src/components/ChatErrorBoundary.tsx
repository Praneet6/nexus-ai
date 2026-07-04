import React from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface ErrorBoundaryState {
  hasError: boolean
  errorMessage: string
}

export class ChatErrorBoundary extends React.Component<
  { children: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false, errorMessage: '' }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, errorMessage: error.message }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ChatErrorBoundary] Render error:', error, info)
  }

  handleReload = () => {
    this.setState({ hasError: false, errorMessage: '' })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen items-center justify-center bg-transparent">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card p-10 flex flex-col items-center gap-5 text-center max-w-sm mx-4"
          >
            <div className="w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
              <AlertTriangle size={26} className="text-red-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white mb-2">Chat failed to load</h2>
              <p className="text-xs text-gray-500 leading-relaxed">
                Something went wrong rendering the chat interface.
                {this.state.errorMessage && (
                  <span className="block mt-2 font-mono text-gray-600 break-all">
                    {this.state.errorMessage}
                  </span>
                )}
              </p>
            </div>
            <button
              onClick={this.handleReload}
              className="flex items-center gap-2 btn-primary text-sm px-5 py-2.5"
            >
              <RefreshCw size={14} />
              Reload chat
            </button>
          </motion.div>
        </div>
      )
    }
    return this.props.children
  }
}

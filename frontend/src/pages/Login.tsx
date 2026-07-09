import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Mail, Lock, User, ArrowRight, Sparkles } from 'lucide-react'
import { useChatStore } from '../store/chatStore'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const setAuth = useChatStore((s) => s.setAuth)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isRegister) {
        // Registration endpoint (JSON body)
        const res = await fetch('/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, name }),
        })

        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Registration failed')

        setAuth(data.access_token, data.customer_id, name, data.role || 'user')
        navigate('/')
      } else {
        // Login endpoint (x-www-form-urlencoded OAuth2 form)
        const params = new URLSearchParams()
        params.append('username', email)
        params.append('password', password)

        const res = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: params.toString(),
        })

        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Invalid credentials')

        setAuth(data.access_token, data.customer_id, data.name, data.role || 'user')
        navigate('/')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-screen flex items-center justify-center p-4 relative overflow-hidden bg-surface">

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md zenta-card p-8 relative z-10"
      >
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-2xl bg-zenta-600 flex items-center justify-center shadow-md">
            <span className="text-white text-2xl font-bold">Z</span>
          </div>
          <div>
            <h2 className="text-2xl font-bold text-text-primary">Welcome to Zenta</h2>
            <p className="text-sm text-text-secondary mt-1">Intelligent Customer Care</p>
          </div>
        </div>

        {/* Error alert */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-xl p-3 mb-6"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Auth form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <AnimatePresence mode="popLayout">
            {isRegister && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className="space-y-1.5"
              >
                <label className="text-xs text-gray-500 font-medium ml-1">Full Name</label>
                <div className="relative flex items-center">
                  <User size={16} className="absolute left-3 text-gray-500" />
                  <input
                    type="text"
                    required
                    placeholder="Enter your name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full input-field pl-10 text-sm"
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="space-y-1.5">
            <label className="text-xs text-gray-500 font-medium ml-1">Email Address</label>
            <div className="relative flex items-center">
              <Mail size={16} className="absolute left-3 text-gray-500" />
              <input
                type="email"
                required
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full input-field pl-10 text-sm"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-gray-500 font-medium ml-1">Password</label>
            <div className="relative flex items-center">
              <Lock size={16} className="absolute left-3 text-gray-500" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full input-field pl-10 text-sm"
              />
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={loading}
            className="w-full btn-primary flex items-center justify-center gap-2 py-3 mt-6 text-sm"
          >
            {loading ? (
              <div className="w-5 h-5 rounded-full border-2 border-white border-t-transparent animate-spin" />
            ) : (
              <>
                {isRegister ? 'Create Account' : 'Sign In'}
                <ArrowRight size={16} />
              </>
            )}
          </motion.button>
        </form>

        {/* Toggle */}
        <div className="text-center mt-6">
          <button
            onClick={() => {
              setIsRegister(!isRegister)
              setError('')
            }}
            className="text-xs text-zenta-600 hover:text-zenta-700 transition-colors font-medium"
          >
            {isRegister
              ? 'Already have an account? Sign in'
              : "Don't have an account? Sign up"}
          </button>
        </div>
      </motion.div>
    </div>
  )
}

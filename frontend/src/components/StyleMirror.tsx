import { motion } from 'framer-motion'
import { Wand2 } from 'lucide-react'
import { useStyleProfile } from '../hooks/useStyleProfile'

export function StyleMirror() {
  const { styleProfile, label: styleLabel } = useStyleProfile()

  if (!styleProfile) return null

  return (
    <motion.div
      data-testid="style-mirror"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card px-3 py-2.5"
    >
      <div className="flex items-center gap-2 mb-1.5">
        <Wand2 size={12} className="text-nexus-400" />
        <span className="text-xs font-semibold text-gray-400">Style Mirror</span>
      </div>
      <p className="text-xs text-nexus-300 font-medium">{styleLabel}</p>
      <div className="mt-1.5 flex flex-wrap gap-1">
        {styleProfile.formality !== 'casual' && (
          <span className="badge text-[10px] bg-nexus-600/15 border-nexus-500/20 text-nexus-300">
            {styleProfile.formality}
          </span>
        )}
        {styleProfile.verbosity !== 'balanced' && (
          <span className="badge text-[10px] bg-white/5 border-white/10 text-gray-400">
            {styleProfile.verbosity}
          </span>
        )}
        {styleProfile.emotional_tone !== 'neutral' && (
          <span className="badge text-[10px] bg-amber-500/10 border-amber-500/20 text-amber-300">
            {styleProfile.emotional_tone}
          </span>
        )}
      </div>
    </motion.div>
  )
}

import { useChatStore } from '../store/chatStore'

/**
 * F04 — Style profile hook.
 * Reads current style profile from global store.
 */
export function useStyleProfile() {
  const styleProfile = useChatStore((s) => s.styleProfile)

  const label = () => {
    if (!styleProfile) return null
    const parts: string[] = []
    if (styleProfile.formality === 'slang') parts.push('Casual')
    else if (styleProfile.formality === 'formal') parts.push('Formal')
    if (styleProfile.verbosity === 'terse') parts.push('Brief')
    else if (styleProfile.verbosity === 'verbose') parts.push('Detailed')
    if (styleProfile.emotional_tone === 'expressive') parts.push('Expressive')
    return parts.join(' · ') || 'Balanced'
  }

  return { styleProfile, label: label() }
}

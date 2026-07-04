import { useRef, useCallback, useEffect } from 'react'

export interface KeystrokeEvent {
  delay_ms: number
  is_backspace: boolean
  idle_ms: number
}

/**
 * F02 — Keystroke tracker.
 * Captures ONLY timing metadata — never the key character itself.
 * Privacy-safe by design.
 */
export function useKeystrokeTracker(active: boolean = true) {
  const lastKeyTime = useRef<number>(0)
  const lastActivityTime = useRef<number>(Date.now())
  const buffer = useRef<KeystrokeEvent[]>([])

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!active) return

    const now = Date.now()
    const delay_ms = lastKeyTime.current ? now - lastKeyTime.current : 0
    const idle_ms = lastActivityTime.current
      ? now - lastActivityTime.current
      : 0

    const event: KeystrokeEvent = {
      delay_ms: Math.min(delay_ms, 10000),       // cap at 10s
      is_backspace: e.key === 'Backspace' || e.key === 'Delete',
      idle_ms: idle_ms > 500 ? Math.min(idle_ms, 30000) : 0,
    }

    buffer.current.push(event)

    // Keep buffer to last 50 events
    if (buffer.current.length > 50) {
      buffer.current = buffer.current.slice(-50)
    }

    lastKeyTime.current = now
    lastActivityTime.current = now
  }, [active])

  useEffect(() => {
    if (!active) return
    document.addEventListener('keydown', handleKeyDown, { passive: true })
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown, active])

  /** Flush the buffer and return all accumulated events since last flush */
  const flushEvents = useCallback((): KeystrokeEvent[] => {
    const events = [...buffer.current]
    buffer.current = []
    return events
  }, [])

  /** Peek without clearing */
  const peekEvents = useCallback((): KeystrokeEvent[] => {
    return [...buffer.current]
  }, [])

  return { flushEvents, peekEvents }
}

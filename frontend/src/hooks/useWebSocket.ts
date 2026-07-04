import { useEffect, useRef, useCallback, useState } from 'react'
import { useChatStore, Contract, TrustCredit } from '../store/chatStore'

const WS_URL = import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()

  const {
    sessionId, token,
    addMessage, appendToLastMessage, setStreaming,
    setContract, setSilenceState, setTrustBalance,
    setTrustCredit, setStyleProfile, setConnected, setTyping,
  } = useChatStore()

  const [toast, setToast] = useState<{ message: string; type: 'info' | 'success' | 'error' } | null>(null)
  const retryCount = useRef(0)
  const MAX_RETRIES = 5

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return
    const tok = localStorage.getItem('nexus_token') || token
    const sid = localStorage.getItem('nexus_session') || sessionId
    if (!sid) return
    const url = `${WS_URL}/ws/chat/${sid}?token=${tok}`
    ws.current = new WebSocket(url)

    ws.current.onopen = () => {
      setConnected(true)
      console.log('[WS] Connected')
      if (retryCount.current > 0) {
        setToast({ message: 'Reconnected!', type: 'success' })
        setTimeout(() => setToast(null), 2000)
        retryCount.current = 0
      }
    }

    ws.current.onclose = () => {
      setConnected(false)
      if (retryCount.current < MAX_RETRIES) {
        retryCount.current += 1
        setToast({ message: 'Connection lost, reconnecting...', type: 'info' })
        console.log(`[WS] Disconnected — reconnecting in 3s... (Attempt ${retryCount.current}/${MAX_RETRIES})`)
        reconnectTimer.current = setTimeout(connect, 3000)
      } else {
        setToast({ message: 'Connection failed. Please refresh.', type: 'error' })
        console.log('[WS] Disconnected — max retries exceeded.')
      }
    }

    ws.current.onerror = (e) => {
      console.error('[WS] Error:', e)
    }

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleServerEvent(data)
      } catch (e) {
        console.warn('[WS] Parse error:', e)
      }
    }
  }, [sessionId, token])

  const handleServerEvent = useCallback((data: Record<string, unknown>) => {
    switch (data.type) {
      case 'token':
        appendToLastMessage(data.content as string)
        break

      case 'tool_executing':
        // Show a subtle indicator that a tool is running
        break

      case 'contract':
        setContract(data.contract as Contract)
        break

      case 'silence_alert':
        setSilenceState(data.state as 'confident' | 'confused' | 'distressed')
        break

      case 'trust_event': {
        setTrustBalance(data.balance as number, data.health as string)
        if (data.credit) {
          setTrustCredit(data.credit as TrustCredit)
          // Show credit message in chat
          addMessage({
            role: 'assistant',
            content: (data.credit as TrustCredit).message,
          })
        }
        break
      }

      case 'style_profile':
        // F04 — update store whenever backend reclassifies writing style
        if (data.profile) {
          setStyleProfile(data.profile as import('../store/chatStore').StyleProfile)
        }
        break

      case 'done':
        setStreaming(false)
        setTyping(false)
        break

      case 'error':
        setStreaming(false)
        setTyping(false)
        addMessage({ role: 'assistant', content: `⚠️ ${data.message}` })
        break
    }
  }, [addMessage, appendToLastMessage, setContract, setSilenceState,
    setTrustBalance, setTrustCredit, setStyleProfile, setStreaming, setTyping])

  useEffect(() => {
    const tryConnect = () => {
      const tok = localStorage.getItem('nexus_token')
      const sid = localStorage.getItem('nexus_session')
      
      if (tok && sid) {
        connect()
      } else {
        reconnectTimer.current = setTimeout(tryConnect, 500)
      }
    }
    
    tryConnect()
    
    return () => {
      clearTimeout(reconnectTimer.current)
      ws.current?.close()
    }
  }, [])

  const sendMessage = useCallback((content: string, keydata: object[] = []) => {
    if (ws.current?.readyState !== WebSocket.OPEN) {
      console.warn('[WS] Not connected')
      return false
    }
    // Add user message optimistically
    addMessage({ role: 'user', content })
    // Add empty assistant message that will be streamed into
    addMessage({ role: 'assistant', content: '', isStreaming: true })
    setTyping(true)

    ws.current.send(JSON.stringify({ type: 'message', content, keydata }))
    return true
  }, [addMessage, setTyping])

  return { sendMessage, isConnected: ws.current?.readyState === WebSocket.OPEN, toast }
}

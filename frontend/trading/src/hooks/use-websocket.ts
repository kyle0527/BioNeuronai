import { useEffect, useRef, useState, useCallback } from 'react'

export interface UseWebSocketOptions {
  onOpen?: () => void
  onMessage?: (data: any) => void
  onClose?: () => void
  onError?: (error: Event) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
  enabled?: boolean
}

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

function resolveWebSocketUrl(url: string): string {
  if (url.startsWith('ws://') || url.startsWith('wss://')) {
    return url
  }

  const apiBase = import.meta.env.VITE_API_BASE_URL as string | undefined
  const base = apiBase || window.location.origin
  const resolved = new URL(url, base)
  resolved.protocol = resolved.protocol === 'https:' ? 'wss:' : 'ws:'
  return resolved.toString()
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const {
    onOpen,
    onMessage,
    onClose,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    enabled = true,
  } = options

  const [status, setStatus] = useState<WebSocketStatus>('disconnected')
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const shouldReconnect = useRef(true)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      setStatus('connecting')
      const ws = new WebSocket(resolveWebSocketUrl(url))

      ws.onopen = () => {
        setStatus('connected')
        setReconnectAttempts(0)
        onOpen?.()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage?.(data)
        } catch {
          onMessage?.(event.data)
        }
      }

      ws.onerror = (error) => {
        setStatus('error')
        onError?.(error)
      }

      ws.onclose = () => {
        setStatus('disconnected')
        onClose?.()

        if (shouldReconnect.current && reconnectAttempts < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts((prev) => prev + 1)
            connect()
          }, reconnectInterval)
        }
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setStatus('error')
    }
  }, [url, onOpen, onMessage, onClose, onError, reconnectAttempts, maxReconnectAttempts, reconnectInterval])

  const disconnect = useCallback(() => {
    shouldReconnect.current = false
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  const sendMessage = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }, [])

  useEffect(() => {
    if (enabled) {
      shouldReconnect.current = true
      connect()
    }

    return () => {
      disconnect()
    }
  }, [enabled, connect, disconnect])

  const reconnect = useCallback(() => {
    setReconnectAttempts(0)
    shouldReconnect.current = true
    connect()
  }, [connect])

  return {
    status,
    sendMessage,
    disconnect,
    reconnect,
    reconnectAttempts,
  }
}

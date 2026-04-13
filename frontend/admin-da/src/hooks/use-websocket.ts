import { useEffect, useRef, useState, useCallback } from 'react'

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

interface UseWebSocketOptions {
  url: string
  reconnect?: boolean
  reconnectInterval?: number
  reconnectAttempts?: number
  onMessage?: (data: unknown) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket({
  url,
  reconnect = true,
  reconnectInterval = 3000,
  reconnectAttempts = 5,
  onMessage,
  onOpen,
  onClose,
  onError
}: UseWebSocketOptions) {
  const [status, setStatus] = useState<WebSocketStatus>('disconnected')
  const [lastMessage, setLastMessage] = useState<unknown>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectCountRef = useRef(0)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || 
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      return
    }

    try {
      setStatus('connecting')
      const ws = new WebSocket(url)

      ws.onopen = () => {
        setStatus('connected')
        reconnectCountRef.current = 0
        onOpen?.()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
          onMessage?.(data)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onclose = () => {
        setStatus('disconnected')
        onClose?.()

        if (reconnect && reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current++
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        }
      }

      ws.onerror = (error) => {
        setStatus('error')
        onError?.(error)
      }

      wsRef.current = ws
    } catch (err) {
      setStatus('error')
      console.error('WebSocket connection error:', err)
    }
  }, [url, reconnect, reconnectAttempts, reconnectInterval, onMessage, onOpen, onClose, onError])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setStatus('disconnected')
  }, [])

  const sendMessage = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    status,
    lastMessage,
    sendMessage,
    connect,
    disconnect
  }
}

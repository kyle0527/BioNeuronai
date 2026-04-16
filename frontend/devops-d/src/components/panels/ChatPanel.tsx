import { useState, useEffect, useRef } from 'react'
import { PaperPlaneRight, Trash } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { endpoints, type ApiError, type ChatResponse } from '@/lib/api'

const MESSAGES_KEY = 'bioneuronai-chat-messages'
const CONV_ID_KEY = 'bioneuronai-chat-conv-id'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  latency_ms?: number
  confidence?: number
  language?: string
}

function loadMessages(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(MESSAGES_KEY)
    return raw ? (JSON.parse(raw) as ChatMessage[]) : []
  } catch {
    return []
  }
}

function saveMessages(msgs: ChatMessage[]) {
  try {
    localStorage.setItem(MESSAGES_KEY, JSON.stringify(msgs))
  } catch {
    // storage full — silently ignore
  }
}

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadMessages())
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [language, setLanguage] = useState<'auto' | 'zh' | 'en'>('auto')
  const [symbol, setSymbol] = useState('')
  const [conversationId, setConversationId] = useState<string | null>(
    () => localStorage.getItem(CONV_ID_KEY)
  )
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const addMessage = (msg: ChatMessage) => {
    setMessages((prev) => {
      const next = [...prev, msg]
      saveMessages(next)
      return next
    })
  }

  const clearChat = () => {
    setMessages([])
    saveMessages([])
    const newId = `conv-${Date.now()}`
    setConversationId(newId)
    localStorage.setItem(CONV_ID_KEY, newId)
    setError(null)
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toLocaleTimeString(),
    }
    addMessage(userMessage)
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const response = await endpoints.chat({
        message: userMessage.content,
        language,
        symbol: symbol.trim() || null,
        conversation_id: conversationId,
      })
      const chatResp = response.data as ChatResponse

      // Persist conversation ID for multi-turn
      if (chatResp.conversation_id) {
        setConversationId(chatResp.conversation_id)
        localStorage.setItem(CONV_ID_KEY, chatResp.conversation_id)
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: chatResp.text,
        timestamp: new Date().toLocaleTimeString(),
        latency_ms: chatResp.latency_ms,
        confidence: chatResp.confidence,
        language: chatResp.language,
      }
      addMessage(assistantMessage)
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="flex flex-col h-[600px]">
      <CardHeader className="flex-none pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-mono font-medium">Chat Interface</CardTitle>
          <Button size="sm" variant="ghost" onClick={clearChat} title="Clear chat">
            <Trash size={14} />
          </Button>
        </div>
        <div className="grid grid-cols-2 gap-2 pt-1">
          <div className="space-y-1">
            <Label htmlFor="chat-lang" className="text-xs">Language</Label>
            <Select value={language} onValueChange={(v) => setLanguage(v as 'auto' | 'zh' | 'en')}>
              <SelectTrigger id="chat-lang" className="h-7 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">Auto</SelectItem>
                <SelectItem value="zh">中文</SelectItem>
                <SelectItem value="en">English</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label htmlFor="chat-symbol" className="text-xs">Symbol (optional)</Label>
            <Input
              id="chat-symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="BTCUSDT"
              className="h-7 text-xs font-mono"
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col space-y-3 min-h-0 pt-0">
        <ScrollArea className="flex-1 pr-2">
          <div className="space-y-3 py-1">
            {messages.map((msg) => (
              <div key={msg.id} className={`space-y-1 ${msg.role === 'user' ? 'text-right' : ''}`}>
                <div className="text-xs text-muted-foreground flex items-center gap-1 flex-wrap">
                  {msg.role === 'user' ? (
                    <span className="ml-auto">{msg.timestamp}</span>
                  ) : (
                    <>
                      <span>{msg.timestamp}</span>
                      {msg.latency_ms != null && (
                        <Badge variant="secondary" className="text-xs px-1 py-0 font-mono">
                          {Math.round(msg.latency_ms)}ms
                        </Badge>
                      )}
                      {msg.confidence != null && (
                        <Badge variant="outline" className="text-xs px-1 py-0 font-mono">
                          {(msg.confidence * 100).toFixed(0)}%
                        </Badge>
                      )}
                      {msg.language && (
                        <Badge variant="outline" className="text-xs px-1 py-0">
                          {msg.language}
                        </Badge>
                      )}
                    </>
                  )}
                </div>
                <div
                  className={`inline-block max-w-[85%] rounded-lg px-3 py-2 text-sm text-left whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-foreground'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <LoadingSpinner size="sm" />
                <span>Thinking...</span>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>

        {error && <ErrorPanel message={error.message} details={error.details} />}

        <Separator />

        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder="Type your message..."
            disabled={loading}
            id="chat-input"
          />
          <Button onClick={sendMessage} disabled={!input.trim() || loading}>
            {loading ? <LoadingSpinner size="sm" /> : <PaperPlaneRight size={16} weight="fill" />}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

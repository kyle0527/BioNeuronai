import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { toast } from 'sonner'
import { api } from '@/lib/api-client'
import type { ChatMessage } from '@/lib/types'
import { PaperPlaneRight } from '@phosphor-icons/react'
import { cn } from '@/lib/utils'

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [conversationId, setConversationId] = useState('')
  const [language, setLanguage] = useState<'auto' | 'zh' | 'en'>('auto')
  const [symbol, setSymbol] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const storedId = localStorage.getItem('chat_conversation_id')
    if (storedId) {
      setConversationId(storedId)
    } else {
      const newId = `conv_${Date.now()}`
      setConversationId(newId)
      localStorage.setItem('chat_conversation_id', newId)
    }

    const storedMessages = localStorage.getItem('chat_messages')
    if (storedMessages) {
      try {
        setMessages(JSON.parse(storedMessages))
      } catch (e) {
        console.error('Failed to parse stored messages')
      }
    }
  }, [])

  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chat_messages', JSON.stringify(messages))
    }
  }, [messages])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await api.sendChatMessage({
        message: input,
        conversation_id: conversationId,
        language,
        symbol: symbol || undefined,
      })

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        latency_ms: response.latency_ms,
        confidence: response.confidence,
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      toast.error('Failed to send message')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const clearChat = () => {
    setMessages([])
    localStorage.removeItem('chat_messages')
    const newId = `conv_${Date.now()}`
    setConversationId(newId)
    localStorage.setItem('chat_conversation_id', newId)
    toast.success('Chat cleared')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold font-mono">Chat Assistant</h1>
        <Button onClick={clearChat} variant="outline" size="sm">
          Clear Chat
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <Card className="flex flex-col h-[calc(100vh-200px)]">
          <CardHeader>
            <CardTitle>Conversation</CardTitle>
            <CardDescription>Ask questions about trading and market analysis</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col gap-4 min-h-0">
            <ScrollArea className="flex-1 pr-4" ref={scrollRef}>
              <div className="space-y-4">
                {messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    <p className="text-sm">Start a conversation by sending a message below</p>
                  </div>
                ) : (
                  messages.map((message, index) => (
                    <div
                      key={index}
                      className={cn(
                        'flex',
                        message.role === 'user' ? 'justify-end' : 'justify-start'
                      )}
                    >
                      <div
                        className={cn(
                          'max-w-[80%] rounded-lg p-3',
                          message.role === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        )}
                      >
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        <div className="flex items-center gap-3 mt-2 text-xs opacity-70">
                          <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
                          {message.latency_ms && <span>⚡ {message.latency_ms}ms</span>}
                          {message.confidence && <span>✓ {(message.confidence * 100).toFixed(0)}%</span>}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>

            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                disabled={loading}
              />
              <Button onClick={handleSend} disabled={loading || !input.trim()}>
                <PaperPlaneRight />
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Language</Label>
                <Select value={language} onValueChange={(v) => setLanguage(v as any)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Auto</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="zh">中文</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="symbol">Symbol Context (Optional)</Label>
                <Input
                  id="symbol"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  placeholder="BTCUSDT"
                />
              </div>

              <div className="pt-4 border-t space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Conversation ID</span>
                </div>
                <p className="font-mono text-xs break-all">{conversationId}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Tips</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="text-sm space-y-2 text-muted-foreground">
                <li>• Ask about market conditions</li>
                <li>• Request trade analysis</li>
                <li>• Get strategy suggestions</li>
                <li>• Discuss risk management</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

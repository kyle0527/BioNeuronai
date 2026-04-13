import { useState } from 'react'
import { PaperPlaneRight } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { JSONViewer } from '@/components/JSONViewer'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { api, type ApiError } from '@/lib/api'

const HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE']

export function APIPlayground() {
  const [method, setMethod] = useState('GET')
  const [endpoint, setEndpoint] = useState('/api/v1/status')
  const [body, setBody] = useState('{}')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [response, setResponse] = useState<unknown>(null)
  const [statusCode, setStatusCode] = useState<number | null>(null)

  const executeRequest = async () => {
    setLoading(true)
    setError(null)
    setResponse(null)
    setStatusCode(null)

    try {
      let parsedBody
      if (method !== 'GET' && body.trim()) {
        try {
          parsedBody = JSON.parse(body)
        } catch {
          throw { message: 'Invalid JSON in request body', details: body } as ApiError
        }
      }

      let result
      switch (method) {
        case 'GET':
          result = await api.get(endpoint)
          break
        case 'POST':
          result = await api.post(endpoint, parsedBody)
          break
        case 'PUT':
          result = await api.put(endpoint, parsedBody)
          break
        case 'DELETE':
          result = await api.delete(endpoint)
          break
        default:
          throw new Error('Invalid HTTP method')
      }

      setResponse(result.data)
      setStatusCode(result.status)
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-mono font-medium">API Playground</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-[140px_1fr_auto] gap-2">
          <div>
            <Label htmlFor="method" className="text-xs">Method</Label>
            <Select value={method} onValueChange={setMethod}>
              <SelectTrigger id="method">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {HTTP_METHODS.map((m) => (
                  <SelectItem key={m} value={m}>
                    {m}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="endpoint" className="text-xs">Endpoint</Label>
            <Input
              id="endpoint"
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              placeholder="/endpoint"
            />
          </div>
          <div className="flex items-end">
            <Button onClick={executeRequest} disabled={!endpoint || loading}>
              {loading ? <LoadingSpinner size="sm" className="mr-2" /> : <PaperPlaneRight size={16} className="mr-2" />}
              Send
            </Button>
          </div>
        </div>

        {method !== 'GET' && (
          <div>
            <Label htmlFor="body" className="text-xs">Request Body (JSON)</Label>
            <Textarea
              id="body"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder='{"key": "value"}'
              className="font-mono text-sm h-32"
            />
          </div>
        )}

        {error && <ErrorPanel message={error.message} details={error.details} />}

        {response !== null && !error && (
          <>
            <Separator />
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-muted-foreground">Response:</p>
                {statusCode && (
                  <Badge variant={statusCode >= 200 && statusCode < 300 ? 'default' : 'destructive'}>
                    {statusCode}
                  </Badge>
                )}
              </div>
              <JSONViewer data={response} maxHeight="400px" />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

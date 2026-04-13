import { useState } from 'react'
import { Play } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { JSONViewer } from '@/components/JSONViewer'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { endpoints, type ApiError } from '@/lib/api'

export function PreTradePanel() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [data, setData] = useState<unknown>(null)
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [action, setAction] = useState<'long' | 'short'>('long')

  const runPreTrade = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await endpoints.pretrade({ symbol, action })
      setData(response.data)
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-mono font-medium">Pre-Trade Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label htmlFor="pretrade-symbol" className="text-xs">Symbol</Label>
            <Input
              id="pretrade-symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="BTCUSDT"
              className="font-mono text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="pretrade-action" className="text-xs">Direction</Label>
            <Select value={action} onValueChange={(v) => setAction(v as 'long' | 'short')}>
              <SelectTrigger id="pretrade-action">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="long">Long</SelectItem>
                <SelectItem value="short">Short</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <Button onClick={runPreTrade} disabled={loading} className="w-full">
          {loading ? <LoadingSpinner size="sm" className="mr-2" /> : <Play size={16} weight="fill" className="mr-2" />}
          Run Pre-Trade Analysis
        </Button>

        {error && <ErrorPanel message={error.message} details={error.details} />}

        {data && !error && (
          <>
            <Separator />
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">Analysis Results:</p>
              <JSONViewer data={data} maxHeight="400px" />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

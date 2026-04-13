import { useState } from 'react'
import { ArrowClockwise } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { JSONViewer } from '@/components/JSONViewer'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { endpoints, type ApiError } from '@/lib/api'

export function NewsPanel() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [data, setData] = useState<unknown>(null)
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [maxItems, setMaxItems] = useState(10)

  const fetchNews = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await endpoints.news({ symbol, max_items: maxItems })
      setData(response.data)
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-sm font-mono font-medium">News Feed</CardTitle>
        <Button size="sm" variant="ghost" onClick={fetchNews} disabled={loading}>
          {loading ? <LoadingSpinner size="sm" /> : <ArrowClockwise size={16} />}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label htmlFor="news-symbol" className="text-xs">Symbol</Label>
            <Input
              id="news-symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="BTCUSDT"
              className="font-mono text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="news-max-items" className="text-xs">Max Items (1–50)</Label>
            <Input
              id="news-max-items"
              type="number"
              min={1}
              max={50}
              value={maxItems}
              onChange={(e) => setMaxItems(Math.min(50, Math.max(1, Number(e.target.value))))}
              className="font-mono text-sm"
            />
          </div>
        </div>

        {error && <ErrorPanel message={error.message} details={error.details} />}

        {data && !error && (
          <>
            <Separator />
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">News Data:</p>
              <ScrollArea className="h-[300px]">
                <JSONViewer data={data} maxHeight="none" />
              </ScrollArea>
            </div>
          </>
        )}

        {!data && !error && !loading && (
          <p className="text-sm text-muted-foreground">Click refresh to fetch news</p>
        )}
      </CardContent>
    </Card>
  )
}

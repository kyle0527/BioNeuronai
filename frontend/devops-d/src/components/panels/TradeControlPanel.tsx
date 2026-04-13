import { useState } from 'react'
import { Play, Stop } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { JSONViewer } from '@/components/JSONViewer'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { endpoints, type ApiError } from '@/lib/api'

export function TradeControlPanel() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [data, setData] = useState<unknown>(null)
  const [tradeActive, setTradeActive] = useState(false)
  const [lastAction, setLastAction] = useState<'start' | 'stop' | null>(null)
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [testnet, setTestnet] = useState(true)

  const handleStart = async () => {
    setLoading(true)
    setError(null)
    setLastAction('start')
    try {
      const response = await endpoints.tradeStart({ symbol, testnet })
      setData(response.data)
      setTradeActive(true)
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  const handleStop = async () => {
    setLoading(true)
    setError(null)
    setLastAction('stop')
    try {
      const response = await endpoints.tradeStop()
      setData(response.data)
      setTradeActive(false)
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-mono font-medium flex items-center justify-between">
          <span>Trade Control</span>
          {tradeActive && <Badge className="bg-success text-success-foreground">Active</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label htmlFor="trade-symbol" className="text-xs">Symbol</Label>
            <Input
              id="trade-symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="BTCUSDT"
              className="font-mono text-sm"
              disabled={tradeActive}
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Testnet</Label>
            <div className="flex items-center gap-2 h-9">
              <Switch
                checked={testnet}
                onCheckedChange={setTestnet}
                disabled={tradeActive}
                id="trade-testnet"
              />
              <Label htmlFor="trade-testnet" className="text-xs text-muted-foreground">
                {testnet ? 'Testnet' : 'Mainnet'}
              </Label>
            </div>
          </div>
        </div>

        {!testnet && (
          <p className="text-xs text-destructive font-medium">
            ⚠ Mainnet mode — real funds at risk
          </p>
        )}

        <div className="flex gap-2">
          <Button onClick={handleStart} disabled={loading || tradeActive} className="flex-1">
            {loading && lastAction === 'start' ? (
              <LoadingSpinner size="sm" className="mr-2" />
            ) : (
              <Play size={16} weight="fill" className="mr-2" />
            )}
            Start Trading
          </Button>
          <Button onClick={handleStop} disabled={loading || !tradeActive} variant="destructive" className="flex-1">
            {loading && lastAction === 'stop' ? (
              <LoadingSpinner size="sm" className="mr-2" />
            ) : (
              <Stop size={16} weight="fill" className="mr-2" />
            )}
            Stop Trading
          </Button>
        </div>

        {error && <ErrorPanel message={error.message} details={error.details} />}

        {data && !error && (
          <>
            <Separator />
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">Response:</p>
              <JSONViewer data={data} maxHeight="300px" />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

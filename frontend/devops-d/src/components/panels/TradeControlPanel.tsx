import { useEffect, useState } from 'react'
import { Play, Stop } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { JSONViewer } from '@/components/JSONViewer'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { endpoints, type ApiError, type TradeMode } from '@/lib/api'

export function TradeControlPanel() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [data, setData] = useState<unknown>(null)
  const [tradeActive, setTradeActive] = useState(false)
  const [lastAction, setLastAction] = useState<'start' | 'stop' | 'status' | null>(null)
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [testnet, setTestnet] = useState(true)
  const [mode, setMode] = useState<TradeMode>('monitor_only')
  const [loadAiModel, setLoadAiModel] = useState(false)
  const [warmupModel, setWarmupModel] = useState(false)
  const [modelName, setModelName] = useState('my_100m_model')
  const [confirmLive, setConfirmLive] = useState('')

  const autoTrade = mode !== 'monitor_only'
  const effectiveTestnet = mode === 'live_auto' ? false : mode === 'testnet_auto' ? true : testnet
  const mainnetRequested = !effectiveTestnet

  const updateActiveFromPayload = (payload: unknown, fallback: boolean) => {
    const running = (payload as { running?: unknown } | null)?.running
    setTradeActive(typeof running === 'boolean' ? running : fallback)
  }

  const handleModeChange = (value: TradeMode) => {
    setMode(value)
    if (value === 'testnet_auto') {
      setTestnet(true)
    }
    if (value === 'live_auto') {
      setTestnet(false)
    }
  }

  const handleStart = async () => {
    setLoading(true)
    setError(null)
    setLastAction('start')
    try {
      const response = await endpoints.tradeStart({
        symbol,
        testnet: effectiveTestnet,
        mode,
        auto_trade: autoTrade,
        load_ai_model: loadAiModel,
        model_name: modelName,
        warmup_model: warmupModel,
        confirm_live: confirmLive,
      })
      setData(response.data ?? response)
      updateActiveFromPayload(response.data, response.success)
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
      setData(response.data ?? response)
      setTradeActive(false)
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  const handleStatus = async () => {
    setLoading(true)
    setError(null)
    setLastAction('status')
    try {
      const response = await endpoints.tradeStatus()
      setData(response.data ?? response)
      updateActiveFromPayload(response.data, false)
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const response = await endpoints.tradeStatus()
        setData(response.data ?? response)
        updateActiveFromPayload(response.data, false)
      } catch {
        // 狀態查詢失敗時保留面板可操作性，使用者按 Start 時會看到實際錯誤。
      }
    }
    void loadStatus()
  }, [])

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
            <Label htmlFor="trade-mode" className="text-xs">Mode</Label>
            <Select value={mode} onValueChange={(value) => handleModeChange(value as TradeMode)} disabled={tradeActive}>
              <SelectTrigger id="trade-mode" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="monitor_only">Monitor only</SelectItem>
                <SelectItem value="testnet_auto">Testnet auto</SelectItem>
                <SelectItem value="live_auto">Live auto</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label className="text-xs">Environment</Label>
            <div className="flex items-center gap-2 h-9">
              <Switch
                checked={testnet}
                onCheckedChange={setTestnet}
                disabled={tradeActive || mode !== 'monitor_only'}
                id="trade-testnet"
              />
              <Label htmlFor="trade-testnet" className="text-xs text-muted-foreground">
                {effectiveTestnet ? 'Testnet' : 'Mainnet'}
              </Label>
            </div>
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Load AI Model</Label>
            <div className="flex items-center gap-2 h-9">
              <Switch
                checked={loadAiModel}
                onCheckedChange={setLoadAiModel}
                disabled={tradeActive}
                id="trade-load-model"
              />
              <Label htmlFor="trade-load-model" className="text-xs text-muted-foreground">
                {loadAiModel ? 'Enabled' : 'Skipped'}
              </Label>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label htmlFor="trade-model-name" className="text-xs">Model</Label>
            <Input
              id="trade-model-name"
              value={modelName}
              onChange={(event) => setModelName(event.target.value)}
              className="font-mono text-sm"
              disabled={tradeActive || !loadAiModel}
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Warmup</Label>
            <div className="flex items-center gap-2 h-9">
              <Switch
                checked={warmupModel}
                onCheckedChange={setWarmupModel}
                disabled={tradeActive || !loadAiModel}
                id="trade-warmup-model"
              />
              <Label htmlFor="trade-warmup-model" className="text-xs text-muted-foreground">
                {warmupModel ? 'On' : 'Off'}
              </Label>
            </div>
          </div>
        </div>

        {mainnetRequested && (
          <div className="space-y-1">
            <Label htmlFor="trade-live-confirm" className="text-xs">Live Confirm</Label>
            <Input
              id="trade-live-confirm"
              value={confirmLive}
              onChange={(event) => setConfirmLive(event.target.value)}
              placeholder="I_UNDERSTAND_LIVE_RISK"
              className="font-mono text-xs"
              disabled={tradeActive}
            />
          </div>
        )}

        {mainnetRequested && (
          <p className="text-xs text-destructive font-medium">
            Mainnet mode - real funds at risk. Backend also requires ALLOW_LIVE_TRADING=1.
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
        <Button onClick={handleStatus} disabled={loading} variant="outline" className="w-full">
          {loading && lastAction === 'status' && <LoadingSpinner size="sm" className="mr-2" />}
          Refresh Status
        </Button>

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

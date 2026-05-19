import { useCallback, useEffect, useMemo, useState } from 'react'
import { ArrowClockwise, ChartLine } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { endpoints, type ApiError, type MarketCandle, type MarketKlinesData } from '@/lib/api'

const INTERVALS = ['1m', '3m', '5m', '15m', '30m', '1h', '4h'] as const
const CHART_WIDTH = 900
const CHART_HEIGHT = 300
const PADDING = { top: 16, right: 58, bottom: 28, left: 10 }

function formatPrice(value: number) {
  if (!Number.isFinite(value)) return '-'
  return value >= 1000 ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : value.toFixed(4)
}

function formatClock(value?: string) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleTimeString()
}

function candleX(index: number, count: number) {
  const usableWidth = CHART_WIDTH - PADDING.left - PADDING.right
  if (count <= 1) return PADDING.left + usableWidth
  return PADDING.left + (index / (count - 1)) * usableWidth
}

function candleY(price: number, min: number, max: number) {
  const usableHeight = CHART_HEIGHT - PADDING.top - PADDING.bottom
  if (max <= min) return PADDING.top + usableHeight / 2
  return PADDING.top + ((max - price) / (max - min)) * usableHeight
}

function MarketCandlesSvg({ candles }: { candles: MarketCandle[] }) {
  const visible = candles.slice(-90)
  const scale = useMemo(() => {
    const lows = visible.map((item) => item.low)
    const highs = visible.map((item) => item.high)
    const min = Math.min(...lows)
    const max = Math.max(...highs)
    const range = Math.max(max - min, 1)
    return {
      min: min - range * 0.04,
      max: max + range * 0.04,
    }
  }, [visible])

  const ticks = useMemo(() => {
    const result: number[] = []
    for (let index = 0; index < 4; index += 1) {
      result.push(scale.min + ((scale.max - scale.min) * index) / 3)
    }
    return result.reverse()
  }, [scale])

  if (visible.length === 0) {
    return (
      <div className="h-[300px] rounded-md border flex items-center justify-center text-sm text-muted-foreground">
        No candle data
      </div>
    )
  }

  const candleWidth = Math.max(3, Math.min(9, (CHART_WIDTH - PADDING.left - PADDING.right) / visible.length * 0.55))

  return (
    <div className="rounded-md border bg-background overflow-hidden">
      <svg viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} className="h-[300px] w-full">
        <rect x={0} y={0} width={CHART_WIDTH} height={CHART_HEIGHT} className="fill-background" />
        {ticks.map((tick) => {
          const y = candleY(tick, scale.min, scale.max)
          return (
            <g key={tick}>
              <line x1={PADDING.left} x2={CHART_WIDTH - PADDING.right + 8} y1={y} y2={y} className="stroke-border" strokeDasharray="4 6" />
              <text x={CHART_WIDTH - PADDING.right + 14} y={y + 4} className="fill-muted-foreground text-[11px] font-mono">
                {formatPrice(tick)}
              </text>
            </g>
          )
        })}
        {visible.map((candle, index) => {
          const x = candleX(index, visible.length)
          const openY = candleY(candle.open, scale.min, scale.max)
          const closeY = candleY(candle.close, scale.min, scale.max)
          const highY = candleY(candle.high, scale.min, scale.max)
          const lowY = candleY(candle.low, scale.min, scale.max)
          const rising = candle.close >= candle.open
          const bodyY = Math.min(openY, closeY)
          const bodyHeight = Math.max(Math.abs(openY - closeY), 1.5)
          const color = rising ? 'stroke-emerald-500 fill-emerald-500' : 'stroke-rose-500 fill-rose-500'
          const opacity = candle.closed ? 'opacity-100' : 'opacity-70'

          return (
            <g key={`${candle.open_time}-${index}`} className={`${color} ${opacity}`}>
              <line x1={x} x2={x} y1={highY} y2={lowY} strokeWidth={1.4} />
              <rect x={x - candleWidth / 2} y={bodyY} width={candleWidth} height={bodyHeight} rx={1} />
            </g>
          )
        })}
        <text x={PADDING.left} y={CHART_HEIGHT - 8} className="fill-muted-foreground text-[11px] font-mono">
          {formatClock(visible[0]?.open_time_iso)}
        </text>
        <text x={CHART_WIDTH - PADDING.right - 72} y={CHART_HEIGHT - 8} className="fill-muted-foreground text-[11px] font-mono">
          {formatClock(visible[visible.length - 1]?.open_time_iso)}
        </text>
      </svg>
    </div>
  )
}

export function MarketChartPanel() {
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [interval, setInterval] = useState<(typeof INTERVALS)[number]>('1m')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [market, setMarket] = useState<MarketKlinesData | null>(null)
  const [lastLoadedAt, setLastLoadedAt] = useState<string | null>(null)

  const latest = market?.latest
  const latestDirection = latest && latest.close >= latest.open ? 'up' : 'down'

  const loadMarket = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true)
    setError(null)
    try {
      const response = await endpoints.marketKlines(symbol.trim().toUpperCase(), interval, 120)
      if (!response.data.success || !response.data.data) {
        throw { message: response.data.message || 'Kline request failed', details: response.data }
      }
      setMarket(response.data.data)
      setLastLoadedAt(new Date().toISOString())
    } catch (err) {
      setError(err as ApiError)
    } finally {
      if (!quiet) setLoading(false)
    }
  }, [interval, symbol])

  useEffect(() => {
    void loadMarket()
  }, [loadMarket])

  useEffect(() => {
    if (!autoRefresh) return undefined
    const timer = window.setInterval(() => {
      void loadMarket(true)
    }, 3000)
    return () => window.clearInterval(timer)
  }, [autoRefresh, loadMarket])

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle className="text-sm font-mono font-medium flex items-center justify-between gap-3">
          <span className="inline-flex items-center gap-2">
            <ChartLine size={18} weight="bold" />
            Live Market Chart
          </span>
          <div className="flex items-center gap-2">
            <Badge variant={autoRefresh ? 'default' : 'secondary'}>
              {autoRefresh ? 'Live refresh' : 'Paused'}
            </Badge>
            {latest && (
              <Badge variant={latest.closed ? 'secondary' : 'outline'}>
                {latest.closed ? 'Last candle closed' : 'Current candle updating'}
              </Badge>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-[160px_140px_1fr_auto] gap-3 items-end">
          <div className="space-y-1">
            <Label htmlFor="market-symbol" className="text-xs">Symbol</Label>
            <Input
              id="market-symbol"
              value={symbol}
              onChange={(event) => setSymbol(event.target.value.toUpperCase())}
              className="font-mono text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Interval</Label>
            <Select value={interval} onValueChange={(value) => setInterval(value as typeof interval)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {INTERVALS.map((item) => (
                  <SelectItem key={item} value={item}>{item}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2 h-9">
            <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} id="market-live-refresh" />
            <Label htmlFor="market-live-refresh" className="text-xs text-muted-foreground">
              Refresh every 3s
            </Label>
          </div>
          <Button onClick={() => void loadMarket()} disabled={loading} variant="outline">
            {loading ? <LoadingSpinner size="sm" className="mr-2" /> : <ArrowClockwise size={16} className="mr-2" />}
            Refresh
          </Button>
        </div>

        {error && <ErrorPanel message={error.message} details={error.details} />}

        {latest && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
            <div>
              <div className="text-xs text-muted-foreground">Price</div>
              <div className={`font-mono font-medium ${latestDirection === 'up' ? 'text-emerald-600' : 'text-rose-600'}`}>
                {formatPrice(latest.close)}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">High / Low</div>
              <div className="font-mono">{formatPrice(latest.high)} / {formatPrice(latest.low)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Volume</div>
              <div className="font-mono">{formatPrice(latest.volume)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Candle Time</div>
              <div className="font-mono">{formatClock(latest.open_time_iso)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Loaded</div>
              <div className="font-mono">{formatClock(lastLoadedAt ?? market?.server_time)}</div>
            </div>
          </div>
        )}

        <MarketCandlesSvg candles={market?.candles ?? []} />
      </CardContent>
    </Card>
  )
}

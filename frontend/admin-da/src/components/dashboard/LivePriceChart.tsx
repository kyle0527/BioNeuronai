import { useState, useEffect, useMemo } from 'react'
import { Card } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { ChartLine, Clock } from '@phosphor-icons/react'
import type { PriceChartData } from '@/lib/types'

interface LivePriceChartProps {
  symbol: string
  onSymbolChange?: (symbol: string) => void
}

const AVAILABLE_SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT']
const TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']

export function LivePriceChart({ symbol, onSymbolChange }: LivePriceChartProps) {
  const [chartData, setChartData] = useState<PriceChartData | null>(null)
  const [interval, setInterval] = useState('15m')
  const [loading, setLoading] = useState(true)
  const [hoveredCandle, setHoveredCandle] = useState<number | null>(null)

  useEffect(() => {
    const fetchChartData = async () => {
      try {
        setLoading(true)
        const response = await fetch(
          `http://localhost:8000/api/v1/charts/${encodeURIComponent(symbol)}?interval=${interval}`
        )
        
        if (response.ok) {
          const data = await response.json()
          setChartData(data)
        } else {
          generateDemoData()
        }
      } catch {
        generateDemoData()
      } finally {
        setLoading(false)
      }
    }

    const generateDemoData = () => {
      const now = Date.now()
      const intervalMs = parseInterval(interval)
      const candles = Array.from({ length: 50 }, (_, i) => {
        const time = now - (49 - i) * intervalMs
        const basePrice = symbol === 'BTC/USDT' ? 43000 : 2250
        const volatility = basePrice * 0.02
        const open = basePrice + (Math.random() - 0.5) * volatility
        const close = open + (Math.random() - 0.5) * volatility
        const high = Math.max(open, close) + Math.random() * volatility * 0.5
        const low = Math.min(open, close) - Math.random() * volatility * 0.5
        const volume = Math.random() * 1000000

        return { time, open, high, low, close, volume }
      })

      setChartData({
        symbol,
        interval,
        candles,
        lastUpdated: new Date().toISOString()
      })
    }

    fetchChartData()

    const ws = new WebSocket('ws://localhost:8000/ws/charts')
    ws.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data)
        if (update.symbol === symbol && update.interval === interval) {
          setChartData(update)
        }
      } catch {}
    }

    return () => {
      ws.close()
    }
  }, [symbol, interval])

  const parseInterval = (interval: string): number => {
    const match = interval.match(/^(\d+)([mhd])$/)
    if (!match) return 900000
    const [, num, unit] = match
    const multiplier = { m: 60000, h: 3600000, d: 86400000 }[unit] || 60000
    return parseInt(num) * multiplier
  }

  const { min, max, priceRange } = useMemo(() => {
    if (!chartData?.candles.length) return { min: 0, max: 0, priceRange: 0 }
    const prices = chartData.candles.flatMap(c => [c.high, c.low])
    const min = Math.min(...prices)
    const max = Math.max(...prices)
    const priceRange = max - min
    return { min: min - priceRange * 0.1, max: max + priceRange * 0.1, priceRange: priceRange * 1.2 }
  }, [chartData])

  const lastPrice = chartData?.candles[chartData.candles.length - 1]?.close
  const firstPrice = chartData?.candles[0]?.open
  const priceChange = lastPrice && firstPrice ? ((lastPrice - firstPrice) / firstPrice) * 100 : 0

  if (loading || !chartData) {
    return (
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-9 w-24" />
          </div>
          <Skeleton className="h-[400px] w-full" />
        </div>
      </Card>
    )
  }

  const formatPrice = (price: number) => price.toLocaleString('en-US', { 
    minimumFractionDigits: 2, 
    maximumFractionDigits: 2 
  })

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <ChartLine size={24} className="text-primary" weight="duotone" />
              <Select value={symbol} onValueChange={onSymbolChange}>
                <SelectTrigger className="h-9 w-[160px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AVAILABLE_SYMBOLS.map(s => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Badge variant={priceChange >= 0 ? 'default' : 'destructive'}>
                {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
              </Badge>
            </div>
            <div className="font-mono text-2xl font-semibold">
              ${lastPrice ? formatPrice(lastPrice) : '—'}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {TIMEFRAMES.map(tf => (
              <button
                key={tf}
                onClick={() => setInterval(tf)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors rounded ${
                  interval === tf
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        <div className="relative h-[400px] border border-border rounded-lg bg-card/50 p-4">
          <svg width="100%" height="100%" className="overflow-visible">
            <defs>
              <linearGradient id="volumeGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="oklch(0.55 0.18 250)" stopOpacity="0.3" />
                <stop offset="100%" stopColor="oklch(0.55 0.18 250)" stopOpacity="0.05" />
              </linearGradient>
            </defs>

            {chartData.candles.map((candle, i) => {
              const x = (i / (chartData.candles.length - 1)) * 100
              const yHigh = ((max - candle.high) / priceRange) * 80 + 10
              const yLow = ((max - candle.low) / priceRange) * 80 + 10
              const yOpen = ((max - candle.open) / priceRange) * 80 + 10
              const yClose = ((max - candle.close) / priceRange) * 80 + 10
              const isUp = candle.close >= candle.open
              const bodyTop = Math.min(yOpen, yClose)
              const bodyHeight = Math.abs(yClose - yOpen) || 0.5

              return (
                <g key={i} onMouseEnter={() => setHoveredCandle(i)} onMouseLeave={() => setHoveredCandle(null)}>
                  <line
                    x1={`${x}%`}
                    y1={`${yHigh}%`}
                    x2={`${x}%`}
                    y2={`${yLow}%`}
                    stroke={isUp ? 'oklch(0.65 0.12 145)' : 'oklch(0.60 0.22 25)'}
                    strokeWidth="1"
                  />
                  <rect
                    x={`${x - 0.8}%`}
                    y={`${bodyTop}%`}
                    width="1.6%"
                    height={`${bodyHeight}%`}
                    fill={isUp ? 'oklch(0.65 0.12 145)' : 'oklch(0.60 0.22 25)'}
                    opacity={hoveredCandle === i ? 1 : 0.9}
                  />
                </g>
              )
            })}
          </svg>

          {hoveredCandle !== null && chartData.candles[hoveredCandle] && (
            <div className="absolute top-4 left-4 bg-card/95 border border-border rounded p-3 text-xs font-mono space-y-1 backdrop-blur-sm">
              <div className="font-semibold text-sm">{formatTime(chartData.candles[hoveredCandle].time)}</div>
              <div>O: ${formatPrice(chartData.candles[hoveredCandle].open)}</div>
              <div>H: ${formatPrice(chartData.candles[hoveredCandle].high)}</div>
              <div>L: ${formatPrice(chartData.candles[hoveredCandle].low)}</div>
              <div>C: ${formatPrice(chartData.candles[hoveredCandle].close)}</div>
              <div className="text-muted-foreground">
                Vol: {(chartData.candles[hoveredCandle].volume / 1000).toFixed(0)}K
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Clock size={14} />
          <span>Last updated: {new Date(chartData.lastUpdated).toLocaleTimeString()}</span>
        </div>
      </div>
    </Card>
  )
}

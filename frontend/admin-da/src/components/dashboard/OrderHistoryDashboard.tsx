import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Clock, TrendUp, TrendDown, ChartLine, ClockCounterClockwise } from '@phosphor-icons/react'
import type { OrderHistoryEntry, TradeAnalytics } from '@/lib/types'

export function OrderHistoryDashboard() {
  const [orders, setOrders] = useState<OrderHistoryEntry[]>([])
  const [analytics, setAnalytics] = useState<TradeAnalytics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [ordersRes, analyticsRes] = await Promise.all([
          fetch('http://localhost:8000/api/v1/orders/history'),
          fetch('http://localhost:8000/api/v1/analytics/trades')
        ])

        if (ordersRes.ok && analyticsRes.ok) {
          setOrders(await ordersRes.json())
          setAnalytics(await analyticsRes.json())
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
      const demoOrders: OrderHistoryEntry[] = Array.from({ length: 15 }, (_, i) => {
        const statuses: Array<OrderHistoryEntry['status']> = ['filled', 'filled', 'filled', 'cancelled', 'filled']
        const sides: Array<OrderHistoryEntry['side']> = ['buy', 'sell']
        const types: Array<OrderHistoryEntry['orderType']> = ['market', 'limit', 'stop_loss', 'take_profit']
        const symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']

        const status = statuses[Math.floor(Math.random() * statuses.length)]
        const side = sides[Math.floor(Math.random() * sides.length)]
        const orderType = types[Math.floor(Math.random() * types.length)]
        const symbol = symbols[Math.floor(Math.random() * symbols.length)]
        const quantity = Math.random() * 5
        const price = symbol === 'BTC/USDT' ? 43000 + Math.random() * 2000 : 2200 + Math.random() * 200
        const pnl = status === 'filled' ? (Math.random() - 0.4) * 500 : undefined

        return {
          id: `order-${i + 1}`,
          symbol,
          side,
          orderType,
          quantity,
          price,
          filledPrice: status === 'filled' ? price + (Math.random() - 0.5) * 10 : undefined,
          filledQuantity: status === 'filled' ? quantity : 0,
          status,
          createdAt: new Date(Date.now() - i * 3600000).toISOString(),
          updatedAt: new Date(Date.now() - i * 3600000 + 60000).toISOString(),
          fee: status === 'filled' ? quantity * price * 0.001 : undefined,
          pnl
        }
      })

      const demoAnalytics: TradeAnalytics = {
        totalTrades: 125,
        winRate: 62.4,
        averageWin: 245.50,
        averageLoss: -128.30,
        profitFactor: 1.91,
        totalPnl: 14652.30,
        bestTrade: 1234.56,
        worstTrade: -567.89,
        averageHoldTime: '4h 32m',
        lastUpdated: new Date().toISOString()
      }

      setOrders(demoOrders)
      setAnalytics(demoAnalytics)
    }

    fetchData()

    const ws = new WebSocket('ws://localhost:8000/ws/orders')
    ws.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data)
        setOrders(prev => [update, ...prev].slice(0, 50))
      } catch {}
    }

    return () => {
      ws.close()
    }
  }, [])

  const formatPrice = (price?: number) => price ? `$${price.toFixed(2)}` : '—'
  const formatPnl = (pnl?: number) => {
    if (pnl === undefined) return '—'
    const sign = pnl >= 0 ? '+' : ''
    return `${sign}$${pnl.toFixed(2)}`
  }

  const getStatusBadgeVariant = (status: OrderHistoryEntry['status']) => {
    switch (status) {
      case 'filled': return 'default'
      case 'cancelled': return 'secondary'
      case 'rejected': return 'destructive'
      default: return 'outline'
    }
  }

  if (loading) {
    return (
      <Card className="p-6">
        <div className="space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-[400px] w-full" />
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <Tabs defaultValue="analytics" className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ChartLine size={24} className="text-primary" weight="duotone" />
            <h2 className="font-semibold text-xl">Trading Performance</h2>
          </div>
          <TabsList>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="history">Order History</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="analytics" className="space-y-6 m-0">
          {analytics && (
            <>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-lg border border-border bg-card/50 p-4">
                  <div className="text-sm text-muted-foreground">Total P&L</div>
                  <div className={`font-mono font-semibold text-2xl ${analytics.totalPnl >= 0 ? 'text-success' : 'text-destructive'}`}>
                    {formatPnl(analytics.totalPnl)}
                  </div>
                </div>

                <div className="rounded-lg border border-border bg-card/50 p-4">
                  <div className="text-sm text-muted-foreground">Win Rate</div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-semibold text-2xl">{analytics.winRate.toFixed(1)}%</span>
                    <TrendUp size={20} className="text-success" weight="bold" />
                  </div>
                </div>

                <div className="rounded-lg border border-border bg-card/50 p-4">
                  <div className="text-sm text-muted-foreground">Profit Factor</div>
                  <div className="font-mono font-semibold text-2xl">{analytics.profitFactor.toFixed(2)}</div>
                </div>

                <div className="rounded-lg border border-border bg-card/50 p-4">
                  <div className="text-sm text-muted-foreground">Total Trades</div>
                  <div className="font-mono font-semibold text-2xl">{analytics.totalTrades}</div>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-4 rounded-lg border border-border bg-card/30 p-4">
                  <h3 className="font-medium text-sm uppercase tracking-wide text-muted-foreground">Trade Statistics</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Average Win</span>
                      <span className="font-mono font-medium text-success">{formatPnl(analytics.averageWin)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Average Loss</span>
                      <span className="font-mono font-medium text-destructive">{formatPnl(analytics.averageLoss)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Best Trade</span>
                      <span className="font-mono font-medium text-success">{formatPnl(analytics.bestTrade)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Worst Trade</span>
                      <span className="font-mono font-medium text-destructive">{formatPnl(analytics.worstTrade)}</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4 rounded-lg border border-border bg-card/30 p-4">
                  <h3 className="font-medium text-sm uppercase tracking-wide text-muted-foreground">Performance Metrics</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Average Hold Time</span>
                      <span className="font-mono font-medium">{analytics.averageHoldTime}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Win/Loss Ratio</span>
                      <span className="font-mono font-medium">
                        {(Math.abs(analytics.averageWin / analytics.averageLoss)).toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Clock size={14} />
                <span>Last updated: {new Date(analytics.lastUpdated).toLocaleTimeString()}</span>
              </div>
            </>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-4 m-0">
          <div className="rounded-lg border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Side</TableHead>
                  <TableHead className="text-right">Quantity</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="text-right">Filled</TableHead>
                  <TableHead className="text-right">P&L</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                      <div className="flex flex-col items-center gap-2">
                        <ClockCounterClockwise size={32} weight="duotone" className="text-muted-foreground/50" />
                        <p>No order history</p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  orders.map((order) => (
                    <TableRow key={order.id}>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {new Date(order.createdAt).toLocaleTimeString('en-US', { 
                          month: 'short', 
                          day: 'numeric', 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </TableCell>
                      <TableCell className="font-medium">{order.symbol}</TableCell>
                      <TableCell className="capitalize text-sm">{order.orderType.replace('_', ' ')}</TableCell>
                      <TableCell>
                        <Badge variant={order.side === 'buy' ? 'default' : 'outline'} className="text-xs">
                          {order.side.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-right">{order.quantity.toFixed(4)}</TableCell>
                      <TableCell className="font-mono text-right">{formatPrice(order.price)}</TableCell>
                      <TableCell className="font-mono text-right">{formatPrice(order.filledPrice)}</TableCell>
                      <TableCell className={`font-mono text-right font-medium ${
                        order.pnl !== undefined ? (order.pnl >= 0 ? 'text-success' : 'text-destructive') : ''
                      }`}>
                        {formatPnl(order.pnl)}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(order.status)} className="text-xs capitalize">
                          {order.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  )
}

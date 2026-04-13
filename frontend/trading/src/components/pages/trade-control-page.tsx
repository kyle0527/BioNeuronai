import { useState, useCallback, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { StatusBadge } from '@/components/status-badge'
import { toast } from 'sonner'
import { api } from '@/lib/api-client'
import { useWebSocket } from '@/hooks/use-websocket'
import type { TradeControlResponse } from '@/lib/types'
import { 
  Play, 
  Stop, 
  Warning, 
  Circle, 
  Bell, 
  BellSlash, 
  Plus, 
  Trash, 
  ArrowUp, 
  ArrowDown,
  WifiHigh,
  WifiSlash
} from '@phosphor-icons/react'

interface PriceAlert {
  id: string
  symbol: string
  targetPrice: number
  type: 'above' | 'below'
  active: boolean
  createdAt: string
}

interface OrderBookEntry {
  price: number
  quantity: number
  total: number
}

interface OrderBookData {
  symbol: string
  bids: OrderBookEntry[]
  asks: OrderBookEntry[]
  lastUpdate: string
}

interface TradeExecution {
  id: string
  timestamp: string
  symbol: string
  type: 'buy' | 'sell'
  price: number
  quantity: number
  status: 'executed' | 'pending' | 'failed'
}

export function TradeControlPage() {
  const [tradingStatus, setTradingStatus] = useState<'stopped' | 'running'>('stopped')
  const [lastResponse, setLastResponse] = useState<TradeControlResponse | null>(null)
  const [showStartDialog, setShowStartDialog] = useState(false)
  const [loading, setLoading] = useState(false)
  
  const [priceAlerts, setPriceAlerts] = useState<PriceAlert[]>(() => {
    try {
      const stored = localStorage.getItem('bioneuronai-price-alerts')
      return stored ? JSON.parse(stored) : []
    } catch { return [] }
  })
  useEffect(() => {
    localStorage.setItem('bioneuronai-price-alerts', JSON.stringify(priceAlerts))
  }, [priceAlerts])
  const [showAddAlertDialog, setShowAddAlertDialog] = useState(false)
  const [newAlert, setNewAlert] = useState({ symbol: 'BTCUSDT', targetPrice: '', type: 'above' as 'above' | 'below' })
  
  const [wsEnabled, setWsEnabled] = useState(false)
  const [liveExecutions, setLiveExecutions] = useState<TradeExecution[]>([])
  const [orderBookData, setOrderBookData] = useState<OrderBookData | null>(null)
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT')

  const handleWebSocketMessage = useCallback((data: any) => {
    if (!data || !data.type) return

    switch (data.type) {
      case 'trade_execution':
        if (data.trade) {
          const newExecution: TradeExecution = {
            id: data.trade.id,
            timestamp: data.trade.timestamp,
            symbol: data.trade.symbol,
            type: data.trade.type,
            price: data.trade.price,
            quantity: data.trade.quantity,
            status: data.trade.status
          }
          setLiveExecutions((prev) => [newExecution, ...prev.slice(0, 49)])
          toast.success(`Trade executed: ${newExecution.type.toUpperCase()} ${newExecution.symbol}`, {
            description: `${newExecution.quantity} @ $${newExecution.price.toFixed(2)}`
          })
        }
        break
      
      case 'orderbook_update':
        if (data.orderbook && data.orderbook.symbol === selectedSymbol) {
          setOrderBookData({
            symbol: data.orderbook.symbol,
            bids: data.orderbook.bids || [],
            asks: data.orderbook.asks || [],
            lastUpdate: new Date().toISOString()
          })
        }
        break

      case 'price_update':
        if (data.price && data.symbol) {
          const currentPrice = data.price
          setPriceAlerts((currentAlerts) => {
            if (!currentAlerts) return []
            return currentAlerts.map(alert => {
              if (!alert.active || alert.symbol !== data.symbol) return alert
              
              const shouldTrigger = 
                (alert.type === 'above' && currentPrice >= alert.targetPrice) ||
                (alert.type === 'below' && currentPrice <= alert.targetPrice)
              
              if (shouldTrigger) {
                toast.info(`Price Alert: ${alert.symbol}`, {
                  description: `Price ${currentPrice.toFixed(2)} ${alert.type} target ${alert.targetPrice.toFixed(2)}`
                })
                return { ...alert, active: false }
              }
              
              return alert
            })
          })
        }
        break

      default:
        console.log('Unknown WebSocket message type:', data.type)
    }
  }, [selectedSymbol])

  const { status: wsStatus } = useWebSocket('/ws/trade', {
    enabled: wsEnabled,
    onMessage: handleWebSocketMessage,
    onOpen: () => {
      toast.success('WebSocket connected', {
        description: 'Real-time trade updates enabled'
      })
    },
    onClose: () => {
      if (wsEnabled) {
        toast.info('WebSocket disconnected', {
          description: 'Attempting to reconnect...'
        })
      }
    },
    onError: (error) => {
      console.error('WebSocket error:', error)
    },
  })

  const handleStartTrading = async () => {
    try {
      setLoading(true)
      const response = await api.startTrading()
      setLastResponse(response)
      setTradingStatus('running')
      setShowStartDialog(false)
      toast.success('Trading started')
    } catch (error) {
      toast.error('Failed to start trading')
    } finally {
      setLoading(false)
    }
  }

  const handleStopTrading = async () => {
    try {
      setLoading(true)
      const response = await api.stopTrading()
      setLastResponse(response)
      setTradingStatus('stopped')
      toast.success('Trading stopped')
    } catch (error) {
      toast.error('Failed to stop trading')
    } finally {
      setLoading(false)
    }
  }

  const handleAddAlert = () => {
    const price = parseFloat(newAlert.targetPrice)
    if (isNaN(price) || price <= 0) {
      toast.error('Invalid price', {
        description: 'Please enter a valid target price'
      })
      return
    }

    const alert: PriceAlert = {
      id: Date.now().toString(),
      symbol: newAlert.symbol,
      targetPrice: price,
      type: newAlert.type,
      active: true,
      createdAt: new Date().toISOString()
    }

    setPriceAlerts((current) => current ? [alert, ...current] : [alert])
    setShowAddAlertDialog(false)
    setNewAlert({ symbol: 'BTCUSDT', targetPrice: '', type: 'above' })
    toast.success('Price alert created', {
      description: `${alert.symbol} ${alert.type} $${alert.targetPrice.toFixed(2)}`
    })
  }

  const handleDeleteAlert = (id: string) => {
    setPriceAlerts((current) => current ? current.filter(a => a.id !== id) : [])
    toast.success('Alert deleted')
  }

  const handleToggleAlert = (id: string) => {
    setPriceAlerts((current) =>
      current ? current.map(a => a.id === id ? { ...a, active: !a.active } : a) : []
    )
  }

  useEffect(() => {
    if (wsEnabled && selectedSymbol) {
      setOrderBookData({
        symbol: selectedSymbol,
        bids: [
          { price: 42850, quantity: 1.2, total: 51420 },
          { price: 42840, quantity: 0.8, total: 34272 },
          { price: 42830, quantity: 2.1, total: 89943 },
          { price: 42820, quantity: 0.5, total: 21410 },
          { price: 42810, quantity: 1.7, total: 72777 },
        ],
        asks: [
          { price: 42860, quantity: 0.9, total: 38574 },
          { price: 42870, quantity: 1.5, total: 64305 },
          { price: 42880, quantity: 0.7, total: 30016 },
          { price: 42890, quantity: 2.3, total: 98647 },
          { price: 42900, quantity: 0.4, total: 17160 },
        ],
        lastUpdate: new Date().toISOString()
      })
    }
  }, [wsEnabled, selectedSymbol])

  const safeAlerts = priceAlerts || []

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <h1 className="text-3xl font-bold font-mono">Trade Control</h1>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 border border-border rounded-md bg-card">
            <Label htmlFor="websocket-toggle-trade" className="text-xs cursor-pointer">
              Live Updates
            </Label>
            <Switch
              id="websocket-toggle-trade"
              checked={wsEnabled}
              onCheckedChange={setWsEnabled}
            />
            {wsEnabled ? (
              <div className="flex items-center gap-1.5">
                <Circle 
                  size={8} 
                  weight="fill" 
                  className={
                    wsStatus === 'connected' 
                      ? 'text-green-500 animate-pulse' 
                      : wsStatus === 'connecting' 
                      ? 'text-yellow-500 animate-pulse'
                      : 'text-red-500'
                  }
                />
                <WifiHigh size={16} className="text-primary" />
              </div>
            ) : (
              <WifiSlash size={16} className="text-muted-foreground" />
            )}
          </div>
        </div>
      </div>

      <Alert variant="destructive" className="border-2">
        <Warning className="h-5 w-5" />
        <AlertTitle className="font-bold">High-Risk Trading Warning</AlertTitle>
        <AlertDescription>
          Live trading involves significant financial risk. Always test strategies on testnet first. 
          Never trade with funds you cannot afford to lose. This system operates autonomously once started.
        </AlertDescription>
      </Alert>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Trading Status</CardTitle>
            <CardDescription>Current trading execution state</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Status</span>
              <StatusBadge 
                status={tradingStatus === 'running' ? 'success' : 'default'}
                label={tradingStatus}
              />
            </div>

            {lastResponse && (
              <div className="space-y-3 pt-4 border-t">
                <div>
                  <p className="text-xs text-muted-foreground">Last Action</p>
                  <p className="text-sm">{lastResponse.status}</p>
                </div>
                {lastResponse.message && (
                  <div>
                    <p className="text-xs text-muted-foreground">Message</p>
                    <p className="text-sm">{lastResponse.message}</p>
                  </div>
                )}
                {lastResponse.timestamp && (
                  <div>
                    <p className="text-xs text-muted-foreground">Timestamp</p>
                    <p className="text-sm font-mono">{new Date(lastResponse.timestamp).toLocaleString()}</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Controls</CardTitle>
            <CardDescription>Start or stop trading operations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={() => setShowStartDialog(true)}
              disabled={tradingStatus === 'running' || loading}
              className="w-full"
              size="lg"
            >
              <Play className="mr-2" />
              Start Trading
            </Button>

            <Button
              onClick={handleStopTrading}
              disabled={tradingStatus === 'stopped' || loading}
              variant="destructive"
              className="w-full"
              size="lg"
            >
              <Stop className="mr-2" />
              Stop Trading
            </Button>

            <div className="pt-4 border-t">
              <p className="text-xs text-muted-foreground">
                Starting trading will begin autonomous execution based on configured strategies. 
                Monitor positions carefully and use stop-loss protection.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg font-semibold">Price Alerts</CardTitle>
              <CardDescription>Get notified when assets hit target prices</CardDescription>
            </div>
            <Button size="sm" onClick={() => setShowAddAlertDialog(true)}>
              <Plus className="mr-2" size={16} />
              Add Alert
            </Button>
          </CardHeader>
          <CardContent>
            {safeAlerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Bell size={48} className="text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground">No price alerts configured</p>
                <p className="text-xs text-muted-foreground mt-1">Create an alert to get notified of price changes</p>
              </div>
            ) : (
              <div className="space-y-3">
                {safeAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="flex items-center justify-between p-3 border border-border rounded-md"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleToggleAlert(alert.id)}
                        className="p-0 h-auto hover:bg-transparent"
                      >
                        {alert.active ? (
                          <Bell size={20} className="text-primary" />
                        ) : (
                          <BellSlash size={20} className="text-muted-foreground" />
                        )}
                      </Button>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-medium text-sm">{alert.symbol}</span>
                          <Badge variant={alert.active ? 'default' : 'secondary'} className="text-xs">
                            {alert.active ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          Notify when {alert.type} ${alert.targetPrice.toFixed(2)}
                        </p>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDeleteAlert(alert.id)}
                    >
                      <Trash size={16} />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg font-semibold">Order Book</CardTitle>
              <CardDescription>Real-time market depth</CardDescription>
            </div>
            <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BTCUSDT">BTC/USDT</SelectItem>
                <SelectItem value="ETHUSDT">ETH/USDT</SelectItem>
                <SelectItem value="SOLUSDT">SOL/USDT</SelectItem>
              </SelectContent>
            </Select>
          </CardHeader>
          <CardContent>
            {!wsEnabled ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <WifiSlash size={48} className="text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground">Enable live updates to view order book</p>
              </div>
            ) : !orderBookData ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Circle size={48} className="text-muted-foreground mb-3 animate-pulse" />
                <p className="text-sm text-muted-foreground">Loading order book...</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-muted-foreground">ASKS</span>
                    <ArrowUp size={14} className="text-red-500" />
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-xs">Price</TableHead>
                        <TableHead className="text-xs text-right">Quantity</TableHead>
                        <TableHead className="text-xs text-right">Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {orderBookData.asks.slice(0, 5).reverse().map((ask, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-mono text-xs text-red-500">${ask.price.toFixed(2)}</TableCell>
                          <TableCell className="font-mono text-xs text-right">{ask.quantity.toFixed(4)}</TableCell>
                          <TableCell className="font-mono text-xs text-right">${ask.total.toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <Separator />

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-muted-foreground">BIDS</span>
                    <ArrowDown size={14} className="text-green-500" />
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-xs">Price</TableHead>
                        <TableHead className="text-xs text-right">Quantity</TableHead>
                        <TableHead className="text-xs text-right">Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {orderBookData.bids.slice(0, 5).map((bid, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-mono text-xs text-green-500">${bid.price.toFixed(2)}</TableCell>
                          <TableCell className="font-mono text-xs text-right">{bid.quantity.toFixed(4)}</TableCell>
                          <TableCell className="font-mono text-xs text-right">${bid.total.toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Live Trade Executions</CardTitle>
          <CardDescription>Recent trades executed in real-time</CardDescription>
        </CardHeader>
        <CardContent>
          {!wsEnabled ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <WifiSlash size={48} className="text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground">Enable live updates to see trade executions</p>
            </div>
          ) : liveExecutions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Circle size={48} className="text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground">Waiting for trade executions...</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="text-right">Quantity</TableHead>
                  <TableHead className="text-right">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {liveExecutions.map((execution) => (
                  <TableRow key={execution.id}>
                    <TableCell className="text-xs text-muted-foreground">
                      {new Date(execution.timestamp).toLocaleTimeString()}
                    </TableCell>
                    <TableCell className="font-mono font-medium">{execution.symbol}</TableCell>
                    <TableCell>
                      <Badge variant={execution.type === 'buy' ? 'default' : 'secondary'} className="text-xs">
                        {execution.type.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-right">${execution.price.toFixed(2)}</TableCell>
                    <TableCell className="font-mono text-right">{execution.quantity.toFixed(4)}</TableCell>
                    <TableCell className="text-right">
                      <Badge
                        variant={
                          execution.status === 'executed' ? 'default' :
                          execution.status === 'pending' ? 'secondary' :
                          'destructive'
                        }
                        className="text-xs"
                      >
                        {execution.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Safety Checklist</CardTitle>
          <CardDescription>Verify these items before starting live trading</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            <li className="flex items-start gap-3">
              <div className="mt-0.5 h-2 w-2 rounded-full bg-primary" />
              <div>
                <p className="text-sm font-medium">Strategy Backtested</p>
                <p className="text-xs text-muted-foreground">Verify strategy performance on historical data</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <div className="mt-0.5 h-2 w-2 rounded-full bg-primary" />
              <div>
                <p className="text-sm font-medium">Testnet Validated</p>
                <p className="text-xs text-muted-foreground">Test with simulated funds before real money</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <div className="mt-0.5 h-2 w-2 rounded-full bg-primary" />
              <div>
                <p className="text-sm font-medium">Risk Limits Set</p>
                <p className="text-xs text-muted-foreground">Configure maximum position size and stop-loss levels</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <div className="mt-0.5 h-2 w-2 rounded-full bg-primary" />
              <div>
                <p className="text-sm font-medium">Monitoring Enabled</p>
                <p className="text-xs text-muted-foreground">Set up alerts and check positions regularly</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <div className="mt-0.5 h-2 w-2 rounded-full bg-primary" />
              <div>
                <p className="text-sm font-medium">Capital Allocated</p>
                <p className="text-xs text-muted-foreground">Only use funds you can afford to lose</p>
              </div>
            </li>
          </ul>
        </CardContent>
      </Card>

      <Dialog open={showStartDialog} onOpenChange={setShowStartDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Start Trading</DialogTitle>
            <DialogDescription>
              Are you sure you want to start live trading? This will begin autonomous trade execution.
            </DialogDescription>
          </DialogHeader>
          <Alert variant="destructive">
            <Warning className="h-4 w-4" />
            <AlertDescription className="text-sm">
              You acknowledge that you have tested this strategy and understand the risks involved in live trading.
            </AlertDescription>
          </Alert>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowStartDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleStartTrading} disabled={loading}>
              {loading ? 'Starting...' : 'Confirm Start'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showAddAlertDialog} onOpenChange={setShowAddAlertDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Price Alert</DialogTitle>
            <DialogDescription>
              Set up notifications when an asset reaches your target price
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="alert-symbol">Symbol</Label>
              <Select value={newAlert.symbol} onValueChange={(val) => setNewAlert({ ...newAlert, symbol: val })}>
                <SelectTrigger id="alert-symbol">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="BTCUSDT">BTC/USDT</SelectItem>
                  <SelectItem value="ETHUSDT">ETH/USDT</SelectItem>
                  <SelectItem value="SOLUSDT">SOL/USDT</SelectItem>
                  <SelectItem value="ADAUSDT">ADA/USDT</SelectItem>
                  <SelectItem value="DOGEUSDT">DOGE/USDT</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="alert-price">Target Price ($)</Label>
              <Input
                id="alert-price"
                type="number"
                step="0.01"
                placeholder="Enter target price"
                value={newAlert.targetPrice}
                onChange={(e) => setNewAlert({ ...newAlert, targetPrice: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="alert-type">Alert Type</Label>
              <Select value={newAlert.type} onValueChange={(val) => setNewAlert({ ...newAlert, type: val as 'above' | 'below' })}>
                <SelectTrigger id="alert-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="above">Price Goes Above</SelectItem>
                  <SelectItem value="below">Price Goes Below</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddAlertDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddAlert}>
              Create Alert
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

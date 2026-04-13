import { useState, useMemo, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { 
  TrendUp, 
  TrendDown, 
  Calendar,
  ArrowUp,
  ArrowDown,
  Database,
  FileArrowDown,
  FileCsv,
  ArrowsClockwise,
  WifiHigh,
  WifiSlash,
  Circle
} from '@phosphor-icons/react'
import { toast } from 'sonner'
import type { Trade, PortfolioAsset, PerformanceDataPoint } from '@/lib/analytics-types'
import { populateMockData } from '@/lib/mock-data-generator'
import { exportPortfolioAsCSV, exportTradesAsCSV, exportFullAnalyticsReport } from '@/lib/export-utils'
import { api } from '@/lib/api-client'
import { useWebSocket } from '@/hooks/use-websocket'
import type { WebSocketStatus } from '@/hooks/use-websocket'

type TimeRange = '7d' | '30d' | '90d' | '1y' | 'all'
type DataSource = 'live' | 'mock'

export function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<TimeRange>('30d')
  const [dataSource, setDataSource] = useState<DataSource>('live')
  const [trades, setTrades] = useState<Trade[]>([])
  const [portfolio, setPortfolio] = useState<PortfolioAsset[]>([])
  const [performanceData, setPerformanceData] = useState<PerformanceDataPoint[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [wsEnabled, setWsEnabled] = useState(false)

  const safePortfolio = portfolio || []
  const safeTrades = trades || []
  const safePerformanceData = performanceData || []

  const handleWebSocketMessage = useCallback((data: any) => {
    if (!data || !data.type) return

    switch (data.type) {
      case 'portfolio_update':
        if (data.portfolio) {
          const mappedPortfolio: PortfolioAsset[] = data.portfolio.map((p: any) => ({
            symbol: p.symbol,
            quantity: p.quantity,
            avgPrice: p.avg_price || p.avgPrice,
            currentPrice: p.current_price || p.currentPrice,
            value: p.value,
            pnl: p.pnl,
            pnlPercent: p.pnl_percent || p.pnlPercent,
            allocation: p.allocation
          }))
          setPortfolio(mappedPortfolio)
          setLastUpdated(new Date().toISOString())
        }
        break
      
      case 'trade_executed':
        if (data.trade) {
          const newTrade: Trade = {
            id: data.trade.id,
            timestamp: data.trade.timestamp,
            symbol: data.trade.symbol,
            type: data.trade.type,
            quantity: data.trade.quantity,
            price: data.trade.price,
            pnl: data.trade.pnl,
            status: data.trade.status
          }
          setTrades((prev) => [newTrade, ...prev])
          setLastUpdated(new Date().toISOString())
          toast.success(`Trade executed: ${newTrade.type.toUpperCase()} ${newTrade.symbol}`, {
            description: `Quantity: ${newTrade.quantity} @ $${newTrade.price}`
          })
        }
        break
      
      case 'performance_update':
        if (data.performance) {
          const mappedPerformance: PerformanceDataPoint[] = data.performance.map((p: any) => ({
            date: p.date,
            pnl: p.pnl,
            dailyPnl: p.daily_pnl || p.dailyPnl,
            value: p.value
          }))
          setPerformanceData(mappedPerformance)
          setLastUpdated(new Date().toISOString())
        }
        break

      default:
        console.log('Unknown WebSocket message type:', data.type)
    }
  }, [])

  const { status: wsStatus, reconnect } = useWebSocket('/ws/analytics', {
    enabled: wsEnabled,
    onMessage: handleWebSocketMessage,
    onOpen: () => {
      toast.success('WebSocket connected', {
        description: 'Real-time updates enabled'
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

  const timeRangeToDays = (range: TimeRange): number => {
    switch (range) {
      case '7d': return 7
      case '30d': return 30
      case '90d': return 90
      case '1y': return 365
      case 'all': return 999999
      default: return 30
    }
  }

  const fetchLiveData = async () => {
    setIsLoading(true)
    try {
      const days = timeRangeToDays(timeRange)
      
      const [portfolioResponse, tradesResponse, performanceResponse] = await Promise.all([
        api.getAnalyticsPortfolio(),
        api.getAnalyticsTrades(100),
        api.getAnalyticsPerformance(days)
      ])

      const mappedPortfolio: PortfolioAsset[] = portfolioResponse.portfolio.map(p => ({
        symbol: p.symbol,
        quantity: p.quantity,
        avgPrice: p.avg_price,
        currentPrice: p.current_price,
        value: p.value,
        pnl: p.pnl,
        pnlPercent: p.pnl_percent,
        allocation: p.allocation
      }))

      const mappedTrades: Trade[] = tradesResponse.trades

      const mappedPerformance: PerformanceDataPoint[] = performanceResponse.performance.map(p => ({
        date: p.date,
        pnl: p.pnl,
        dailyPnl: p.daily_pnl,
        value: p.value
      }))

      setPortfolio(mappedPortfolio)
      setTrades(mappedTrades)
      setPerformanceData(mappedPerformance)
      setLastUpdated(new Date().toISOString())
      setDataSource('live')
      
      toast.success('Live data loaded', {
        description: `${mappedPortfolio.length} positions, ${mappedTrades.length} trades`
      })
    } catch (error) {
      toast.error('Failed to fetch live data', {
        description: error instanceof Error ? error.message : 'Backend may be unavailable'
      })
      console.error('Analytics API error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerateMockData = () => {
    setIsGenerating(true)
    try {
      const mockData = populateMockData()
      setTrades(mockData.trades)
      setPortfolio(mockData.portfolio)
      setPerformanceData(mockData.performance)
      setDataSource('mock')
      setLastUpdated(new Date().toISOString())
      toast.success('Mock data generated successfully', {
        description: `Generated ${mockData.trades.length} trades and ${mockData.portfolio.length} portfolio positions`
      })
    } catch (error) {
      toast.error('Failed to generate mock data', {
        description: error instanceof Error ? error.message : 'Unknown error'
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const handleRefreshLiveData = () => {
    fetchLiveData()
  }

  useEffect(() => {
    fetchLiveData()
  }, [timeRange])

  const handleExportPortfolio = () => {
    try {
      exportPortfolioAsCSV(safePortfolio)
      toast.success('Portfolio exported', {
        description: 'Downloaded as CSV file'
      })
    } catch (error) {
      toast.error('Failed to export portfolio', {
        description: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }

  const handleExportTrades = () => {
    try {
      exportTradesAsCSV(safeTrades)
      toast.success('Trades exported', {
        description: 'Downloaded as CSV file'
      })
    } catch (error) {
      toast.error('Failed to export trades', {
        description: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }

  const handleExportFullReport = () => {
    try {
      exportFullAnalyticsReport(safePortfolio, safeTrades)
      toast.success('Full report exported', {
        description: 'Downloaded as CSV file'
      })
    } catch (error) {
      toast.error('Failed to export report', {
        description: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }

  const formatLastUpdated = (timestamp: string | null) => {
    if (!timestamp) return 'Never'
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins === 1) return '1 minute ago'
    if (diffMins < 60) return `${diffMins} minutes ago`
    
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours === 1) return '1 hour ago'
    if (diffHours < 24) return `${diffHours} hours ago`
    
    return date.toLocaleString()
  }

  const totalValue = useMemo(() => {
    return safePortfolio.reduce((sum, asset) => sum + asset.value, 0)
  }, [safePortfolio])

  const totalPnL = useMemo(() => {
    return safePortfolio.reduce((sum, asset) => sum + asset.pnl, 0)
  }, [safePortfolio])

  const totalPnLPercent = useMemo(() => {
    const invested = totalValue - totalPnL
    return invested !== 0 ? (totalPnL / invested) * 100 : 0
  }, [totalValue, totalPnL])

  const winRate = useMemo(() => {
    const completedTrades = safeTrades.filter(t => t.status === 'completed')
    if (completedTrades.length === 0) return 0
    const winningTrades = completedTrades.filter(t => t.pnl > 0).length
    return (winningTrades / completedTrades.length) * 100
  }, [safeTrades])

  const recentTrades = useMemo(() => {
    return [...safeTrades]
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 10)
  }, [safeTrades])

  const pieColors = ['oklch(0.65 0.15 200)', 'oklch(0.75 0.15 80)', 'oklch(0.7 0.15 150)', 'oklch(0.6 0.15 280)', 'oklch(0.68 0.15 340)']

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-mono">Performance Analytics</h1>
          <div className="flex items-center gap-3 mt-1">
            <p className="text-muted-foreground">Portfolio tracking and P&L visualization</p>
            <Badge variant={dataSource === 'live' ? 'default' : 'secondary'} className="text-xs">
              {dataSource === 'live' ? 'Live Data' : 'Mock Data'}
            </Badge>
            {wsEnabled && (
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
                <span className="text-xs text-muted-foreground">
                  {wsStatus === 'connected' && 'Live'}
                  {wsStatus === 'connecting' && 'Connecting'}
                  {wsStatus === 'disconnected' && 'Disconnected'}
                  {wsStatus === 'error' && 'Error'}
                </span>
              </div>
            )}
            <span className="text-xs text-muted-foreground">
              Updated: {formatLastUpdated(lastUpdated)}
            </span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 border border-border rounded-md bg-card">
            <Label htmlFor="websocket-toggle" className="text-xs cursor-pointer">
              Real-time
            </Label>
            <Switch
              id="websocket-toggle"
              checked={wsEnabled}
              onCheckedChange={setWsEnabled}
            />
            {wsEnabled ? (
              <WifiHigh size={16} className="text-primary" />
            ) : (
              <WifiSlash size={16} className="text-muted-foreground" />
            )}
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleRefreshLiveData}
            disabled={isLoading}
          >
            <ArrowsClockwise className="mr-2" size={16} />
            {isLoading ? 'Loading...' : 'Refresh Live'}
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleGenerateMockData}
            disabled={isGenerating}
          >
            <Database className="mr-2" size={16} />
            {isGenerating ? 'Generating...' : 'Mock Data'}
          </Button>
          <Select value={timeRange} onValueChange={(val) => setTimeRange(val as TimeRange)} disabled={isLoading}>
            <SelectTrigger className="w-32">
              <Calendar className="mr-2" size={16} />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">7 Days</SelectItem>
              <SelectItem value="30d">30 Days</SelectItem>
              <SelectItem value="90d">90 Days</SelectItem>
              <SelectItem value="1y">1 Year</SelectItem>
              <SelectItem value="all">All Time</SelectItem>
            </SelectContent>
          </Select>
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleExportPortfolio}
            disabled={safePortfolio.length === 0}
          >
            <FileCsv className="mr-2" size={16} />
            Portfolio
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleExportTrades}
            disabled={safeTrades.length === 0}
          >
            <FileCsv className="mr-2" size={16} />
            Trades
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleExportFullReport}
            disabled={safePortfolio.length === 0 && safeTrades.length === 0}
          >
            <FileArrowDown className="mr-2" size={16} />
            Full Report
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          <>
            {[...Array(4)].map((_, i) => (
              <Card key={i}>
                <CardHeader className="pb-3">
                  <Skeleton className="h-3 w-32" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-40 mb-2" />
                  <Skeleton className="h-4 w-24" />
                </CardContent>
              </Card>
            ))}
          </>
        ) : (
          <>
            <Card className="transition-all hover:shadow-md hover:translate-y-[-2px]">
              <CardHeader className="pb-3">
                <CardDescription className="text-xs">Total Portfolio Value</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold font-mono">{formatCurrency(totalValue)}</div>
                <div className="flex items-center gap-2 mt-2">
                  {totalPnL >= 0 ? (
                    <ArrowUp className="text-green-500" size={16} weight="bold" />
                  ) : (
                    <ArrowDown className="text-red-500" size={16} weight="bold" />
                  )}
                  <span className={`text-sm font-medium ${totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {formatCurrency(Math.abs(totalPnL))} ({formatPercent(totalPnLPercent)})
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="transition-all hover:shadow-md hover:translate-y-[-2px]">
              <CardHeader className="pb-3">
                <CardDescription className="text-xs">Total P&L</CardDescription>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold font-mono ${totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {formatCurrency(totalPnL)}
                </div>
                <div className="flex items-center gap-2 mt-2">
                  {totalPnL >= 0 ? (
                    <TrendUp className="text-green-500" size={16} weight="bold" />
                  ) : (
                    <TrendDown className="text-red-500" size={16} weight="bold" />
                  )}
                  <span className="text-sm text-muted-foreground">
                    {formatPercent(totalPnLPercent)} return
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="transition-all hover:shadow-md hover:translate-y-[-2px]">
              <CardHeader className="pb-3">
                <CardDescription className="text-xs">Win Rate</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold font-mono">{winRate.toFixed(1)}%</div>
                <div className="text-sm text-muted-foreground mt-2">
                  {safeTrades.filter(t => t.status === 'completed' && t.pnl > 0).length} / {safeTrades.filter(t => t.status === 'completed').length} trades
                </div>
              </CardContent>
            </Card>

            <Card className="transition-all hover:shadow-md hover:translate-y-[-2px]">
              <CardHeader className="pb-3">
                <CardDescription className="text-xs">Total Trades</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold font-mono">{safeTrades.length}</div>
                <div className="text-sm text-muted-foreground mt-2">
                  {safeTrades.filter(t => t.status === 'completed').length} completed
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Portfolio Performance</CardTitle>
            <CardDescription>Cumulative P&L over time</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(10)].map((_, i) => (
                  <div key={i} className="flex items-center justify-between py-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-20" />
                  </div>
                ))}
              </div>
            ) : safePerformanceData.length === 0 ? (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                <p className="text-sm">No performance data available</p>
              </div>
            ) : (
              <div className="space-y-3">
                {safePerformanceData.slice(-10).map((item, index) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b last:border-0">
                    <span className="text-sm font-mono">{item.date}</span>
                    <span className={`text-sm font-mono font-medium ${item.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {formatCurrency(item.pnl)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Asset Allocation</CardTitle>
            <CardDescription>Portfolio distribution by asset</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Skeleton className="h-4 w-20" />
                      <Skeleton className="h-4 w-12" />
                    </div>
                    <Skeleton className="h-2 w-full" />
                  </div>
                ))}
              </div>
            ) : safePortfolio.length === 0 ? (
              <div className="flex items-center justify-center h-[250px] text-muted-foreground">
                <p className="text-sm">No assets in portfolio</p>
              </div>
            ) : (
              <div className="space-y-4">
                {safePortfolio.map((asset, index) => (
                  <div key={asset.symbol} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: pieColors[index % pieColors.length] }}
                        />
                        <span className="font-mono font-medium">{asset.symbol}</span>
                      </div>
                      <span className="font-mono">{asset.allocation.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div 
                        className="h-2 rounded-full transition-all" 
                        style={{ 
                          width: `${asset.allocation}%`,
                          backgroundColor: pieColors[index % pieColors.length]
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Portfolio Holdings</CardTitle>
            <CardDescription>{safePortfolio.length} positions</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead className="text-right">Quantity</TableHead>
                  <TableHead className="text-right">Value</TableHead>
                  <TableHead className="text-right">P&L</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {safePortfolio.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                      No holdings in portfolio
                    </TableCell>
                  </TableRow>
                ) : (
                  safePortfolio.map((asset) => (
                    <TableRow key={asset.symbol}>
                      <TableCell className="font-mono font-medium">{asset.symbol}</TableCell>
                      <TableCell className="text-right font-mono">{asset.quantity.toFixed(4)}</TableCell>
                      <TableCell className="text-right font-mono">{formatCurrency(asset.value)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex flex-col items-end">
                          <span className={`font-mono font-medium ${asset.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                            {formatCurrency(asset.pnl)}
                          </span>
                          <span className={`text-xs ${asset.pnl >= 0 ? 'text-green-500/70' : 'text-red-500/70'}`}>
                            {formatPercent(asset.pnlPercent)}
                          </span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Recent Trades</CardTitle>
            <CardDescription>Last {recentTrades.length} trades</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Symbol</TableHead>
                  <TableHead className="text-right">Type</TableHead>
                  <TableHead className="text-right">P&L</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentTrades.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                      No trades executed yet
                    </TableCell>
                  </TableRow>
                ) : (
                  recentTrades.map((trade) => (
                    <TableRow key={trade.id}>
                      <TableCell className="text-xs text-muted-foreground">{formatDate(trade.timestamp)}</TableCell>
                      <TableCell className="font-mono font-medium">{trade.symbol}</TableCell>
                      <TableCell className="text-right">
                        <Badge variant={trade.type === 'buy' ? 'default' : 'secondary'} className="text-xs">
                          {trade.type.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <span className={`font-mono font-medium ${trade.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                          {formatCurrency(trade.pnl)}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

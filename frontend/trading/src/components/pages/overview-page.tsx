import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { StatusBadge } from '@/components/status-badge'
import { DataTable } from '@/components/data-table'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { api } from '@/lib/api-client'
import type { SystemStatus, BacktestCatalog, BacktestRun, NewsSentiment, PretradeChecklist } from '@/lib/types'
import { CheckCircle, XCircle, Warning, ArrowsClockwise, Newspaper, ListChecks } from '@phosphor-icons/react'

export function OverviewPage() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [catalog, setCatalog] = useState<BacktestCatalog | null>(null)
  const [recentRuns, setRecentRuns] = useState<BacktestRun[]>([])
  const [sentiment, setSentiment] = useState<NewsSentiment | null>(null)
  const [pretrade, setPretrade] = useState<PretradeChecklist | null>(null)
  
  const [newsSymbol, setNewsSymbol] = useState('BTCUSDT')
  const [pretradeSymbol, setPretradeSymbol] = useState('BTCUSDT')
  const [pretradeAction, setPretradeAction] = useState<'buy' | 'sell'>('buy')
  
  const [loading, setLoading] = useState({
    status: true,
    catalog: true,
    runs: true,
    sentiment: false,
    pretrade: false,
  })

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    await Promise.all([
      loadSystemStatus(),
      loadCatalog(),
      loadRecentRuns(),
    ])
  }

  const loadSystemStatus = async () => {
    try {
      setLoading(prev => ({ ...prev, status: true }))
      const data = await api.getStatus()
      setSystemStatus(data)
    } catch (error) {
      toast.error('Failed to load system status')
    } finally {
      setLoading(prev => ({ ...prev, status: false }))
    }
  }

  const loadCatalog = async () => {
    try {
      setLoading(prev => ({ ...prev, catalog: true }))
      const data = await api.getBacktestCatalog()
      setCatalog(data)
    } catch (error) {
      toast.error('Failed to load backtest catalog')
    } finally {
      setLoading(prev => ({ ...prev, catalog: false }))
    }
  }

  const loadRecentRuns = async () => {
    try {
      setLoading(prev => ({ ...prev, runs: true }))
      const data = await api.getBacktestRuns(10)
      setRecentRuns(data.runs)
    } catch (error) {
      toast.error('Failed to load recent runs')
    } finally {
      setLoading(prev => ({ ...prev, runs: false }))
    }
  }

  const runNewsSentiment = async () => {
    try {
      setLoading(prev => ({ ...prev, sentiment: true }))
      const data = await api.getNewsSentiment(newsSymbol)
      setSentiment(data)
      toast.success('News sentiment analysis complete')
    } catch (error) {
      toast.error('Failed to analyze news sentiment')
    } finally {
      setLoading(prev => ({ ...prev, sentiment: false }))
    }
  }

  const runPretradeChecklist = async () => {
    try {
      setLoading(prev => ({ ...prev, pretrade: true }))
      const data = await api.getPretradeChecklist(pretradeSymbol, pretradeAction)
      setPretrade(data)
      toast.success('Pretrade checklist complete')
    } catch (error) {
      toast.error('Failed to run pretrade checklist')
    } finally {
      setLoading(prev => ({ ...prev, pretrade: false }))
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold font-mono">Overview</h1>
        <Button onClick={loadInitialData} variant="outline" size="sm">
          <ArrowsClockwise className="mr-2" />
          Refresh All
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              System Status
            </CardTitle>
            <CardDescription>Module availability and health</CardDescription>
          </CardHeader>
          <CardContent>
            {loading.status ? (
              <div className="space-y-2">
                {[...Array(4)].map((_, i) => (
                  <Skeleton key={i} className="h-8 w-full" />
                ))}
              </div>
            ) : systemStatus ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Overall Status</span>
                  <StatusBadge 
                    status={systemStatus.status === 'healthy' ? 'success' : 'error'} 
                    label={systemStatus.status}
                  />
                </div>
                {Object.entries(systemStatus.modules).map(([module, status]) => (
                  <div key={module} className="flex items-center justify-between py-2 border-t">
                    <span className="text-sm capitalize font-mono">{module.replace('_', ' ')}</span>
                    <StatusBadge 
                      status={status === true || status === 'online' ? 'success' : 'error'} 
                      label={String(status)}
                    />
                  </div>
                ))}
                {systemStatus.timestamp && (
                  <p className="text-xs text-muted-foreground mt-4">
                    Last checked: {new Date(systemStatus.timestamp).toLocaleString()}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No data available</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Backtest Catalog</CardTitle>
            <CardDescription>Available datasets</CardDescription>
          </CardHeader>
          <CardContent>
            {loading.catalog ? (
              <div className="space-y-2">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            ) : catalog ? (
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-4xl font-bold font-mono">{catalog.dataset_count}</div>
                  <p className="text-sm text-muted-foreground">Datasets</p>
                </div>
                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground">Root</p>
                  <p className="text-sm font-mono break-all">{catalog.root}</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No data available</p>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Recent Backtest Runs</CardTitle>
            <CardDescription>Last 10 backtest executions</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={recentRuns}
              isLoading={loading.runs}
              emptyMessage="No recent runs"
              columns={[
                { key: 'symbol', header: 'Symbol' },
                { key: 'interval', header: 'Interval' },
                { key: 'start_date', header: 'Start Date' },
                { key: 'end_date', header: 'End Date' },
                { 
                  key: 'balance', 
                  header: 'Balance',
                  render: (run) => `$${run.balance.toLocaleString()}`,
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (run) => (
                    <StatusBadge
                      status={
                        run.status === 'completed' ? 'success' :
                        run.status === 'failed' ? 'error' :
                        run.status === 'running' ? 'info' : 'warning'
                      }
                      label={run.status}
                    />
                  ),
                },
                { key: 'created_at', header: 'Created', render: (run) => new Date(run.created_at).toLocaleDateString() },
              ]}
              onRowClick={(run) => {
                toast.info(`View details for run ${run.id}`)
              }}
            />
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Newspaper />
              News Sentiment Analysis
            </CardTitle>
            <CardDescription>Get market sentiment for a symbol</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <div className="flex-1">
                <Label htmlFor="news-symbol">Symbol</Label>
                <Input
                  id="news-symbol"
                  value={newsSymbol}
                  onChange={(e) => setNewsSymbol(e.target.value)}
                  placeholder="BTCUSDT"
                />
              </div>
              <div className="flex items-end">
                <Button onClick={runNewsSentiment} disabled={loading.sentiment}>
                  {loading.sentiment ? 'Analyzing...' : 'Analyze'}
                </Button>
              </div>
            </div>
            {sentiment && (
              <div className="space-y-3 pt-4 border-t">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{sentiment.symbol}</span>
                  <StatusBadge 
                    status={
                      sentiment.sentiment === 'positive' ? 'success' :
                      sentiment.sentiment === 'negative' ? 'error' : 'warning'
                    }
                    label={sentiment.sentiment}
                  />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Sentiment Score</p>
                  <p className="text-2xl font-bold font-mono">{sentiment.score.toFixed(2)}</p>
                </div>
                {sentiment.highlights && sentiment.highlights.length > 0 && (
                  <div>
                    <p className="text-xs text-muted-foreground mb-2">Highlights</p>
                    <ul className="space-y-1">
                      {sentiment.highlights.map((highlight, i) => (
                        <li key={i} className="text-sm">• {highlight}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ListChecks />
              Pretrade Checklist
            </CardTitle>
            <CardDescription>Validate trade conditions</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="pretrade-symbol">Symbol</Label>
              <Input
                id="pretrade-symbol"
                value={pretradeSymbol}
                onChange={(e) => setPretradeSymbol(e.target.value)}
                placeholder="BTCUSDT"
              />
            </div>
            <div className="space-y-2">
              <Label>Action</Label>
              <div className="flex gap-2">
                <Button 
                  variant={pretradeAction === 'buy' ? 'default' : 'outline'} 
                  onClick={() => setPretradeAction('buy')}
                  className="flex-1"
                >
                  Buy
                </Button>
                <Button 
                  variant={pretradeAction === 'sell' ? 'default' : 'outline'} 
                  onClick={() => setPretradeAction('sell')}
                  className="flex-1"
                >
                  Sell
                </Button>
              </div>
            </div>
            <Button onClick={runPretradeChecklist} disabled={loading.pretrade} className="w-full">
              {loading.pretrade ? 'Checking...' : 'Run Checklist'}
            </Button>
            {pretrade && (
              <div className="space-y-2 pt-4 border-t">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold">Overall</span>
                  <StatusBadge 
                    status={
                      pretrade.overall_status === 'pass' ? 'success' :
                      pretrade.overall_status === 'fail' ? 'error' : 'warning'
                    }
                    label={pretrade.overall_status}
                  />
                </div>
                {pretrade.checks.map((check, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm py-2 border-t">
                    {check.status === 'pass' ? <CheckCircle className="text-green-500 mt-0.5" size={16} /> :
                     check.status === 'fail' ? <XCircle className="text-red-500 mt-0.5" size={16} /> :
                     <Warning className="text-amber-500 mt-0.5" size={16} />}
                    <div className="flex-1">
                      <p className="font-medium">{check.name}</p>
                      <p className="text-xs text-muted-foreground">{check.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

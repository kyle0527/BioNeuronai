import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DataTable } from '@/components/data-table'
import { StatusBadge } from '@/components/status-badge'
import { toast } from 'sonner'
import { api } from '@/lib/api-client'
import type { BacktestConfig, BacktestInspectResponse, BacktestSimulateResponse, BacktestRunResponse } from '@/lib/types'
import { MagnifyingGlass, Flask, Play } from '@phosphor-icons/react'

export function BacktestPage() {
  const [config, setConfig] = useState<BacktestConfig>({
    symbol: 'BTCUSDT',
    interval: '1h',
    start_date: '2024-01-01',
    end_date: '2024-01-31',
    balance: 10000,
    warmup_bars: 50,
    bars: 1000,
  })

  const [inspectResult, setInspectResult] = useState<BacktestInspectResponse | null>(null)
  const [simulateResult, setSimulateResult] = useState<BacktestSimulateResponse | null>(null)
  const [runResult, setRunResult] = useState<BacktestRunResponse | null>(null)
  const [runs, setRuns] = useState<any[]>([])

  const [loading, setLoading] = useState({
    inspect: false,
    simulate: false,
    run: false,
  })

  const handleInspect = async () => {
    try {
      setLoading(prev => ({ ...prev, inspect: true }))
      const result = await api.inspectBacktest(config)
      setInspectResult(result)
      toast.success('Inspection complete')
    } catch (error) {
      toast.error('Inspection failed')
    } finally {
      setLoading(prev => ({ ...prev, inspect: false }))
    }
  }

  const handleSimulate = async () => {
    try {
      setLoading(prev => ({ ...prev, simulate: true }))
      const result = await api.simulateBacktest(config)
      setSimulateResult(result)
      toast.success('Simulation complete')
    } catch (error) {
      toast.error('Simulation failed')
    } finally {
      setLoading(prev => ({ ...prev, simulate: false }))
    }
  }

  const handleRun = async () => {
    try {
      setLoading(prev => ({ ...prev, run: true }))
      const result = await api.runBacktest(config)
      setRunResult(result)
      toast.success(`Backtest started: ${result.run_id}`)
      setRuns(prev => [...prev, { id: result.run_id, ...config, status: result.status, created_at: new Date().toISOString() }])
    } catch (error) {
      toast.error('Backtest run failed')
    } finally {
      setLoading(prev => ({ ...prev, run: false }))
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold font-mono">Backtest</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
            <CardDescription>Set backtest parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="symbol">Symbol</Label>
                <Input
                  id="symbol"
                  value={config.symbol}
                  onChange={(e) => setConfig({ ...config, symbol: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="interval">Interval</Label>
                <Input
                  id="interval"
                  value={config.interval}
                  onChange={(e) => setConfig({ ...config, interval: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={config.start_date}
                  onChange={(e) => setConfig({ ...config, start_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="end_date">End Date</Label>
                <Input
                  id="end_date"
                  type="date"
                  value={config.end_date}
                  onChange={(e) => setConfig({ ...config, end_date: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="balance">Initial Balance</Label>
              <Input
                id="balance"
                type="number"
                value={config.balance}
                onChange={(e) => setConfig({ ...config, balance: Number(e.target.value) })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="warmup_bars">Warmup Bars</Label>
                <Input
                  id="warmup_bars"
                  type="number"
                  value={config.warmup_bars}
                  onChange={(e) => setConfig({ ...config, warmup_bars: Number(e.target.value) })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bars">Bars</Label>
                <Input
                  id="bars"
                  type="number"
                  value={config.bars}
                  onChange={(e) => setConfig({ ...config, bars: Number(e.target.value) })}
                />
              </div>
            </div>

            <div className="flex gap-2 pt-4">
              <Button onClick={handleInspect} disabled={loading.inspect} variant="outline" className="flex-1">
                <MagnifyingGlass className="mr-2" />
                {loading.inspect ? 'Inspecting...' : 'Inspect'}
              </Button>
              <Button onClick={handleSimulate} disabled={loading.simulate} variant="outline" className="flex-1">
                <Flask className="mr-2" />
                {loading.simulate ? 'Simulating...' : 'Simulate'}
              </Button>
              <Button onClick={handleRun} disabled={loading.run} className="flex-1">
                <Play className="mr-2" />
                {loading.run ? 'Running...' : 'Run'}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
            <CardDescription>Backtest operation results</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="inspect">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="inspect">Inspect</TabsTrigger>
                <TabsTrigger value="simulate">Simulate</TabsTrigger>
                <TabsTrigger value="run">Run</TabsTrigger>
              </TabsList>
              <TabsContent value="inspect" className="space-y-3 pt-4">
                {inspectResult ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-xs text-muted-foreground">Symbol</p>
                        <p className="font-mono">{inspectResult.symbol}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Data Points</p>
                        <p className="font-mono">{inspectResult.data_points}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Start</p>
                        <p className="font-mono text-sm">{inspectResult.start_date}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">End</p>
                        <p className="font-mono text-sm">{inspectResult.end_date}</p>
                      </div>
                    </div>
                    {inspectResult.warnings && inspectResult.warnings.length > 0 && (
                      <div className="pt-3 border-t">
                        <p className="text-xs text-muted-foreground mb-2">Warnings</p>
                        <ul className="space-y-1">
                          {inspectResult.warnings.map((w, i) => (
                            <li key={i} className="text-sm text-amber-500">⚠ {w}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No inspection results yet</p>
                )}
              </TabsContent>
              <TabsContent value="simulate" className="space-y-3 pt-4">
                {simulateResult ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-xs text-muted-foreground">Trades</p>
                        <p className="font-mono text-xl">{simulateResult.trades_count}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Final Balance</p>
                        <p className="font-mono text-xl">${simulateResult.final_balance.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">PnL</p>
                        <p className={`font-mono text-xl ${simulateResult.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                          ${simulateResult.pnl.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">PnL %</p>
                        <p className={`font-mono text-xl ${simulateResult.pnl_percentage >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                          {simulateResult.pnl_percentage.toFixed(2)}%
                        </p>
                      </div>
                    </div>
                    {simulateResult.max_drawdown !== undefined && (
                      <div className="pt-3 border-t">
                        <p className="text-xs text-muted-foreground">Max Drawdown</p>
                        <p className="font-mono text-red-500">{simulateResult.max_drawdown.toFixed(2)}%</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No simulation results yet</p>
                )}
              </TabsContent>
              <TabsContent value="run" className="space-y-3 pt-4">
                {runResult ? (
                  <div className="space-y-3">
                    <div>
                      <p className="text-xs text-muted-foreground">Run ID</p>
                      <p className="font-mono text-sm">{runResult.run_id}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Status</p>
                      <StatusBadge status="info" label={runResult.status} />
                    </div>
                    {runResult.message && (
                      <div>
                        <p className="text-xs text-muted-foreground">Message</p>
                        <p className="text-sm">{runResult.message}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No run results yet</p>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Run History</CardTitle>
          <CardDescription>All backtest runs</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            data={runs}
            emptyMessage="No runs yet - execute a backtest to see results"
            columns={[
              { key: 'id', header: 'Run ID', render: (r) => r.id.substring(0, 8) },
              { key: 'symbol', header: 'Symbol' },
              { key: 'interval', header: 'Interval' },
              { key: 'start_date', header: 'Start' },
              { key: 'end_date', header: 'End' },
              { key: 'balance', header: 'Balance', render: (r) => `$${r.balance.toLocaleString()}` },
              { key: 'status', header: 'Status', render: (r) => <StatusBadge status="info" label={r.status} /> },
            ]}
            onRowClick={(run) => toast.info(`View details for run ${run.id}`)}
          />
        </CardContent>
      </Card>
    </div>
  )
}

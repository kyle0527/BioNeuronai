import { useState } from 'react'
import { Play, MagnifyingGlass, ListBullets, Gauge } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { JSONViewer } from '@/components/JSONViewer'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { endpoints, type ApiError } from '@/lib/api'

const INTERVALS = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']

export function BacktestPanel() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [data, setData] = useState<unknown>(null)
  const [activeTab, setActiveTab] = useState('run')

  // Shared fields
  const [symbol, setSymbol] = useState('ETHUSDT')
  const [interval, setInterval] = useState('1h')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  // Run / Simulate fields
  const [balance, setBalance] = useState(10000)
  const [warmupBars, setWarmupBars] = useState(100)
  const [bars, setBars] = useState(200)

  const execute = async () => {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      let response
      switch (activeTab) {
        case 'catalog':
          response = await endpoints.backtestCatalog(symbol || undefined, interval || undefined)
          break
        case 'inspect':
          response = await endpoints.backtestInspect(symbol, interval, startDate || undefined, endDate || undefined)
          break
        case 'simulate':
          response = await endpoints.backtestSimulate({
            symbol, interval, balance, bars,
            start_date: startDate || null,
            end_date: endDate || null,
          })
          break
        case 'run':
          response = await endpoints.backtestRun({
            symbol, interval, balance, warmup_bars: warmupBars,
            start_date: startDate || null,
            end_date: endDate || null,
          })
          break
        case 'runs':
          response = await endpoints.backtestRuns(10)
          break
      }
      setData(response?.data ?? null)
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  const tabConfig: Record<string, { label: string; icon: React.ReactNode; showParams: boolean; showBars: boolean; showWarmup: boolean }> = {
    catalog: { label: 'Catalog', icon: <ListBullets size={14} />, showParams: false, showBars: false, showWarmup: false },
    inspect:  { label: 'Inspect',  icon: <MagnifyingGlass size={14} />, showParams: true, showBars: false, showWarmup: false },
    simulate: { label: 'Simulate', icon: <Gauge size={14} />, showParams: true, showBars: true, showWarmup: false },
    run:      { label: 'Run',      icon: <Play size={14} />, showParams: true, showBars: false, showWarmup: true },
    runs:     { label: 'History',  icon: <ListBullets size={14} />, showParams: false, showBars: false, showWarmup: false },
  }

  const tab = tabConfig[activeTab]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-mono font-medium">Backtest Operations</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs value={activeTab} onValueChange={(v) => { setActiveTab(v); setData(null); setError(null) }}>
          <TabsList className="grid grid-cols-5 w-full">
            {Object.entries(tabConfig).map(([key, cfg]) => (
              <TabsTrigger key={key} value={key} className="gap-1 text-xs">
                {cfg.icon} {cfg.label}
              </TabsTrigger>
            ))}
          </TabsList>

          {/* Shared param fields, rendered outside TabsContent so they persist */}
          {(tab.showParams || tab.showBars || tab.showWarmup) && (
            <div className="grid grid-cols-2 gap-2 mt-3">
              <div className="space-y-1">
                <Label htmlFor="bt-symbol" className="text-xs">Symbol</Label>
                <Input
                  id="bt-symbol"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                  placeholder="ETHUSDT"
                  className="font-mono text-sm"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="bt-interval" className="text-xs">Interval</Label>
                <select
                  id="bt-interval"
                  value={interval}
                  onChange={(e) => setInterval(e.target.value)}
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                >
                  {INTERVALS.map((i) => (
                    <option key={i} value={i}>{i}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <Label htmlFor="bt-start" className="text-xs">Start Date</Label>
                <Input
                  id="bt-start"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="text-sm"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="bt-end" className="text-xs">End Date</Label>
                <Input
                  id="bt-end"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="text-sm"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="bt-balance" className="text-xs">Balance (USDT)</Label>
                <Input
                  id="bt-balance"
                  type="number"
                  min={1}
                  value={balance}
                  onChange={(e) => setBalance(Number(e.target.value))}
                  className="font-mono text-sm"
                />
              </div>
              {tab.showWarmup && (
                <div className="space-y-1">
                  <Label htmlFor="bt-warmup" className="text-xs">Warmup Bars</Label>
                  <Input
                    id="bt-warmup"
                    type="number"
                    min={0}
                    value={warmupBars}
                    onChange={(e) => setWarmupBars(Number(e.target.value))}
                    className="font-mono text-sm"
                  />
                </div>
              )}
              {tab.showBars && (
                <div className="space-y-1">
                  <Label htmlFor="bt-bars" className="text-xs">Bars (1–5000)</Label>
                  <Input
                    id="bt-bars"
                    type="number"
                    min={1}
                    max={5000}
                    value={bars}
                    onChange={(e) => setBars(Math.min(5000, Math.max(1, Number(e.target.value))))}
                    className="font-mono text-sm"
                  />
                </div>
              )}
            </div>
          )}

          {/* Catalog / Runs — no params needed, just a description */}
          <TabsContent value="catalog" className="mt-2">
            <p className="text-xs text-muted-foreground">List all available historical datasets. Optionally filter by symbol/interval above.</p>
          </TabsContent>
          <TabsContent value="inspect" className="mt-2">
            <p className="text-xs text-muted-foreground">Check if the selected dataset can be loaded by the replay engine.</p>
          </TabsContent>
          <TabsContent value="simulate" className="mt-2">
            <p className="text-xs text-muted-foreground">Run a quick simulation summary on the selected dataset.</p>
          </TabsContent>
          <TabsContent value="run" className="mt-2">
            <p className="text-xs text-muted-foreground">Execute a full backtest and store the run result.</p>
          </TabsContent>
          <TabsContent value="runs" className="mt-2">
            <p className="text-xs text-muted-foreground">Fetch the 10 most recent backtest runs.</p>
          </TabsContent>
        </Tabs>

        <Button onClick={execute} disabled={loading} className="w-full gap-2">
          {loading ? <LoadingSpinner size="sm" /> : tab.icon}
          {tab.label}
        </Button>

        {error && <ErrorPanel message={error.message} details={error.details} />}

        {data && !error && (
          <>
            <Separator />
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">Response:</p>
              <JSONViewer data={data} maxHeight="400px" />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

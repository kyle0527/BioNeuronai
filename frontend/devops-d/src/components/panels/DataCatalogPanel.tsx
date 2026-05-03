import { useState } from 'react'
import { Database, ArrowClockwise, MagnifyingGlass } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { endpoints, type ApiError } from '@/lib/api'

interface Dataset {
  symbol: string
  interval: string
  start_date?: string | null
  end_date?: string | null
  zip_count?: number
  bar_count?: number
}

interface CatalogData {
  root?: string
  dataset_count?: number
  datasets?: Dataset[]
}

export function DataCatalogPanel() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [catalog, setCatalog] = useState<CatalogData | null>(null)
  const [symbol, setSymbol] = useState('')
  const [interval, setInterval] = useState('')

  const fetchCatalog = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await endpoints.dataCatalog(symbol || undefined, interval || undefined)
      const body = res.data as { success: boolean; data?: CatalogData; message?: string }
      if (body.success) {
        setCatalog(body.data ?? null)
      } else {
        setError({ message: body.message ?? '掃描失敗' })
      }
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  const datasets = catalog?.datasets ?? []

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-sm font-mono font-medium flex items-center gap-2">
          <Database size={16} weight="bold" />
          本地歷史資料
        </CardTitle>
        <Button size="sm" variant="ghost" onClick={fetchCatalog} disabled={loading}>
          {loading ? <LoadingSpinner size="sm" /> : <ArrowClockwise size={16} />}
        </Button>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 篩選列 */}
        <div className="flex gap-2">
          <div className="flex-1 space-y-1">
            <Label className="text-xs font-mono text-muted-foreground">Symbol（選填）</Label>
            <Input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="BTCUSDT"
              className="font-mono text-xs h-8"
            />
          </div>
          <div className="flex-1 space-y-1">
            <Label className="text-xs font-mono text-muted-foreground">Interval（選填）</Label>
            <Input
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
              placeholder="1h"
              className="font-mono text-xs h-8"
            />
          </div>
          <div className="flex items-end">
            <Button size="sm" variant="outline" onClick={fetchCatalog} disabled={loading} className="h-8 gap-1">
              <MagnifyingGlass size={14} />
              掃描
            </Button>
          </div>
        </div>

        {error && <ErrorPanel message={error.message} details={error.details} />}

        {!catalog && !error && !loading && (
          <p className="text-sm text-muted-foreground">點擊「掃描」查詢本地已下載的資料</p>
        )}

        {catalog && (
          <>
            <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
              <span>根目錄：{catalog.root ?? 'backtest/data'}</span>
              <Badge variant="secondary" className="ml-auto">
                {catalog.dataset_count ?? datasets.length} 筆
              </Badge>
            </div>

            <Separator />

            {datasets.length === 0 ? (
              <div className="rounded-md bg-yellow-50 border border-yellow-200 px-3 py-3 space-y-1">
                <p className="text-xs font-mono font-semibold text-yellow-800">尚無本地資料</p>
                <p className="text-xs text-yellow-700">請在終端機執行以下指令下載：</p>
                <code className="block text-xs bg-yellow-100 rounded px-2 py-1 text-yellow-900 mt-1">
                  python main.py backtest-data --symbol BTCUSDT --interval 1h
                </code>
              </div>
            ) : (
              <div className="space-y-1.5">
                {datasets.map((ds, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 rounded-md border border-border bg-muted/20 px-3 py-2 text-xs font-mono"
                  >
                    <span className="font-semibold w-20 shrink-0">{ds.symbol}</span>
                    <Badge variant="outline" className="text-[10px] px-1.5 py-0">{ds.interval}</Badge>
                    <span className="text-muted-foreground flex-1">
                      {ds.start_date ?? '?'} ~ {ds.end_date ?? '?'}
                    </span>
                    {ds.zip_count !== undefined && (
                      <span className="text-muted-foreground">{ds.zip_count} zip</span>
                    )}
                    {ds.bar_count !== undefined && (
                      <span className="text-muted-foreground">{ds.bar_count.toLocaleString()} bars</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}

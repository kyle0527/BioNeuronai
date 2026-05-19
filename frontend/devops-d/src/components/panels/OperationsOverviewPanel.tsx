import { useEffect, useMemo, useState } from 'react'
import {
  ArrowClockwise,
  CheckCircle,
  Database,
  Gauge,
  ShieldCheck,
  WarningCircle,
} from '@phosphor-icons/react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import {
  endpoints,
  type ApiError,
  type DashboardSnapshot,
  type RestApiResponse,
  type StatusResponse,
} from '@/lib/api'

type RuntimeStatus = {
  running?: boolean
  mode?: string
  request?: {
    symbol?: string
    mode?: string
    testnet?: boolean
    auto_trade?: boolean
    load_ai_model?: boolean
  }
  engine?: {
    auto_trade?: boolean
    paper_trading?: boolean
    ai_model_loaded?: boolean
    enable_ai_model?: boolean
  }
  paper?: {
    log_dir?: string
    account?: {
      balance?: number
      total_equity?: number
      positions_count?: number
      open_orders_count?: number
    }
    stats?: {
      total_trades?: number
      total_return?: number
    }
  }
}

type ModelStatus = {
  active_model?: {
    model_name?: string
    model_path?: string
    materialized_path?: string
  }
  active_model_name?: string
  active_model_path?: string
  active_model_exists?: boolean
  active_model_source?: string
  running_engine?: {
    ai_model_loaded?: boolean
    enable_ai_model?: boolean
  }
  trade_engine?: {
    engine?: {
      ai_model_loaded?: boolean
      enable_ai_model?: boolean
    }
  }
}

function getActiveModelName(model: ModelStatus | null) {
  return model?.active_model?.model_name ?? model?.active_model_name ?? '-'
}

function getActiveModelPath(model: ModelStatus | null) {
  return model?.active_model?.materialized_path ?? model?.active_model?.model_path ?? model?.active_model_path ?? ''
}

function getModelLoaded(model: ModelStatus | null) {
  return model?.trade_engine?.engine?.ai_model_loaded ?? model?.running_engine?.ai_model_loaded ?? false
}

function getModelExists(model: ModelStatus | null) {
  const path = getActiveModelPath(model)
  if (typeof model?.active_model_exists === 'boolean') {
    return model.active_model_exists
  }
  return path.length > 0
}

type FlattenedModelStatus = {
  activeModelName: string
  modelExists: boolean
  modelLoaded: boolean
}

function flattenModelStatus(model: ModelStatus | null): FlattenedModelStatus {
  return {
    activeModelName: getActiveModelName(model),
    modelExists: getModelExists(model),
    modelLoaded: getModelLoaded(model),
  }
}

type OverviewState = {
  system: StatusResponse | null
  runtime: RuntimeStatus | null
  model: ModelStatus | null
  dashboard: DashboardSnapshot | null
}

const modeLabels: Record<string, string> = {
  monitor_only: 'Monitor only',
  paper_live: 'Paper live',
  testnet_auto: 'Testnet auto',
  live_auto: 'Live auto',
}

function unwrapRestData<T>(value: unknown): T | null {
  if (value && typeof value === 'object' && 'data' in value) {
    return (value as RestApiResponse<T>).data ?? null
  }
  return value as T
}

function formatNumber(value: unknown, digits = 2) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : '-'
}

function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return ok ? (
    <Badge className="bg-success text-success-foreground">{label}</Badge>
  ) : (
    <Badge variant="destructive">{label}</Badge>
  )
}

function FactRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono text-right">{value}</span>
    </div>
  )
}

export function OperationsOverviewPanel() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [state, setState] = useState<OverviewState>({
    system: null,
    runtime: null,
    model: null,
    dashboard: null,
  })
  const [lastUpdate, setLastUpdate] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [system, runtime, model, dashboard] = await Promise.all([
        endpoints.status(),
        endpoints.tradeStatus(),
        endpoints.modelStatus(),
        endpoints.dashboard(),
      ])

      setState({
        system: system.data,
        runtime: unwrapRestData<RuntimeStatus>(runtime.data),
        model: unwrapRestData<ModelStatus>(model.data),
        dashboard: dashboard.data,
      })
      setLastUpdate(new Date().toLocaleTimeString())
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const runtimeMode = state.runtime?.request?.mode ?? state.runtime?.mode ?? state.dashboard?.environment ?? 'unknown'
  const modeLabel = modeLabels[runtimeMode] ?? runtimeMode
  const running = state.runtime?.running === true
  const paperTrading = state.runtime?.engine?.paper_trading === true || runtimeMode === 'paper_live'
  const liveMode = runtimeMode === 'live_auto'
  const testnetMode = runtimeMode === 'testnet_auto' || state.runtime?.request?.testnet === true
  const executionLabel = paperTrading
    ? 'Virtual paper ledger'
    : liveMode
      ? 'Binance mainnet orders'
      : testnetMode
        ? 'Binance testnet'
        : 'No order execution'
  const marketDataLabel = paperTrading || liveMode
    ? 'Binance mainnet market data'
    : testnetMode
      ? 'Binance testnet market data'
      : 'Runtime connector / local data'
  const unavailableModules = useMemo(
    () => state.system?.modules?.filter((module) => !module.available) ?? [],
    [state.system],
  )
  const readinessIssues = useMemo(
    () => state.system?.readiness?.filter((item) => !item.available) ?? [],
    [state.system],
  )
  const blockingItems = state.system?.blocking ?? []
  const modelStatus = flattenModelStatus(state.model)

  return (
    <Card className="lg:col-span-2">
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div className="space-y-2">
          <CardTitle className="text-base font-mono font-medium">Operations Overview</CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge ok={state.system?.ready === true} label={state.system?.ready ? 'Runtime ready' : 'Readiness needed'} />
            <Badge variant={running ? 'default' : 'secondary'}>{running ? 'Runtime running' : 'Runtime stopped'}</Badge>
            <Badge variant={paperTrading ? 'outline' : liveMode ? 'destructive' : 'secondary'}>
              {modeLabel}
            </Badge>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdate && <span className="text-xs text-muted-foreground">Updated {lastUpdate}</span>}
          <Button size="sm" variant="outline" onClick={load} disabled={loading}>
            {loading ? <LoadingSpinner size="sm" /> : <ArrowClockwise size={16} />}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {error && <ErrorPanel message={error.message} details={error.details} />}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Gauge size={16} />
              Runtime
            </div>
            <FactRow label="Symbol" value={state.runtime?.request?.symbol ?? '-'} />
            <FactRow label="Auto trade" value={state.runtime?.engine?.auto_trade ? 'on' : 'off'} />
            <FactRow label="Mode" value={modeLabel} />
          </div>

          <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <ShieldCheck size={16} />
              Execution
            </div>
            <FactRow label="Orders" value={executionLabel} />
            <FactRow label="Market data" value={marketDataLabel} />
            <FactRow label="Positions" value={String(state.runtime?.paper?.account?.positions_count ?? state.dashboard?.positions?.length ?? 0)} />
          </div>

          <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Database size={16} />
              Model
            </div>
            <FactRow label="Active" value={modelStatus.activeModelName} />
            <FactRow label="Exists" value={modelStatus.modelExists ? 'yes' : 'no'} />
            <FactRow label="Loaded" value={modelStatus.modelLoaded ? 'yes' : 'no'} />
          </div>

          <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              {unavailableModules.length === 0 ? <CheckCircle size={16} /> : <WarningCircle size={16} />}
              Health
            </div>
            <FactRow label="Modules" value={`${state.system?.modules?.length ?? 0}`} />
            <FactRow label="Blocking" value={`${blockingItems.length}`} />
            <FactRow label="Risk" value={`${state.dashboard?.risk?.level ?? '-'} ${formatNumber(state.dashboard?.risk?.percentage)}%`} />
          </div>
        </div>

        {(blockingItems.length > 0 || readinessIssues.length > 0 || unavailableModules.length > 0) && (
          <>
            <Separator />
            <div className="space-y-2">
              <div className="text-sm font-medium">Readiness</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {[...unavailableModules, ...readinessIssues].slice(0, 6).map((item) => (
                  <div key={`${item.category ?? 'module'}-${item.name}`} className="rounded-md border border-destructive/30 bg-destructive/5 p-3">
                    <div className="flex items-center justify-between gap-3 text-sm">
                      <span className="font-medium">{item.name}</span>
                      <Badge variant={item.required === false ? 'secondary' : 'destructive'}>
                        {item.required === false ? 'optional' : 'required'}
                      </Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground break-all">
                      {item.error ?? 'Unavailable'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {paperTrading && (
          <>
            <Separator />
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <FactRow label="Paper balance" value={`USDT ${formatNumber(state.runtime?.paper?.account?.balance)}`} />
              <FactRow label="Paper equity" value={`USDT ${formatNumber(state.runtime?.paper?.account?.total_equity)}`} />
              <FactRow label="Paper trades" value={String(state.runtime?.paper?.stats?.total_trades ?? 0)} />
              <FactRow label="Open orders" value={String(state.runtime?.paper?.account?.open_orders_count ?? 0)} />
            </div>
            <p className="text-xs text-muted-foreground font-mono break-all">
              Paper log: {state.runtime?.paper?.log_dir ?? 'not created yet'}
            </p>
          </>
        )}

        {liveMode && (
          <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
            Live auto mode can submit real Binance mainnet orders. Keep this mode off until paper live has been observed for enough runtime.
          </div>
        )}
      </CardContent>
    </Card>
  )
}

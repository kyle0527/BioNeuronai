import type {
  ApiPerformanceDataPoint,
  ApiPortfolioAsset,
  Trade,
} from './analytics-types'
import type {
  BacktestCatalog,
  BacktestConfig,
  BacktestInspectResponse,
  BacktestRun,
  BacktestRunResponse,
  BacktestSimulateResponse,
  NewsSentiment,
  PretradeChecklist,
  SystemStatus,
  TradeControlResponse,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

interface RestEnvelope<T = unknown> {
  success?: boolean
  message?: string
  data?: T
  timestamp?: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })

  const text = await response.text()
  const payload = text ? JSON.parse(text) : null

  if (!response.ok) {
    const message = payload?.message || payload?.detail || response.statusText
    throw new Error(`HTTP ${response.status}: ${message}`)
  }

  return payload as T
}

function unwrap<T>(payload: RestEnvelope<T> | T): T {
  if (payload && typeof payload === 'object' && 'success' in payload) {
    const envelope = payload as RestEnvelope<T>
    if (envelope.success === false) {
      throw new Error(envelope.message || 'API request failed')
    }
    return (envelope.data ?? ({} as T)) as T
  }
  return payload as T
}

function query(params: Record<string, string | number | boolean | undefined>) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      search.set(key, String(value))
    }
  })
  const text = search.toString()
  return text ? `?${text}` : ''
}

function numberValue(value: unknown, fallback = 0): number {
  const next = Number(value)
  return Number.isFinite(next) ? next : fallback
}

function stringValue(value: unknown, fallback = ''): string {
  return typeof value === 'string' && value.length > 0 ? value : fallback
}

function arrayValue<T = unknown>(value: unknown): T[] {
  return Array.isArray(value) ? value as T[] : []
}

function msToIso(value: unknown): string | undefined {
  const numeric = Number(value)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return typeof value === 'string' ? value : undefined
  }
  return new Date(numeric).toISOString()
}

function normalizeTradeAction(action: string): 'long' | 'short' {
  return action === 'sell' || action === 'short' ? 'short' : 'long'
}

function sentimentFromScore(score: number, value?: unknown): NewsSentiment['sentiment'] {
  const text = String(value ?? '').toLowerCase()
  if (text === 'positive' || text === 'negative' || text === 'neutral') {
    return text
  }
  if (score > 0.15) return 'positive'
  if (score < -0.15) return 'negative'
  return 'neutral'
}

function pretradeStatus(value: unknown): PretradeChecklist['overall_status'] {
  const text = String(value ?? '').toLowerCase()
  if (['pass', 'passed', 'approve', 'approved', 'success', 'ok'].includes(text)) return 'pass'
  if (['fail', 'failed', 'reject', 'rejected', 'error'].includes(text)) return 'fail'
  return 'warning'
}

function checklistItemStatus(value: unknown): 'pass' | 'fail' | 'warning' {
  const text = String(value ?? '').toLowerCase()
  if (['pass', 'passed', 'approve', 'approved', 'success', 'ok', 'good'].some(item => text.includes(item))) {
    return 'pass'
  }
  if (['fail', 'failed', 'reject', 'rejected', 'error', 'danger'].some(item => text.includes(item))) {
    return 'fail'
  }
  return 'warning'
}

function mapBacktestRun(raw: any): BacktestRun {
  const config = raw?.config ?? {}
  const stats = raw?.stats ?? {}
  const balance = numberValue(config.balance, numberValue(stats.initial_balance, numberValue(raw?.final_balance)))
  const runId = stringValue(raw?.run_id, stringValue(raw?.id, 'unknown'))

  return {
    id: runId,
    run_id: runId,
    symbol: stringValue(raw?.symbol, stringValue(config.symbol, 'UNKNOWN')),
    interval: stringValue(raw?.interval, stringValue(config.interval, '-')),
    start_date: stringValue(raw?.start_date, stringValue(config.start_date, '-')),
    end_date: stringValue(raw?.end_date, stringValue(config.end_date, '-')),
    balance,
    status: stringValue(raw?.status, 'unknown'),
    created_at: stringValue(raw?.started_at, stringValue(raw?.completed_at, new Date().toISOString())),
  }
}

function mapPortfolioAsset(raw: any, totalValue = 0): ApiPortfolioAsset {
  const symbol = stringValue(raw?.symbol, 'UNKNOWN')
  const quantity = numberValue(raw?.quantity)
  const avgPrice = numberValue(raw?.avg_price, numberValue(raw?.avgPrice, numberValue(raw?.entryPrice)))
  const currentPrice = numberValue(raw?.current_price, numberValue(raw?.currentPrice, avgPrice))
  const value = numberValue(raw?.value, Math.abs(quantity) * currentPrice)
  const pnl = numberValue(raw?.pnl, numberValue(raw?.unrealizedPnl))
  const pnlPercent = numberValue(raw?.pnl_percent, numberValue(raw?.pnlPercent, numberValue(raw?.unrealizedPnlPercent)))
  const allocation = numberValue(raw?.allocation, totalValue > 0 ? (value / totalValue) * 100 : 0)

  return {
    symbol,
    quantity,
    avg_price: avgPrice,
    current_price: currentPrice,
    value,
    pnl,
    pnl_percent: pnlPercent,
    allocation,
  }
}

function mapBacktestRunToTrade(raw: any): Trade {
  const stats = raw?.stats ?? {}
  const config = raw?.config ?? {}
  const pnl = numberValue(raw?.final_balance, numberValue(stats.current_balance)) - numberValue(stats.initial_balance, numberValue(config.balance))
  const runId = stringValue(raw?.run_id, stringValue(raw?.id, crypto.randomUUID()))

  return {
    id: runId,
    timestamp: stringValue(raw?.completed_at, stringValue(raw?.started_at, new Date().toISOString())),
    symbol: stringValue(raw?.symbol, stringValue(config.symbol, 'UNKNOWN')),
    type: numberValue(raw?.signal_counts?.buy) >= numberValue(raw?.signal_counts?.sell) ? 'buy' : 'sell',
    quantity: numberValue(raw?.fills_recorded, numberValue(raw?.orders_recorded)),
    price: numberValue(raw?.final_balance, numberValue(stats.current_balance)),
    pnl,
    status: raw?.status === 'failed' ? 'failed' : raw?.status === 'running' ? 'pending' : 'completed',
  }
}

function mapRunsToPerformance(runs: any[], days: number): ApiPerformanceDataPoint[] {
  const cutoff = days >= 999999 ? 0 : Date.now() - days * 86_400_000
  const sorted = runs
    .filter(run => new Date(stringValue(run?.completed_at, stringValue(run?.started_at))).getTime() >= cutoff)
    .sort((a, b) => new Date(stringValue(a?.completed_at, stringValue(a?.started_at))).getTime() - new Date(stringValue(b?.completed_at, stringValue(b?.started_at))).getTime())

  let cumulativePnl = 0
  return sorted.map(run => {
    const stats = run?.stats ?? {}
    const config = run?.config ?? {}
    const startingValue = numberValue(stats.initial_balance, numberValue(config.balance))
    const endingValue = numberValue(run?.final_balance, numberValue(stats.current_balance, startingValue))
    const dailyPnl = endingValue - startingValue
    cumulativePnl += dailyPnl

    return {
      date: stringValue(run?.completed_at, stringValue(run?.started_at, new Date().toISOString())).slice(0, 10),
      pnl: cumulativePnl,
      daily_pnl: dailyPnl,
      value: endingValue,
    }
  })
}

export const api = {
  async getStatus(): Promise<SystemStatus> {
    const payload = await request<any>('/api/v1/status')
    const modules = Object.fromEntries(
      arrayValue<any>(payload.modules).map(item => [String(item.name), Boolean(item.available)])
    )

    return {
      status: payload.all_ok ? 'healthy' : 'degraded',
      modules,
      timestamp: payload.timestamp,
    }
  },

  async getBacktestCatalog(): Promise<BacktestCatalog> {
    const data = unwrap<any>(await request('/api/v1/backtest/catalog'))
    const datasets = arrayValue<Record<string, unknown>>(data.datasets)

    return {
      root: stringValue(data.root, stringValue(data.resolved_root, stringValue(data.data_dir))),
      dataset_count: numberValue(data.dataset_count, datasets.length),
      datasets,
    }
  },

  async getBacktestRuns(limit = 10): Promise<{ runs: BacktestRun[] }> {
    const data = unwrap<any>(await request(`/api/v1/backtest/runs${query({ limit })}`))
    return { runs: arrayValue<any>(data.runs).map(mapBacktestRun) }
  },

  async getNewsSentiment(symbol: string): Promise<NewsSentiment> {
    const data = unwrap<any>(await request('/api/v1/news', {
      method: 'POST',
      body: JSON.stringify({ symbol, max_items: 10 }),
    }))
    const score = numberValue(data.sentiment_score, numberValue(data.score))
    const highlights = arrayValue<any>(data.highlights).length > 0
      ? arrayValue<string>(data.highlights)
      : arrayValue<any>(data.articles ?? data.news).slice(0, 5).map(item => stringValue(item?.title, String(item)))

    return {
      symbol,
      sentiment: sentimentFromScore(score, data.overall_sentiment ?? data.sentiment),
      score,
      highlights,
    }
  },

  async getPretradeChecklist(symbol: string, action: string): Promise<PretradeChecklist> {
    const data = unwrap<any>(await request('/api/v1/pretrade', {
      method: 'POST',
      body: JSON.stringify({ symbol, action: normalizeTradeAction(action) }),
    }))
    const assessment = data.overall_assessment ?? data.assessment ?? data
    const checkEntries = [
      ['Technical', assessment.technical_status ?? data.technical_status],
      ['Fundamental', assessment.fundamental_status ?? data.fundamental_status],
      ['Risk', assessment.risk_status ?? data.risk_status],
      ['Order', assessment.order_status ?? data.order_status],
      ['Final', assessment.final_status ?? data.final_status ?? assessment.status],
    ] as const

    return {
      overall_status: pretradeStatus(assessment.status ?? data.status ?? data.decision),
      checks: checkEntries.map(([name, value]) => ({
        name,
        status: checklistItemStatus(value),
        message: stringValue(value, 'N/A'),
      })),
    }
  },

  async inspectBacktest(config: BacktestConfig): Promise<BacktestInspectResponse> {
    const data = unwrap<any>(await request(`/api/v1/backtest/inspect${query({
      symbol: config.symbol,
      interval: config.interval,
      start_date: config.start_date,
      end_date: config.end_date,
    })}`))

    return {
      symbol: stringValue(data.symbol, config.symbol),
      interval: stringValue(data.interval, config.interval),
      data_points: numberValue(data.bars, numberValue(data.data_points)),
      start_date: stringValue(data.start_date, msToIso(data.start_open_time) ?? ''),
      end_date: stringValue(data.end_date, msToIso(data.end_open_time) ?? ''),
      warnings: arrayValue<string>(data.warnings),
    }
  },

  async simulateBacktest(config: BacktestConfig): Promise<BacktestSimulateResponse> {
    const data = unwrap<any>(await request('/api/v1/backtest/simulate', {
      method: 'POST',
      body: JSON.stringify({
        symbol: config.symbol,
        interval: config.interval,
        balance: config.balance,
        bars: config.bars,
        start_date: config.start_date,
        end_date: config.end_date,
      }),
    }))
    const summary = data.summary ?? data
    const stats = summary.stats ?? {}
    const finalBalance = numberValue(summary.final_balance, numberValue(stats.current_balance, config.balance))
    const pnl = numberValue(summary.pnl, numberValue(stats.total_realized_pnl, finalBalance - config.balance))

    return {
      trades_count: numberValue(summary.total_trades, numberValue(stats.total_trades, numberValue(summary.fills_recorded))),
      final_balance: finalBalance,
      pnl,
      pnl_percentage: config.balance ? (pnl / config.balance) * 100 : 0,
      max_drawdown: numberValue(summary.max_drawdown, numberValue(stats.max_drawdown)),
    }
  },

  async runBacktest(config: BacktestConfig): Promise<BacktestRunResponse> {
    const data = unwrap<any>(await request('/api/v1/backtest/run', {
      method: 'POST',
      body: JSON.stringify({
        symbol: config.symbol,
        interval: config.interval,
        start_date: config.start_date,
        end_date: config.end_date,
        balance: config.balance,
        warmup_bars: config.warmup_bars,
      }),
    }))

    return {
      run_id: stringValue(data.run_id, stringValue(data.summary?.run_id, 'unknown')),
      status: stringValue(data.status, stringValue(data.summary?.status, 'completed')),
      message: data.message,
    }
  },

  async sendChatMessage(payload: {
    message: string
    conversation_id?: string
    language?: string
    symbol?: string
  }): Promise<{ response: string; latency_ms?: number; confidence?: number }> {
    const data = await request<any>('/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    })

    if (data.success === false) {
      throw new Error(data.text || 'Chat request failed')
    }

    return {
      response: stringValue(data.response, stringValue(data.text)),
      latency_ms: data.latency_ms,
      confidence: data.confidence,
    }
  },

  async startTrading(): Promise<TradeControlResponse> {
    const payload = await request<RestEnvelope>('/api/v1/trade/start', {
      method: 'POST',
      body: JSON.stringify({ symbol: 'BTCUSDT', testnet: true }),
    })

    return {
      status: payload.success ? 'running' : 'failed',
      message: payload.message,
      timestamp: payload.timestamp,
    }
  },

  async stopTrading(): Promise<TradeControlResponse> {
    const payload = await request<RestEnvelope>('/api/v1/trade/stop', { method: 'POST' })
    return {
      status: payload.success ? 'stopped' : 'failed',
      message: payload.message,
      timestamp: payload.timestamp,
    }
  },

  async getAnalyticsPortfolio(): Promise<{ portfolio: ApiPortfolioAsset[] }> {
    const dashboard = await request<any>('/api/v1/dashboard')
    const rawPositions = arrayValue<any>(dashboard.positions)
    const totalValue = rawPositions.reduce((sum, item) => {
      const currentPrice = numberValue(item?.current_price, numberValue(item?.currentPrice, numberValue(item?.entryPrice)))
      return sum + numberValue(item?.value, Math.abs(numberValue(item?.quantity)) * currentPrice)
    }, 0)

    return { portfolio: rawPositions.map(item => mapPortfolioAsset(item, totalValue)) }
  },

  async getAnalyticsTrades(limit = 100): Promise<{ trades: Trade[] }> {
    const data = unwrap<any>(await request(`/api/v1/backtest/runs${query({ limit })}`))
    return { trades: arrayValue<any>(data.runs).map(mapBacktestRunToTrade) }
  },

  async getAnalyticsPerformance(days = 30): Promise<{ performance: ApiPerformanceDataPoint[] }> {
    const data = unwrap<any>(await request(`/api/v1/backtest/runs${query({ limit: 500 })}`))
    return { performance: mapRunsToPerformance(arrayValue<any>(data.runs), days) }
  },
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  latency_ms?: number
  confidence?: number
}

export interface SystemStatus {
  status: 'healthy' | 'degraded'
  modules: Record<string, boolean | string>
  timestamp?: string
}

export interface BacktestCatalogDataset {
  symbol?: string
  interval?: string
  file_count?: number
  bars?: number
  start_date?: string
  end_date?: string
  [key: string]: unknown
}

export interface BacktestCatalog {
  root: string
  dataset_count: number
  datasets: BacktestCatalogDataset[]
}

export interface BacktestRun {
  id: string
  run_id: string
  symbol: string
  interval: string
  start_date?: string
  end_date?: string
  balance: number
  status: string
  created_at: string
}

export interface NewsSentiment {
  symbol: string
  sentiment: 'positive' | 'negative' | 'neutral'
  score: number
  highlights: string[]
}

export interface PretradeChecklist {
  overall_status: 'pass' | 'fail' | 'warning'
  checks: Array<{
    name: string
    status: 'pass' | 'fail' | 'warning'
    message: string
  }>
}

export interface BacktestConfig {
  symbol: string
  interval: string
  start_date?: string
  end_date?: string
  balance: number
  warmup_bars?: number
  bars?: number
}

export interface BacktestInspectResponse {
  symbol: string
  interval: string
  data_points: number
  start_date?: string
  end_date?: string
  warnings?: string[]
}

export interface BacktestSimulateResponse {
  trades_count: number
  final_balance: number
  pnl: number
  pnl_percentage: number
  max_drawdown?: number
}

export interface BacktestRunResponse {
  run_id: string
  status: string
  message?: string
}

export interface TradeControlResponse {
  status: 'running' | 'stopped' | 'failed'
  message?: string
  timestamp?: string
}

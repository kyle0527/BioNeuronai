export interface Trade {
  id: string
  timestamp: string
  symbol: string
  type: 'buy' | 'sell'
  quantity: number
  price: number
  pnl: number
  status: 'completed' | 'pending' | 'failed'
}

export interface PortfolioAsset {
  symbol: string
  quantity: number
  avgPrice: number
  currentPrice: number
  value: number
  pnl: number
  pnlPercent: number
  allocation: number
}

export interface ApiPortfolioAsset {
  symbol: string
  quantity: number
  avg_price: number
  current_price: number
  value: number
  pnl: number
  pnl_percent: number
  allocation: number
}

export interface PerformanceDataPoint {
  date: string
  pnl: number
  dailyPnl: number
  value: number
}

export interface ApiPerformanceDataPoint {
  date: string
  pnl: number
  daily_pnl: number
  value: number
}

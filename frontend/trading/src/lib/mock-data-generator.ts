import type { PerformanceDataPoint, PortfolioAsset, Trade } from './analytics-types'

export function populateMockData(): {
  trades: Trade[]
  portfolio: PortfolioAsset[]
  performance: PerformanceDataPoint[]
} {
  const now = Date.now()
  const portfolio: PortfolioAsset[] = [
    {
      symbol: 'BTCUSDT',
      quantity: 0.12,
      avgPrice: 76000,
      currentPrice: 78000,
      value: 9360,
      pnl: 240,
      pnlPercent: 2.63,
      allocation: 68,
    },
    {
      symbol: 'ETHUSDT',
      quantity: 1.8,
      avgPrice: 2500,
      currentPrice: 2630,
      value: 4734,
      pnl: 234,
      pnlPercent: 5.2,
      allocation: 32,
    },
  ]

  const trades: Trade[] = [
    {
      id: 'demo-trade-btc-1',
      timestamp: new Date(now - 3_600_000).toISOString(),
      symbol: 'BTCUSDT',
      type: 'buy',
      quantity: 0.04,
      price: 77000,
      pnl: 80,
      status: 'completed',
    },
    {
      id: 'demo-trade-eth-1',
      timestamp: new Date(now - 7_200_000).toISOString(),
      symbol: 'ETHUSDT',
      type: 'sell',
      quantity: 0.5,
      price: 2620,
      pnl: -18,
      status: 'completed',
    },
  ]

  const performance: PerformanceDataPoint[] = Array.from({ length: 14 }, (_, index) => ({
    date: new Date(now - (13 - index) * 86_400_000).toISOString().slice(0, 10),
    pnl: index * 42 - 120,
    dailyPnl: index % 3 === 0 ? -18 : 48,
    value: 10000 + index * 42,
  }))

  return { trades, portfolio, performance }
}

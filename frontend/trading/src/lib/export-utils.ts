import type { PortfolioAsset, Trade } from './analytics-types'

function escapeCsvCell(value: string): string {
  return `"${value.replace(/"/g, '""')}"`
}

function downloadCsv(filename: string, rows: string[][]) {
  const csv = rows.map(row => row.map(cell => escapeCsvCell(cell)).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export function exportPortfolioAsCSV(portfolio: PortfolioAsset[]) {
  downloadCsv('portfolio.csv', [
    ['symbol', 'quantity', 'avgPrice', 'currentPrice', 'value', 'pnl', 'pnlPercent', 'allocation'],
    ...portfolio.map(asset => [
      asset.symbol,
      String(asset.quantity),
      String(asset.avgPrice),
      String(asset.currentPrice),
      String(asset.value),
      String(asset.pnl),
      String(asset.pnlPercent),
      String(asset.allocation),
    ]),
  ])
}

export function exportTradesAsCSV(trades: Trade[]) {
  downloadCsv('trades.csv', [
    ['id', 'timestamp', 'symbol', 'type', 'quantity', 'price', 'pnl', 'status'],
    ...trades.map(trade => [
      trade.id,
      trade.timestamp,
      trade.symbol,
      trade.type,
      String(trade.quantity),
      String(trade.price),
      String(trade.pnl),
      trade.status,
    ]),
  ])
}

export function exportFullAnalyticsReport(portfolio: PortfolioAsset[], trades: Trade[]) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  exportPortfolioAsCSV(portfolio)
  downloadCsv(`trades-${timestamp}.csv`, [
    ['id', 'timestamp', 'symbol', 'type', 'quantity', 'price', 'pnl', 'status'],
    ...trades.map(trade => [
      trade.id,
      trade.timestamp,
      trade.symbol,
      trade.type,
      String(trade.quantity),
      String(trade.price),
      String(trade.pnl),
      trade.status,
    ]),
  ])
}

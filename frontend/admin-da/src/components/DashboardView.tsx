import { useState, useEffect, useCallback } from 'react'
import { EnvironmentBadge } from './dashboard/EnvironmentBadge'
import { RiskWarning } from './dashboard/RiskWarning'
import { RiskIndicator } from './dashboard/RiskIndicator'
import { MaxDrawdownWidget } from './dashboard/MaxDrawdownWidget'
import { PretradeChecklist } from './dashboard/PretradeChecklist'
import { AuditLog } from './dashboard/AuditLog'
import { ConnectionStatus } from './dashboard/ConnectionStatus'
import { TradingControls } from './dashboard/TradingControls'
import { PositionMonitor } from './dashboard/PositionMonitor'
import { LivePriceChart } from './dashboard/LivePriceChart'
import { OrderHistoryDashboard } from './dashboard/OrderHistoryDashboard'
import { Skeleton } from './ui/skeleton'
import type { DashboardData, TradeOrder } from '@/lib/types'
import { useWebSocket } from '@/hooks/use-websocket'
import { toast } from 'sonner'

const DEMO_DATA: DashboardData = {
  environment: 'testnet',
  risk: {
    level: 'medium',
    percentage: 34.5,
    lastUpdated: new Date().toISOString()
  },
  maxDrawdown: {
    current: 12.3,
    historical: 18.7,
    period: '90 days',
    lastUpdated: new Date().toISOString()
  },
  pretradeChecklist: {
    items: [
      { id: '1', label: 'Risk limits configured', completed: true, required: true },
      { id: '2', label: 'API keys verified', completed: true, required: true },
      { id: '3', label: 'Position sizing rules set', completed: false, required: true },
      { id: '4', label: 'Stop-loss parameters defined', completed: false, required: true },
      { id: '5', label: 'Market conditions reviewed', completed: true, required: false }
    ],
    completedCount: 3,
    totalCount: 5,
    lastUpdated: new Date().toISOString()
  },
  auditLog: [
    {
      id: '1',
      timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
      eventType: 'backtest',
      description: 'Completed backtest run for BTC/USDT strategy',
      status: 'success'
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
      eventType: 'config_change',
      description: 'Updated risk parameters: max leverage 3x',
      status: 'info'
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
      eventType: 'chat_session',
      description: 'AI chat session initiated',
      status: 'success'
    }
  ],
  positions: [
    {
      id: 'pos-1',
      symbol: 'BTC/USDT',
      side: 'long',
      quantity: 0.25,
      entryPrice: 42350.50,
      currentPrice: 43120.75,
      unrealizedPnl: 192.56,
      unrealizedPnlPercent: 1.82,
      leverage: 3,
      liquidationPrice: 38500.00,
      openedAt: new Date(Date.now() - 2 * 3600000).toISOString()
    },
    {
      id: 'pos-2',
      symbol: 'ETH/USDT',
      side: 'short',
      quantity: 5.0,
      entryPrice: 2245.80,
      currentPrice: 2267.30,
      unrealizedPnl: -107.50,
      unrealizedPnlPercent: -0.96,
      leverage: 2,
      liquidationPrice: 2580.00,
      openedAt: new Date(Date.now() - 6 * 3600000).toISOString()
    }
  ]
}

export function DashboardView() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [useDemoData, setUseDemoData] = useState(false)
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT')

  const handleWSMessage = useCallback((message: unknown) => {
    const wsData = message as DashboardData
    setData(wsData)
    setUseDemoData(false)
  }, [])

  const handleWSOpen = useCallback(() => {
    toast.success('Connected', {
      description: 'Real-time data stream active'
    })
  }, [])

  const handleWSClose = useCallback(() => {
    if (!useDemoData) {
      toast.info('Disconnected', {
        description: 'Attempting to reconnect...'
      })
    }
  }, [useDemoData])

  const handleWSError = useCallback(() => {
    if (!useDemoData) {
      toast.error('Connection Error', {
        description: 'Unable to establish WebSocket connection'
      })
    }
  }, [useDemoData])

  const { status } = useWebSocket({
    url: 'ws://localhost:8000/ws/dashboard',
    reconnect: true,
    reconnectInterval: 3000,
    reconnectAttempts: 5,
    onMessage: handleWSMessage,
    onOpen: handleWSOpen,
    onClose: handleWSClose,
    onError: handleWSError
  })

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const response = await fetch('http://localhost:8000/api/v1/dashboard')
        
        if (!response.ok) {
          throw new Error(`API returned ${response.status}`)
        }
        
        const dashboardData = await response.json()
        setData(dashboardData)
        setUseDemoData(false)
      } catch (err) {
        setUseDemoData(true)
        setData(DEMO_DATA)
        toast.warning('Using Demo Data', {
          description: 'Backend unavailable. Displaying sample data.'
        })
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const handleOrderSubmit = async (order: TradeOrder) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(order)
      })

      if (!response.ok) {
        throw new Error(`Order submission failed: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (error) {
      throw error
    }
  }

  const handleClosePosition = async (positionId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/positions/${positionId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error(`Failed to close position: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (error) {
      throw error
    }
  }

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          <div className="flex items-center justify-between">
            <Skeleton className="h-10 w-64" />
            <Skeleton className="h-10 w-32" />
          </div>
          <Skeleton className="h-24 w-full" />
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <Skeleton className="h-48 w-full" />
            <Skeleton className="h-48 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    )
  }

  if (!data) return null

  const checklistComplete = data.pretradeChecklist.completedCount === data.pretradeChecklist.items.filter(i => i.required).length

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="font-bold text-3xl tracking-tight">BioNeuronAI</h1>
            <p className="text-sm text-muted-foreground">Trading Dashboard</p>
          </div>
          <div className="flex items-center gap-3">
            <ConnectionStatus status={status} />
            <EnvironmentBadge mode={data.environment} />
          </div>
        </header>

        <RiskWarning />

        <LivePriceChart symbol={selectedSymbol} onSymbolChange={setSelectedSymbol} />

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <RiskIndicator
            level={data.risk.level}
            percentage={data.risk.percentage}
            lastUpdated={data.risk.lastUpdated}
          />
          <MaxDrawdownWidget
            current={data.maxDrawdown.current}
            historical={data.maxDrawdown.historical}
            period={data.maxDrawdown.period}
            lastUpdated={data.maxDrawdown.lastUpdated}
          />
          <PretradeChecklist data={data.pretradeChecklist} />
        </div>

        <TradingControls
          disabled={!checklistComplete}
          onOrderSubmit={handleOrderSubmit}
        />

        <PositionMonitor
          positions={data.positions || []}
          onClosePosition={handleClosePosition}
        />

        <OrderHistoryDashboard />

        <AuditLog entries={data.auditLog} />
      </div>
    </div>
  )
}

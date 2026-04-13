import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { ArrowUp, ArrowDown, X, TrendUp, TrendDown } from '@phosphor-icons/react'
import { toast } from 'sonner'
import type { Position } from '@/lib/types'
import { cn } from '@/lib/utils'
import { formatDistance } from 'date-fns'

interface PositionMonitorProps {
  positions: Position[]
  onClosePosition?: (positionId: string) => Promise<void>
}

export function PositionMonitor({ positions, onClosePosition }: PositionMonitorProps) {
  const [closingPositions, setClosingPositions] = useState<Set<string>>(new Set())

  const handleClosePosition = async (position: Position) => {
    setClosingPositions(prev => new Set(prev).add(position.id))
    
    try {
      if (onClosePosition) {
        await onClosePosition(position.id)
      } else {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
      
      toast.success('Position Closed', {
        description: `${position.symbol} ${position.side.toUpperCase()} position closed`
      })
    } catch (error) {
      toast.error('Close Failed', {
        description: error instanceof Error ? error.message : 'Failed to close position'
      })
      setClosingPositions(prev => {
        const next = new Set(prev)
        next.delete(position.id)
        return next
      })
    }
  }

  const formatPrice = (price: number) => {
    return price.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 8
    })
  }

  const formatPnl = (pnl: number, percent: number) => {
    const sign = pnl >= 0 ? '+' : ''
    return {
      value: `${sign}${pnl.toFixed(2)}`,
      percent: `${sign}${percent.toFixed(2)}%`
    }
  }

  if (positions.length === 0) {
    return (
      <Card className="p-8">
        <div className="flex flex-col items-center justify-center gap-3 text-center">
          <div className="rounded-full bg-muted p-4">
            <TrendUp className="text-muted-foreground" size={32} />
          </div>
          <div>
            <h3 className="font-semibold text-lg">No Open Positions</h3>
            <p className="text-sm text-muted-foreground">
              Your open positions will appear here in real-time
            </p>
          </div>
        </div>
      </Card>
    )
  }

  const totalPnl = positions.reduce((sum, pos) => sum + pos.unrealizedPnl, 0)
  const isProfitable = totalPnl >= 0

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-border bg-card p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-lg">Open Positions</h3>
            <p className="text-sm text-muted-foreground">
              {positions.length} active {positions.length === 1 ? 'position' : 'positions'}
            </p>
          </div>
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Total Unrealized P&L</div>
            <div className={cn(
              'font-mono font-semibold text-xl',
              isProfitable ? 'text-success' : 'text-destructive'
            )}>
              {isProfitable ? '+' : ''}{totalPnl.toFixed(2)} USDT
            </div>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Symbol</TableHead>
              <TableHead>Side</TableHead>
              <TableHead className="text-right">Quantity</TableHead>
              <TableHead className="text-right">Entry Price</TableHead>
              <TableHead className="text-right">Current Price</TableHead>
              <TableHead className="text-right">Unrealized P&L</TableHead>
              <TableHead className="text-right">Leverage</TableHead>
              <TableHead>Age</TableHead>
              <TableHead className="text-center">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {positions.map((position) => {
              const pnl = formatPnl(position.unrealizedPnl, position.unrealizedPnlPercent)
              const isProfitable = position.unrealizedPnl >= 0
              const isClosing = closingPositions.has(position.id)
              
              return (
                <TableRow key={position.id}>
                  <TableCell className="font-medium font-mono">
                    {position.symbol}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={position.side === 'long' ? 'default' : 'destructive'}
                      className={cn(
                        'gap-1',
                        position.side === 'long' && 'bg-success text-success-foreground'
                      )}
                    >
                      {position.side === 'long' ? (
                        <ArrowUp weight="bold" size={12} />
                      ) : (
                        <ArrowDown weight="bold" size={12} />
                      )}
                      {position.side.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {position.quantity}
                  </TableCell>
                  <TableCell className="text-right font-mono text-muted-foreground">
                    {formatPrice(position.entryPrice)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatPrice(position.currentPrice)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className={cn(
                      'font-mono font-semibold',
                      isProfitable ? 'text-success' : 'text-destructive'
                    )}>
                      <div className="flex items-center justify-end gap-1">
                        {isProfitable ? (
                          <TrendUp size={14} weight="bold" />
                        ) : (
                          <TrendDown size={14} weight="bold" />
                        )}
                        <span>{pnl.value}</span>
                      </div>
                      <div className="text-xs">{pnl.percent}</div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    <Badge variant="outline">
                      {position.leverage}x
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDistance(new Date(position.openedAt), new Date(), { addSuffix: true })}
                  </TableCell>
                  <TableCell className="text-center">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleClosePosition(position)}
                      disabled={isClosing}
                      className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10 hover:text-destructive"
                    >
                      <X weight="bold" />
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>

      {positions.some(p => p.liquidationPrice) && (
        <div className="border-t border-border bg-muted/50 p-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="font-semibold">⚠️ Liquidation Prices:</span>
            {positions.filter(p => p.liquidationPrice).map((pos, idx) => (
              <span key={pos.id} className="font-mono">
                {idx > 0 && '•'}
                {pos.symbol}: {formatPrice(pos.liquidationPrice!)}
              </span>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

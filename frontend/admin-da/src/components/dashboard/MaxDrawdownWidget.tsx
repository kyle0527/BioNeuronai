import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Clock, TrendDown } from '@phosphor-icons/react'
import { formatDistanceToNow } from 'date-fns'

interface MaxDrawdownWidgetProps {
  current: number
  historical: number
  period: string
  lastUpdated: string
}

export function MaxDrawdownWidget({ current, historical, period, lastUpdated }: MaxDrawdownWidgetProps) {
  return (
    <Card className="border-border/50">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">Max Drawdown</CardTitle>
        <TrendDown className="text-muted-foreground" weight="duotone" />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-2">
          <div>
            <div className="text-xs text-muted-foreground">Current</div>
            <div className="font-mono text-3xl font-semibold tracking-tight text-destructive">
              {current.toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Historical ({period})</div>
            <div className="font-mono text-lg font-medium text-muted-foreground">
              {historical.toFixed(2)}%
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Clock size={14} />
          <span>Updated {formatDistanceToNow(new Date(lastUpdated), { addSuffix: true })}</span>
        </div>
      </CardContent>
    </Card>
  )
}

import type { RiskLevel } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock, ShieldWarning } from '@phosphor-icons/react'
import { formatDistanceToNow } from 'date-fns'

interface RiskIndicatorProps {
  level: RiskLevel
  percentage: number
  lastUpdated: string
}

const riskConfig = {
  low: { label: 'Low', color: 'bg-success text-success-foreground' },
  medium: { label: 'Medium', color: 'bg-warning text-warning-foreground' },
  high: { label: 'High', color: 'bg-destructive text-destructive-foreground' },
  critical: { label: 'Critical', color: 'bg-destructive text-destructive-foreground animate-pulse' },
}

export function RiskIndicator({ level, percentage, lastUpdated }: RiskIndicatorProps) {
  const config = riskConfig[level]
  
  return (
    <Card className="border-border/50">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">Risk Level</CardTitle>
        <ShieldWarning className="text-muted-foreground" weight="duotone" />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-end gap-3">
          <div className="font-mono text-4xl font-semibold tracking-tight">
            {percentage.toFixed(1)}%
          </div>
          <Badge className={`${config.color} mb-1.5`}>
            {config.label}
          </Badge>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Clock size={14} />
          <span>Updated {formatDistanceToNow(new Date(lastUpdated), { addSuffix: true })}</span>
        </div>
      </CardContent>
    </Card>
  )
}

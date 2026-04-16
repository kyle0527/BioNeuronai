import type { AuditLogEntry } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Pulse, ChartLine, ChatCircle, Gear, Lightning } from '@phosphor-icons/react'
import { formatDistanceToNow } from 'date-fns'

interface AuditLogProps {
  entries: AuditLogEntry[]
}

const eventIcons = {
  backtest: ChartLine,
  trade_start: Lightning,
  trade_stop: Lightning,
  chat_session: ChatCircle,
  config_change: Gear,
}

const statusColors = {
  success: 'bg-success text-success-foreground',
  error: 'bg-destructive text-destructive-foreground',
  pending: 'bg-warning text-warning-foreground',
  info: 'bg-accent text-accent-foreground',
}

export function AuditLog({ entries }: AuditLogProps) {
  return (
    <Card className="border-border/50">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-sm font-medium text-muted-foreground">Recent Activity</CardTitle>
        <Pulse className="text-muted-foreground" weight="duotone" />
      </CardHeader>
      <CardContent className="space-y-0">
        {entries.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            No recent activity
          </div>
        ) : (
          <div className="space-y-0">
            {entries.map((entry, index) => {
              const Icon = eventIcons[entry.eventType]
              return (
                <div
                  key={entry.id}
                  className={`flex items-start gap-3 border-border/50 py-3 ${
                    index !== entries.length - 1 ? 'border-b' : ''
                  }`}
                >
                  <div className="mt-0.5 rounded-md bg-secondary/30 p-2">
                    <Icon size={16} weight="duotone" className="text-foreground" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm leading-tight">{entry.description}</p>
                      <Badge className={`${statusColors[entry.status]} shrink-0 text-xs`}>
                        {entry.status}
                      </Badge>
                    </div>
                    <p className="font-mono text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(entry.timestamp), { addSuffix: true })}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

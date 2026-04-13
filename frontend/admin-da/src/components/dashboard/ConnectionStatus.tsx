import { Badge } from '@/components/ui/badge'
import { WifiHigh, WifiSlash, WifiX } from '@phosphor-icons/react'
import type { WebSocketStatus } from '@/hooks/use-websocket'

interface ConnectionStatusProps {
  status: WebSocketStatus
}

export function ConnectionStatus({ status }: ConnectionStatusProps) {
  const statusConfig = {
    connecting: {
      label: 'Connecting',
      variant: 'secondary' as const,
      icon: WifiSlash,
      color: 'text-warning'
    },
    connected: {
      label: 'Live',
      variant: 'default' as const,
      icon: WifiHigh,
      color: 'text-success'
    },
    disconnected: {
      label: 'Disconnected',
      variant: 'secondary' as const,
      icon: WifiSlash,
      color: 'text-muted-foreground'
    },
    error: {
      label: 'Error',
      variant: 'destructive' as const,
      icon: WifiX,
      color: 'text-destructive'
    }
  }

  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <Badge variant={config.variant} className="gap-1.5 px-2.5 py-1">
      <Icon className={config.color} size={14} weight="bold" />
      <span className="text-xs font-medium">{config.label}</span>
    </Badge>
  )
}

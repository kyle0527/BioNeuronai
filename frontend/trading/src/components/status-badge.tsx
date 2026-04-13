import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

type StatusVariant = 'success' | 'warning' | 'error' | 'info' | 'default'

interface StatusBadgeProps {
  status: StatusVariant
  label: string
  withDot?: boolean
  className?: string
}

const statusConfig = {
  success: {
    className: 'bg-green-500/10 text-green-500 border-green-500/20',
    dotClassName: 'bg-green-500',
  },
  warning: {
    className: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
    dotClassName: 'bg-amber-500',
  },
  error: {
    className: 'bg-red-500/10 text-red-500 border-red-500/20',
    dotClassName: 'bg-red-500',
  },
  info: {
    className: 'bg-primary/10 text-primary border-primary/20',
    dotClassName: 'bg-primary',
  },
  default: {
    className: 'bg-muted text-muted-foreground border-border',
    dotClassName: 'bg-muted-foreground',
  },
}

export function StatusBadge({ status, label, withDot = true, className }: StatusBadgeProps) {
  const config = statusConfig[status]

  return (
    <Badge variant="outline" className={cn(config.className, 'font-mono text-xs', className)}>
      {withDot && (
        <span className={cn('mr-1.5 h-1.5 w-1.5 rounded-full', config.dotClassName)} />
      )}
      {label}
    </Badge>
  )
}

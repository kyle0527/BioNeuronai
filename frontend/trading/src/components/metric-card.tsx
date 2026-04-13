import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

interface MetricCardProps {
  title: string
  value: string | number
  description?: string
  trend?: {
    value: number
    label: string
  }
  icon?: React.ReactNode
  isLoading?: boolean
  className?: string
}

export function MetricCard({
  title,
  value,
  description,
  trend,
  icon,
  isLoading = false,
  className,
}: MetricCardProps) {
  if (isLoading) {
    return (
      <Card className={cn('transition-all', className)}>
        <CardHeader>
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-32 mt-2" />
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className={cn('transition-all hover:shadow-md hover:-translate-y-0.5', className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="space-y-1">
          <CardTitle className="text-sm font-semibold">{title}</CardTitle>
          {description && (
            <CardDescription className="text-xs">{description}</CardDescription>
          )}
        </div>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold font-mono">{value}</div>
        {trend && (
          <p
            className={cn(
              'text-xs font-medium mt-1',
              trend.value >= 0 ? 'text-green-500' : 'text-red-500'
            )}
          >
            {trend.value >= 0 ? '+' : ''}
            {trend.value}% {trend.label}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

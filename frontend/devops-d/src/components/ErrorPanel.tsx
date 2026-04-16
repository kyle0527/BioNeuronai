import { WarningCircle } from '@phosphor-icons/react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { JSONViewer } from './JSONViewer'

interface ErrorPanelProps {
  title?: string
  message: string
  details?: unknown
}

export function ErrorPanel({ title = 'Error', message, details }: ErrorPanelProps) {
  return (
    <div className="space-y-3">
      <Alert variant="destructive">
        <WarningCircle size={18} weight="fill" />
        <AlertTitle>{title}</AlertTitle>
        <AlertDescription>{message}</AlertDescription>
      </Alert>
      {details && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground">Error Details:</p>
          <JSONViewer data={details} maxHeight="200px" />
        </div>
      )}
    </div>
  )
}

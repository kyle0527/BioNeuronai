import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Warning } from '@phosphor-icons/react'

export function RiskWarning() {
  return (
    <Alert className="border-destructive/50 bg-destructive/10">
      <Warning size={20} weight="fill" className="text-destructive" />
      <AlertTitle className="text-destructive">High-Risk Trading Warning</AlertTitle>
      <AlertDescription className="text-sm text-foreground/90">
        Futures trading carries substantial risk of loss. Only trade with capital you can afford to lose. 
        Past performance does not guarantee future results. Ensure you understand the risks before proceeding.
      </AlertDescription>
    </Alert>
  )
}

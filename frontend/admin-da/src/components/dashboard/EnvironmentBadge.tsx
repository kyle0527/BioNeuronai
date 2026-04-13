import type { EnvironmentMode } from '@/lib/types'
import { Badge } from '@/components/ui/badge'
import { TestTube, Warning } from '@phosphor-icons/react'

interface EnvironmentBadgeProps {
  mode: EnvironmentMode
}

export function EnvironmentBadge({ mode }: EnvironmentBadgeProps) {
  const isTestnet = mode === 'testnet'
  
  return (
    <Badge 
      className={`${
        isTestnet 
          ? 'bg-success text-success-foreground' 
          : 'bg-destructive text-destructive-foreground'
      } flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold`}
    >
      {isTestnet ? (
        <TestTube size={16} weight="fill" />
      ) : (
        <Warning size={16} weight="fill" />
      )}
      {isTestnet ? 'TESTNET MODE' : 'MAINNET MODE'}
    </Badge>
  )
}

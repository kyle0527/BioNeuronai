import { useState } from 'react'
import { Copy, Check } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

interface JSONViewerProps {
  data: unknown
  className?: string
  maxHeight?: string
}

export function JSONViewer({ data, className, maxHeight = '400px' }: JSONViewerProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    const jsonString = JSON.stringify(data, null, 2)
    navigator.clipboard.writeText(jsonString)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const jsonString = JSON.stringify(data, null, 2)

  return (
    <div className={cn('relative border rounded-md bg-muted/30', className)}>
      <div className="absolute top-2 right-2 z-10">
        <Button
          size="sm"
          variant="outline"
          onClick={handleCopy}
          className="h-7 gap-1.5 bg-background"
        >
          {copied ? (
            <>
              <Check size={14} weight="bold" />
              Copied
            </>
          ) : (
            <>
              <Copy size={14} />
              Copy
            </>
          )}
        </Button>
      </div>
      <ScrollArea style={{ maxHeight }} className="w-full">
        <pre className="json-viewer p-4 pr-24 overflow-x-auto">
          <code>{jsonString}</code>
        </pre>
      </ScrollArea>
    </div>
  )
}

import type { PretradeChecklistData } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Progress } from '@/components/ui/progress'
import { CheckSquare, Clock, Square } from '@phosphor-icons/react'
import { formatDistanceToNow } from 'date-fns'

interface PretradeChecklistProps {
  data: PretradeChecklistData
}

export function PretradeChecklist({ data }: PretradeChecklistProps) {
  const completionPercentage = (data.completedCount / data.totalCount) * 100
  
  return (
    <Card className="border-border/50">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">Pre-trade Checklist</CardTitle>
        <CheckSquare className="text-muted-foreground" weight="duotone" />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-mono text-2xl font-semibold">
              {data.completedCount}/{data.totalCount}
            </span>
            <span className="text-sm text-muted-foreground">
              {completionPercentage.toFixed(0)}% Complete
            </span>
          </div>
          <Progress value={completionPercentage} className="h-2" />
        </div>
        
        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="items" className="border-0">
            <AccordionTrigger className="py-2 text-xs text-muted-foreground hover:text-foreground hover:no-underline">
              View Details
            </AccordionTrigger>
            <AccordionContent className="space-y-2 pb-0 pt-2">
              {data.items.map((item) => (
                <div 
                  key={item.id} 
                  className="flex items-center gap-2 rounded-md bg-secondary/30 px-3 py-2"
                >
                  {item.completed ? (
                    <CheckSquare size={16} weight="fill" className="text-success" />
                  ) : (
                    <Square size={16} className="text-muted-foreground" />
                  )}
                  <span className="flex-1 text-sm">
                    {item.label}
                    {item.required && <span className="ml-1 text-destructive">*</span>}
                  </span>
                </div>
              ))}
            </AccordionContent>
          </AccordionItem>
        </Accordion>
        
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Clock size={14} />
          <span>Updated {formatDistanceToNow(new Date(data.lastUpdated), { addSuffix: true })}</span>
        </div>
      </CardContent>
    </Card>
  )
}

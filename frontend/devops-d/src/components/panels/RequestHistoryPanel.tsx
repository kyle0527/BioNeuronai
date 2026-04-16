import { useState } from 'react'
import { Download, Trash, FunnelSimple, CheckCircle, WarningCircle, Clock } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { JSONViewer } from '@/components/JSONViewer'
import { useRequestLoggerContext } from '@/lib/RequestLoggerContext'
import { toast } from 'sonner'
import type { RequestLog } from '@/hooks/use-request-logger'

export function RequestHistoryPanel() {
  const { logs, clearLogs, downloadLogs } = useRequestLoggerContext()
  const [selectedLog, setSelectedLog] = useState<RequestLog | null>(null)
  const [methodFilter, setMethodFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const filteredLogs = logs.filter(log => {
    if (methodFilter !== 'all' && log.method !== methodFilter) return false
    if (statusFilter === 'success' && (log.error || !log.responseStatus || log.responseStatus >= 400)) return false
    if (statusFilter === 'error' && !log.error && log.responseStatus && log.responseStatus < 400) return false
    return true
  })

  const handleClearHistory = () => {
    clearLogs()
    setSelectedLog(null)
    toast.success('Request history cleared')
  }

  const handleExport = (format: 'json' | 'csv') => {
    downloadLogs(format)
    toast.success(`Exported ${logs.length} requests as ${format.toUpperCase()}`)
  }

  const getStatusColor = (log: RequestLog) => {
    if (log.error) return 'text-destructive'
    if (!log.responseStatus) return 'text-muted-foreground'
    if (log.responseStatus >= 200 && log.responseStatus < 300) return 'text-success'
    if (log.responseStatus >= 400) return 'text-destructive'
    return 'text-muted-foreground'
  }

  const getStatusIcon = (log: RequestLog) => {
    if (log.error) return <WarningCircle size={16} weight="fill" className="text-destructive" />
    if (log.responseStatus && log.responseStatus >= 200 && log.responseStatus < 300) {
      return <CheckCircle size={16} weight="fill" className="text-success" />
    }
    if (log.responseStatus && log.responseStatus >= 400) {
      return <WarningCircle size={16} weight="fill" className="text-destructive" />
    }
    return <Clock size={16} className="text-muted-foreground" />
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-[calc(100vh-12rem)]">
      <Card className="flex flex-col">
        <CardHeader className="flex-none">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-mono font-medium">Request History</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="font-mono text-xs">
                {filteredLogs.length} {filteredLogs.length === 1 ? 'request' : 'requests'}
              </Badge>
            </div>
          </div>
          
          <div className="flex items-center gap-2 pt-2">
            <Select value={methodFilter} onValueChange={setMethodFilter}>
              <SelectTrigger className="w-[100px] h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="GET">GET</SelectItem>
                <SelectItem value="POST">POST</SelectItem>
                <SelectItem value="PUT">PUT</SelectItem>
                <SelectItem value="DELETE">DELETE</SelectItem>
              </SelectContent>
            </Select>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[100px] h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="success">Success</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex-1" />

            <Button size="sm" variant="ghost" onClick={() => handleExport('json')}>
              <Download size={16} className="mr-1" />
              JSON
            </Button>
            <Button size="sm" variant="ghost" onClick={() => handleExport('csv')}>
              <Download size={16} className="mr-1" />
              CSV
            </Button>
            <Button size="sm" variant="ghost" onClick={handleClearHistory} disabled={logs.length === 0}>
              <Trash size={16} />
            </Button>
          </div>
        </CardHeader>

        <Separator />

        <CardContent className="flex-1 p-0 overflow-hidden">
          <ScrollArea className="h-full">
            {filteredLogs.length === 0 ? (
              <div className="p-6 text-center text-sm text-muted-foreground">
                <FunnelSimple size={32} className="mx-auto mb-2 opacity-50" />
                {logs.length === 0 ? 'No requests logged yet' : 'No requests match the current filters'}
              </div>
            ) : (
              <div className="divide-y divide-border">
                {filteredLogs.map((log) => (
                  <button
                    key={log.id}
                    onClick={() => setSelectedLog(log)}
                    className={`w-full text-left px-4 py-3 hover:bg-muted/50 transition-colors ${
                      selectedLog?.id === log.id ? 'bg-muted' : ''
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <div className="flex-none mt-0.5">{getStatusIcon(log)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline" className="font-mono text-xs px-1.5 py-0">
                            {log.method}
                          </Badge>
                          {log.responseStatus && (
                            <span className={`font-mono text-xs font-medium ${getStatusColor(log)}`}>
                              {log.responseStatus}
                            </span>
                          )}
                          {log.duration !== undefined && (
                            <span className="text-xs text-muted-foreground font-mono ml-auto">
                              {log.duration}ms
                            </span>
                          )}
                        </div>
                        <p className="text-sm font-mono truncate">{log.endpoint}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {new Date(log.timestamp).toLocaleString()}
                        </p>
                        {log.error && (
                          <p className="text-xs text-destructive mt-1 truncate">{log.error}</p>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      <Card className="flex flex-col">
        <CardHeader className="flex-none">
          <CardTitle className="text-sm font-mono font-medium">
            {selectedLog ? 'Request Details' : 'Select a Request'}
          </CardTitle>
        </CardHeader>

        <Separator />

        <CardContent className="flex-1 p-0 overflow-hidden">
          {selectedLog ? (
            <ScrollArea className="h-full">
              <div className="p-4 space-y-4">
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-2">Request</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground min-w-[80px]">Method:</span>
                      <Badge variant="outline" className="font-mono">{selectedLog.method}</Badge>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-muted-foreground min-w-[80px] flex-none">Endpoint:</span>
                      <code className="text-xs font-mono bg-muted px-2 py-1 rounded flex-1 break-all">
                        {selectedLog.endpoint}
                      </code>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground min-w-[80px]">Time:</span>
                      <span className="font-mono text-xs">{new Date(selectedLog.timestamp).toLocaleString()}</span>
                    </div>
                    {selectedLog.duration !== undefined && (
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground min-w-[80px]">Duration:</span>
                        <span className="font-mono text-xs">{selectedLog.duration}ms</span>
                      </div>
                    )}
                  </div>
                </div>

                {selectedLog.requestHeaders && Object.keys(selectedLog.requestHeaders).length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-2">Request Headers</p>
                      <JSONViewer data={selectedLog.requestHeaders} maxHeight="150px" />
                    </div>
                  </>
                )}

                {selectedLog.requestBody && (
                  <>
                    <Separator />
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-2">Request Body</p>
                      <JSONViewer data={selectedLog.requestBody} maxHeight="200px" />
                    </div>
                  </>
                )}

                <Separator />

                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-2">Response</p>
                  <div className="space-y-2 text-sm">
                    {selectedLog.responseStatus && (
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground min-w-[80px]">Status:</span>
                        <Badge variant={selectedLog.responseStatus >= 200 && selectedLog.responseStatus < 300 ? 'default' : 'destructive'}>
                          {selectedLog.responseStatus}
                        </Badge>
                      </div>
                    )}
                    {selectedLog.error && (
                      <div className="flex items-start gap-2">
                        <span className="text-muted-foreground min-w-[80px] flex-none">Error:</span>
                        <span className="text-destructive text-xs">{selectedLog.error}</span>
                      </div>
                    )}
                  </div>
                </div>

                {selectedLog.responseHeaders && Object.keys(selectedLog.responseHeaders).length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-2">Response Headers</p>
                      <JSONViewer data={selectedLog.responseHeaders} maxHeight="150px" />
                    </div>
                  </>
                )}

                {selectedLog.responseData && (
                  <>
                    <Separator />
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-2">Response Body</p>
                      <JSONViewer data={selectedLog.responseData} maxHeight="300px" />
                    </div>
                  </>
                )}
              </div>
            </ScrollArea>
          ) : (
            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
              Select a request from the list to view details
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

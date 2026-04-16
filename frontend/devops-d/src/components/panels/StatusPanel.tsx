import { useState } from 'react'
import { ArrowClockwise, CheckCircle, WarningCircle } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { JSONViewer } from '@/components/JSONViewer'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { endpoints, type ApiError, type RestApiResponse, type StatusResponse } from '@/lib/api'

export function StatusPanel() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [data, setData] = useState<StatusResponse | null>(null)
  const [lastUpdate, setLastUpdate] = useState<string | null>(null)

  const fetchStatus = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await endpoints.status()
      const body = response.data as RestApiResponse<StatusResponse>
      setData(body as unknown as StatusResponse)
      setLastUpdate(new Date().toLocaleTimeString())
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-sm font-mono font-medium">System Status</CardTitle>
        <Button size="sm" variant="ghost" onClick={fetchStatus} disabled={loading}>
          {loading ? <LoadingSpinner size="sm" /> : <ArrowClockwise size={16} />}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <ErrorPanel message={error.message} details={error.details} />}

        {data && !error && (
          <>
            <div className="flex items-center gap-3">
              {data.all_ok ? (
                <>
                  <CheckCircle size={20} weight="fill" className="text-success" />
                  <Badge className="bg-success text-success-foreground">All Systems OK</Badge>
                </>
              ) : (
                <>
                  <WarningCircle size={20} weight="fill" className="text-destructive" />
                  <Badge variant="destructive">Degraded</Badge>
                </>
              )}
              {lastUpdate && (
                <span className="text-xs text-muted-foreground ml-auto">
                  Updated: {lastUpdate}
                </span>
              )}
            </div>

            {data.modules && data.modules.length > 0 && (
              <div className="space-y-1">
                {data.modules.map((mod) => (
                  <div key={mod.name} className="flex items-center gap-2 text-xs">
                    {mod.available ? (
                      <CheckCircle size={14} className="text-success shrink-0" />
                    ) : (
                      <WarningCircle size={14} className="text-destructive shrink-0" />
                    )}
                    <span className="font-mono">{mod.name}</span>
                    {!mod.available && mod.error && (
                      <span className="text-muted-foreground truncate" title={mod.error}>
                        — {mod.error}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}

            <Separator />

            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">Raw Response:</p>
              <JSONViewer data={data} maxHeight="300px" />
            </div>
          </>
        )}

        {!data && !error && !loading && (
          <p className="text-sm text-muted-foreground">Click refresh to fetch status</p>
        )}
      </CardContent>
    </Card>
  )
}

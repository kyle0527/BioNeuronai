import { useState } from 'react'
import { ShieldCheck, ArrowClockwise, FloppyDisk } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { JSONViewer } from '@/components/JSONViewer'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { endpoints, type ApiError } from '@/lib/api'

const RISK_LEVELS = ['CONSERVATIVE', 'MODERATE', 'AGGRESSIVE', 'HIGH_RISK'] as const
type RiskLevel = typeof RISK_LEVELS[number]

const LEVEL_COLOR: Record<RiskLevel, string> = {
  CONSERVATIVE: 'bg-blue-100 text-blue-800 border-blue-200',
  MODERATE:     'bg-green-100 text-green-800 border-green-200',
  AGGRESSIVE:   'bg-yellow-100 text-yellow-800 border-yellow-200',
  HIGH_RISK:    'bg-red-100 text-red-800 border-red-200',
}

const LEVEL_DESC: Record<RiskLevel, string> = {
  CONSERVATIVE: '保守：每筆最多損失 1%，槓桿 ≤ 2x',
  MODERATE:     '中等（預設）：每筆最多損失 2%，槓桿 ≤ 3x',
  AGGRESSIVE:   '積極：每筆最多損失 3%，槓桿 ≤ 5x',
  HIGH_RISK:    '高風險：每筆最多損失 5%，槓桿 ≤ 10x',
}

export function RiskConfigPanel() {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [rawConfig, setRawConfig] = useState<unknown>(null)
  const [currentLevel, setCurrentLevel] = useState<RiskLevel | null>(null)
  const [selectedLevel, setSelectedLevel] = useState<RiskLevel | null>(null)

  const fetchConfig = async () => {
    setLoading(true)
    setError(null)
    setSuccessMsg(null)
    try {
      const res = await endpoints.riskConfigGet()
      const body = res.data as { success: boolean; data?: Record<string, unknown> }
      if (body.success && body.data) {
        setRawConfig(body.data)
        const level = body.data['risk_level'] as RiskLevel | undefined
        if (level && RISK_LEVELS.includes(level)) {
          setCurrentLevel(level)
          setSelectedLevel(level)
        }
      } else {
        setError({ message: '讀取失敗' })
      }
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(false)
    }
  }

  const saveLevel = async () => {
    if (!selectedLevel) return
    setSaving(true)
    setError(null)
    setSuccessMsg(null)
    try {
      const res = await endpoints.riskConfigUpdate({ risk_level: selectedLevel })
      const body = res.data as { success: boolean; message?: string; data?: unknown }
      if (body.success) {
        setCurrentLevel(selectedLevel)
        setRawConfig(body.data ?? rawConfig)
        setSuccessMsg(body.message ?? '已更新')
      } else {
        setError({ message: body.message ?? '更新失敗' })
      }
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setSaving(false)
    }
  }

  const isDirty = selectedLevel !== currentLevel

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-sm font-mono font-medium flex items-center gap-2">
          <ShieldCheck size={16} weight="bold" />
          Risk Config
        </CardTitle>
        <Button size="sm" variant="ghost" onClick={fetchConfig} disabled={loading || saving}>
          {loading ? <LoadingSpinner size="sm" /> : <ArrowClockwise size={16} />}
        </Button>
      </CardHeader>

      <CardContent className="space-y-4">
        {error && <ErrorPanel message={error.message} details={error.details} />}

        {successMsg && (
          <div className="rounded-md bg-green-50 border border-green-200 px-3 py-2 text-xs text-green-800 font-mono">
            ✓ {successMsg}
          </div>
        )}

        {rawConfig === null && !error && !loading && (
          <p className="text-sm text-muted-foreground">點擊右上角重新整理以讀取目前設定</p>
        )}

        {rawConfig !== null && (
          <>
            <div className="space-y-2">
              <Label className="text-xs font-mono text-muted-foreground">目前等級</Label>
              {currentLevel && (
                <Badge className={`font-mono text-xs border ${LEVEL_COLOR[currentLevel]}`}>
                  {currentLevel}
                </Badge>
              )}
            </div>

            <Separator />

            <div className="space-y-2">
              <Label className="text-xs font-mono text-muted-foreground">選擇新等級</Label>
              <div className="grid grid-cols-2 gap-2">
                {RISK_LEVELS.map((lvl) => (
                  <button
                    key={lvl}
                    onClick={() => setSelectedLevel(lvl)}
                    className={`rounded-md border px-3 py-2 text-left transition-all ${
                      selectedLevel === lvl
                        ? `${LEVEL_COLOR[lvl]} ring-2 ring-offset-1 ring-current`
                        : 'border-border bg-muted/30 hover:bg-muted/60'
                    }`}
                  >
                    <div className="text-xs font-mono font-semibold">{lvl}</div>
                    <div className="text-[10px] text-muted-foreground mt-0.5 leading-tight">
                      {LEVEL_DESC[lvl]}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {isDirty && (
              <Button
                size="sm"
                className="w-full gap-2"
                onClick={saveLevel}
                disabled={saving}
              >
                {saving ? <LoadingSpinner size="sm" /> : <FloppyDisk size={15} weight="bold" />}
                {saving ? '儲存中...' : `套用 ${selectedLevel}`}
              </Button>
            )}

            <Separator />

            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">完整設定：</p>
              <JSONViewer data={rawConfig} maxHeight="200px" />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

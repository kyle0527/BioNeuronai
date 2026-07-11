import { useState } from 'react'
import { Play, ArrowClockwise, FloppyDisk } from '@phosphor-icons/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { JSONViewer } from '@/components/JSONViewer'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { endpoints, type ApiError, type TrainingStartBody } from '@/lib/api'

type TrainingMode = TrainingStartBody['execution_mode']

function nullableText(value: string) {
  const trimmed = value.trim()
  return trimmed || null
}

function numberOrNull(value: string) {
  const trimmed = value.trim()
  if (!trimmed) return null
  const parsed = Number(trimmed)
  return Number.isFinite(parsed) ? parsed : null
}

function getJobId(payload: unknown): string | null {
  const data = (payload as { data?: unknown } | null)?.data
  const jobId = (data as { job_id?: unknown } | null)?.job_id
  return typeof jobId === 'string' ? jobId : null
}

export function TrainingPanel() {
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [data, setData] = useState<unknown>(null)
  const [mode, setMode] = useState<TrainingMode>('external')
  const [jobName, setJobName] = useState('cloud-training')
  const [cloudJobId, setCloudJobId] = useState('')
  const [jobId, setJobId] = useState('')
  const [signalData, setSignalData] = useState('data/processed/signal_train.pt')
  const [signalValData, setSignalValData] = useState('data/processed/signal_val.pt')
  const [cloudOutputUri, setCloudOutputUri] = useState('')
  const [outputDir, setOutputDir] = useState('output/api_training')
  const [epochs, setEpochs] = useState('1')
  const [batch, setBatch] = useState('2')
  const [gradAccum, setGradAccum] = useState('1')
  const [saveSteps, setSaveSteps] = useState('100')
  const [maxSignalSamples, setMaxSignalSamples] = useState('')
  const [sigOnly, setSigOnly] = useState(true)
  const [lmOnly, setLmOnly] = useState(false)
  const [noSave, setNoSave] = useState(false)
  const [modelName, setModelName] = useState('unified_v2_100m')
  const [modelPath, setModelPath] = useState('')
  const [validatePath, setValidatePath] = useState(true)
  const [reloadEngine, setReloadEngine] = useState(false)

  const runAction = async (action: string, callback: () => Promise<unknown>) => {
    setLoading(action)
    setError(null)
    try {
      const result = await callback()
      setData(result)
      const nextJobId = getJobId(result)
      if (nextJobId) setJobId(nextJobId)
    } catch (err) {
      setError(err as ApiError)
    } finally {
      setLoading(null)
    }
  }

  const handleStart = () => runAction('start', async () => {
    const response = await endpoints.trainingStart({
      execution_mode: mode,
      job_name: jobName,
      cloud_job_id: nullableText(cloudJobId),
      signal_data: nullableText(signalData),
      signal_val_data: nullableText(signalValData),
      base_model: null,
      resume: null,
      output_dir: outputDir,
      cloud_output_uri: nullableText(cloudOutputUri),
      epochs: Number(epochs) || 1,
      batch: Number(batch) || 2,
      grad_accum: Number(gradAccum) || 1,
      save_steps: Number(saveSteps) || 100,
      max_signal_samples: numberOrNull(maxSignalSamples),
      lm_only: lmOnly,
      sig_only: sigOnly,
      no_save: noSave,
      notes: null,
    })
    return response.data
  })

  const handleStatus = () => runAction('status', async () => {
    const response = jobId.trim()
      ? await endpoints.trainingStatus(jobId.trim())
      : await endpoints.trainingList()
    return response.data
  })

  const handleModelStatus = () => runAction('model-status', async () => {
    const response = await endpoints.modelStatus()
    return response.data
  })

  const handlePromote = () => runAction('promote', async () => {
    const response = await endpoints.modelPromote({
      model_name: modelName,
      model_path: modelPath,
      validate_path: validatePath,
      reload_running_engine: reloadEngine,
      warmup_model: false,
      notes: null,
    })
    return response.data
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-mono font-medium flex items-center justify-between">
          <span>Training / Model</span>
          <Badge variant="secondary" className="font-mono text-xs">{mode}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label htmlFor="training-mode" className="text-xs">Mode</Label>
            <Select value={mode} onValueChange={(value) => setMode(value as TrainingMode)}>
              <SelectTrigger id="training-mode">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="external">External</SelectItem>
                <SelectItem value="local_process">Local process</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label htmlFor="training-job-name" className="text-xs">Job</Label>
            <Input id="training-job-name" value={jobName} onChange={(event) => setJobName(event.target.value)} className="font-mono text-sm" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label htmlFor="training-cloud-job" className="text-xs">Cloud Job ID</Label>
            <Input id="training-cloud-job" value={cloudJobId} onChange={(event) => setCloudJobId(event.target.value)} className="font-mono text-sm" />
          </div>
          <div className="space-y-1">
            <Label htmlFor="training-query-job" className="text-xs">Tracked Job ID</Label>
            <Input id="training-query-job" value={jobId} onChange={(event) => setJobId(event.target.value)} className="font-mono text-sm" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label htmlFor="training-signal-data" className="text-xs">Signal Train</Label>
            <Input id="training-signal-data" value={signalData} onChange={(event) => setSignalData(event.target.value)} className="font-mono text-sm" />
          </div>
          <div className="space-y-1">
            <Label htmlFor="training-signal-val" className="text-xs">Signal Val</Label>
            <Input id="training-signal-val" value={signalValData} onChange={(event) => setSignalValData(event.target.value)} className="font-mono text-sm" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label htmlFor="training-output-dir" className="text-xs">Output Dir</Label>
            <Input id="training-output-dir" value={outputDir} onChange={(event) => setOutputDir(event.target.value)} className="font-mono text-sm" />
          </div>
          <div className="space-y-1">
            <Label htmlFor="training-cloud-output" className="text-xs">Cloud Output</Label>
            <Input id="training-cloud-output" value={cloudOutputUri} onChange={(event) => setCloudOutputUri(event.target.value)} className="font-mono text-sm" />
          </div>
        </div>

        <div className="grid grid-cols-4 gap-2">
          <div className="space-y-1">
            <Label htmlFor="training-epochs" className="text-xs">Epochs</Label>
            <Input id="training-epochs" type="number" min="1" value={epochs} onChange={(event) => setEpochs(event.target.value)} className="font-mono text-sm" />
          </div>
          <div className="space-y-1">
            <Label htmlFor="training-batch" className="text-xs">Batch</Label>
            <Input id="training-batch" type="number" min="1" value={batch} onChange={(event) => setBatch(event.target.value)} className="font-mono text-sm" />
          </div>
          <div className="space-y-1">
            <Label htmlFor="training-grad-accum" className="text-xs">Accum</Label>
            <Input id="training-grad-accum" type="number" min="1" value={gradAccum} onChange={(event) => setGradAccum(event.target.value)} className="font-mono text-sm" />
          </div>
          <div className="space-y-1">
            <Label htmlFor="training-save-steps" className="text-xs">Save</Label>
            <Input id="training-save-steps" type="number" min="1" value={saveSteps} onChange={(event) => setSaveSteps(event.target.value)} className="font-mono text-sm" />
          </div>
        </div>

        <div className="grid grid-cols-4 gap-2">
          <div className="space-y-1">
            <Label htmlFor="training-max-samples" className="text-xs">Max Samples</Label>
            <Input id="training-max-samples" type="number" min="1" value={maxSignalSamples} onChange={(event) => setMaxSignalSamples(event.target.value)} className="font-mono text-sm" />
          </div>
          <div className="flex items-end gap-2 h-14">
            <Switch id="training-sig-only" checked={sigOnly} onCheckedChange={setSigOnly} />
            <Label htmlFor="training-sig-only" className="text-xs">Sig</Label>
          </div>
          <div className="flex items-end gap-2 h-14">
            <Switch id="training-lm-only" checked={lmOnly} onCheckedChange={setLmOnly} />
            <Label htmlFor="training-lm-only" className="text-xs">LM</Label>
          </div>
          <div className="flex items-end gap-2 h-14">
            <Switch id="training-no-save" checked={noSave} onCheckedChange={setNoSave} />
            <Label htmlFor="training-no-save" className="text-xs">No Save</Label>
          </div>
        </div>

        <div className="flex gap-2">
          <Button onClick={handleStart} disabled={loading !== null || !jobName} className="flex-1">
            {loading === 'start' ? <LoadingSpinner size="sm" className="mr-2" /> : <Play size={16} className="mr-2" />}
            Start / Register
          </Button>
          <Button onClick={handleStatus} disabled={loading !== null} variant="outline" className="flex-1">
            {loading === 'status' ? <LoadingSpinner size="sm" className="mr-2" /> : <ArrowClockwise size={16} className="mr-2" />}
            Job Status
          </Button>
        </div>

        <Separator />

        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <Label htmlFor="promote-model-name" className="text-xs">Model</Label>
            <Input id="promote-model-name" value={modelName} onChange={(event) => setModelName(event.target.value)} className="font-mono text-sm" />
          </div>
          <div className="space-y-1">
            <Label htmlFor="promote-model-path" className="text-xs">Model Path</Label>
            <Input id="promote-model-path" value={modelPath} onChange={(event) => setModelPath(event.target.value)} className="font-mono text-sm" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="flex items-center gap-2 h-9">
            <Switch id="promote-validate" checked={validatePath} onCheckedChange={setValidatePath} />
            <Label htmlFor="promote-validate" className="text-xs">Validate</Label>
          </div>
          <div className="flex items-center gap-2 h-9">
            <Switch id="promote-reload" checked={reloadEngine} onCheckedChange={setReloadEngine} />
            <Label htmlFor="promote-reload" className="text-xs">Reload Engine</Label>
          </div>
        </div>

        <div className="flex gap-2">
          <Button onClick={handlePromote} disabled={loading !== null || !modelPath || !modelName} className="flex-1">
            {loading === 'promote' ? <LoadingSpinner size="sm" className="mr-2" /> : <FloppyDisk size={16} className="mr-2" />}
            Promote
          </Button>
          <Button onClick={handleModelStatus} disabled={loading !== null} variant="outline" className="flex-1">
            {loading === 'model-status' ? <LoadingSpinner size="sm" className="mr-2" /> : <ArrowClockwise size={16} className="mr-2" />}
            Model Status
          </Button>
        </div>

        {error && <ErrorPanel message={error.message} details={error.details} />}

        {data !== null && !error && (
          <>
            <Separator />
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">Response:</p>
              <JSONViewer data={data} maxHeight="320px" />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

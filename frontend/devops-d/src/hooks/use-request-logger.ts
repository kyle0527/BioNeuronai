import { useState, useCallback } from 'react'

export interface RequestLog {
  id: string
  timestamp: number
  method: string
  endpoint: string
  requestBody?: unknown
  requestHeaders?: Record<string, string>
  responseStatus?: number
  responseData?: unknown
  responseHeaders?: Record<string, string>
  error?: string
  duration?: number
}

const STORAGE_KEY = 'bioneuronai-request-logs'
const MAX_LOGS = 500

function loadLogsFromStorage(): RequestLog[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as RequestLog[]) : []
  } catch {
    return []
  }
}

function saveLogsToStorage(logs: RequestLog[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(logs))
  } catch {
    // storage full — silently ignore
  }
}

export function useRequestLogger() {
  const [logs, setLogs] = useState<RequestLog[]>(() => loadLogsFromStorage())

  const logRequest = useCallback((log: RequestLog) => {
    setLogs((currentLogs) => {
      const newLogs = [log, ...currentLogs].slice(0, MAX_LOGS)
      saveLogsToStorage(newLogs)
      return newLogs
    })
  }, [])

  const clearLogs = useCallback(() => {
    setLogs([])
    saveLogsToStorage([])
  }, [])

  const exportLogs = useCallback((format: 'json' | 'csv' = 'json') => {
    if (format === 'json') {
      return JSON.stringify(logs, null, 2)
    } else {
      const headers = ['Timestamp', 'Method', 'Endpoint', 'Status', 'Duration (ms)', 'Error']
      const rows = logs.map(log => [
        new Date(log.timestamp).toISOString(),
        log.method,
        log.endpoint,
        log.responseStatus?.toString() || '',
        log.duration?.toString() || '',
        log.error || ''
      ])
      return [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(','))
      ].join('\n')
    }
  }, [logs])

  const downloadLogs = useCallback((format: 'json' | 'csv' = 'json') => {
    const content = exportLogs(format)
    const blob = new Blob([content], { type: format === 'json' ? 'application/json' : 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `request-logs-${new Date().toISOString().slice(0, 10)}.${format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [exportLogs])

  return {
    logs,
    logRequest,
    clearLogs,
    exportLogs,
    downloadLogs
  }
}

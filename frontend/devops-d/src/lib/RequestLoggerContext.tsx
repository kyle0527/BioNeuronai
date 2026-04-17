import { createContext, useContext, type ReactNode } from 'react'
import { useRequestLogger, type RequestLog } from '@/hooks/use-request-logger'

interface RequestLoggerContextValue {
  logs: RequestLog[]
  logRequest: (log: RequestLog) => void
  clearLogs: () => void
  exportLogs: (format?: 'json' | 'csv') => string
  downloadLogs: (format?: 'json' | 'csv') => void
}

const RequestLoggerContext = createContext<RequestLoggerContextValue | null>(null)

export function RequestLoggerProvider({ children }: { children: ReactNode }) {
  const logger = useRequestLogger()
  return (
    <RequestLoggerContext.Provider value={logger}>
      {children}
    </RequestLoggerContext.Provider>
  )
}

export function useRequestLoggerContext() {
  const context = useContext(RequestLoggerContext)
  if (!context) {
    throw new Error('useRequestLoggerContext must be used inside RequestLoggerProvider')
  }
  return context
}

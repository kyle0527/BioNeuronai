import type { RequestLog } from '@/hooks/use-request-logger'

export interface ApiResult<T = unknown> {
  status: number
  data: T
  headers: Record<string, string>
}

export interface ApiError {
  message: string
  status?: number
  details?: unknown
}

export interface RestApiResponse<T = unknown> {
  success: boolean
  message?: string
  data?: T
}

export interface ModuleStatus {
  name: string
  available: boolean
  error?: string | null
}

export interface StatusResponse {
  modules: ModuleStatus[]
  version?: string | null
  all_ok: boolean
}

export interface ChatResponse {
  success: boolean
  text: string
  language: string
  conversation_id: string
  confidence?: number | null
  market_context_used?: boolean
  stopped_reason?: string | null
  latency_ms?: number | null
}

type RequestLogger = (log: RequestLog) => void

let requestLogger: RequestLogger | null = null

export function setRequestLogger(logger: RequestLogger | null) {
  requestLogger = logger
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

function normalizeEndpoint(endpoint: string) {
  if (/^https?:\/\//i.test(endpoint)) {
    return endpoint
  }
  return `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`
}

function headersToObject(headers: Headers): Record<string, string> {
  const result: Record<string, string> = {}
  headers.forEach((value, key) => {
    result[key] = value
  })
  return result
}

async function parseResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json()
  }
  return response.text()
}

function createApiError(response: Response, data: unknown): ApiError {
  const message =
    typeof data === 'object' && data !== null && 'message' in data
      ? String((data as { message?: unknown }).message)
      : `Request failed with status ${response.status}`

  return {
    message,
    status: response.status,
    details: data,
  }
}

async function request<T = unknown>(
  method: string,
  endpoint: string,
  body?: unknown,
): Promise<ApiResult<T>> {
  const url = normalizeEndpoint(endpoint)
  const startedAt = performance.now()
  const requestHeaders: Record<string, string> = {
    Accept: 'application/json',
  }

  const init: RequestInit = {
    method,
    headers: requestHeaders,
  }

  if (body !== undefined) {
    requestHeaders['Content-Type'] = 'application/json'
    init.body = JSON.stringify(body)
  }

  let response: Response | null = null
  let responseData: unknown = null
  let error: ApiError | null = null

  try {
    response = await fetch(url, init)
    responseData = await parseResponse(response)

    if (!response.ok) {
      throw createApiError(response, responseData)
    }

    return {
      status: response.status,
      data: responseData as T,
      headers: headersToObject(response.headers),
    }
  } catch (caught) {
    error = caught && typeof caught === 'object' && 'message' in caught
      ? caught as ApiError
      : { message: String(caught) }
    throw error
  } finally {
    requestLogger?.({
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      timestamp: Date.now(),
      method,
      endpoint,
      requestBody: body,
      requestHeaders,
      responseStatus: response?.status,
      responseData,
      responseHeaders: response ? headersToObject(response.headers) : undefined,
      error: error?.message,
      duration: Math.round(performance.now() - startedAt),
    })
  }
}

export const api = {
  get: <T = unknown>(endpoint: string) => request<T>('GET', endpoint),
  post: <T = unknown>(endpoint: string, body?: unknown) => request<T>('POST', endpoint, body),
  put: <T = unknown>(endpoint: string, body?: unknown) => request<T>('PUT', endpoint, body),
  delete: <T = unknown>(endpoint: string) => request<T>('DELETE', endpoint),
}

export const endpoints = {
  status: () => api.get<StatusResponse>('/api/v1/status'),
  news: (body: { symbol: string; max_items: number }) =>
    api.post<RestApiResponse>('/api/v1/news', body),
  pretrade: (body: { symbol: string; action: 'long' | 'short' }) =>
    api.post<RestApiResponse>('/api/v1/pretrade', body),
  tradeStart: (body: { symbol: string; testnet: boolean }) =>
    api.post<RestApiResponse>('/api/v1/trade/start', body),
  tradeStop: () => api.post<RestApiResponse>('/api/v1/trade/stop', {}),
  chat: (body: {
    message: string
    language: 'auto' | 'zh' | 'en'
    symbol?: string | null
    conversation_id?: string | null
  }) => api.post<ChatResponse>('/api/v1/chat', body),
  backtestCatalog: (symbol?: string, interval?: string) => {
    const params = new URLSearchParams()
    if (symbol) params.set('symbol', symbol)
    if (interval) params.set('interval', interval)
    const query = params.toString()
    return api.get<RestApiResponse>(`/api/v1/backtest/catalog${query ? `?${query}` : ''}`)
  },
  backtestInspect: (symbol: string, interval: string, startDate?: string, endDate?: string) => {
    const params = new URLSearchParams({ symbol, interval })
    if (startDate) params.set('start_date', startDate)
    if (endDate) params.set('end_date', endDate)
    return api.get<RestApiResponse>(`/api/v1/backtest/inspect?${params.toString()}`)
  },
  backtestSimulate: (body: {
    symbol: string
    interval: string
    balance: number
    bars: number
    start_date?: string | null
    end_date?: string | null
  }) => api.post<RestApiResponse>('/api/v1/backtest/simulate', body),
  backtestRun: (body: {
    symbol: string
    interval: string
    balance: number
    warmup_bars: number
    start_date?: string | null
    end_date?: string | null
  }) => api.post<RestApiResponse>('/api/v1/backtest/run', body),
  backtestRuns: (limit = 10) =>
    api.get<RestApiResponse>(`/api/v1/backtest/runs?limit=${encodeURIComponent(String(limit))}`),
}

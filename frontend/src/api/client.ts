import { ApiError, type ApiErrorBody } from '../types/api'

const TOKEN_STORAGE_KEY = 'dme_access_token'

export type UnauthorizedHandler = () => void

let unauthorizedHandler: UnauthorizedHandler | null = null

export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  unauthorizedHandler = handler
}

export function getApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL
  if (typeof configured === 'string') {
    return configured.replace(/\/$/, '')
  }
  return ''
}

export function getStoredToken(): string | null {
  return sessionStorage.getItem(TOKEN_STORAGE_KEY)
}

export function storeToken(token: string): void {
  sessionStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearStoredToken(): void {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY)
}

interface RequestOptions {
  method?: string
  body?: BodyInit | null
  token?: string | null
  headers?: Record<string, string>
  json?: unknown
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers ?? {})
  const token = options.token === undefined ? getStoredToken() : options.token

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let body = options.body ?? null
  if (options.json !== undefined) {
    headers.set('Content-Type', 'application/json')
    body = JSON.stringify(options.json)
  }

  let response: Response
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body,
    })
  } catch {
    throw new Error('Network error. Check your connection and try again.')
  }

  if (response.status === 204) {
    return undefined as T
  }

  const contentType = response.headers.get('content-type') ?? ''
  const isJson = contentType.includes('application/json')
  const payload = isJson ? ((await response.json()) as ApiErrorBody | T) : null

  if (!response.ok) {
    const errorBody = (payload ?? {}) as ApiErrorBody
    if (response.status === 401) {
      clearStoredToken()
      unauthorizedHandler?.()
    }
    throw new ApiError(response.status, errorBody)
  }

  return payload as T
}

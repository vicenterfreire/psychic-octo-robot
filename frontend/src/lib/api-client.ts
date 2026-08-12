const defaultApiUrl = 'http://localhost:8000/api'

const apiUrl = (import.meta.env.VITE_API_URL ?? defaultApiUrl).replace(/\/$/, '')

/** Normalized non-success HTTP response exposed to feature-level recovery logic. */
export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as unknown
    if (
      typeof payload === 'object' &&
      payload !== null &&
      'detail' in payload &&
      typeof payload.detail === 'string'
    ) {
      return payload.detail
    }
  } catch {
    // The status remains useful when an upstream response is not JSON.
  }

  return `API request failed with status ${response.status}`
}

/**
 * Call the JSON API with the opaque session cookie and normalize its response boundary.
 *
 * The generic type is a compile-time contract, not runtime validation. Successful 204 responses
 * resolve as `undefined`; every other non-success response throws `ApiError`.
 */
export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json')
  }

  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    credentials: 'include',
    headers,
  })

  if (!response.ok) {
    throw new ApiError(response.status, await getErrorMessage(response))
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

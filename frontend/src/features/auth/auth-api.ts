import { ApiError, apiRequest } from '../../lib/api-client'

export type UserRole = 'organizer' | 'customer' | 'gate'

export interface CurrentUser {
  id: string
  email: string
  role: UserRole
}

export interface LoginCredentials {
  email: string
  password: string
}

export const sessionQueryKey = ['auth', 'session'] as const

export async function getCurrentUser(): Promise<CurrentUser | null> {
  try {
    return await apiRequest<CurrentUser>('/auth/me')
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null
    }
    throw error
  }
}

export function login(credentials: LoginCredentials): Promise<CurrentUser> {
  return apiRequest<CurrentUser>('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  })
}

export function logout(): Promise<void> {
  return apiRequest<void>('/auth/logout', { method: 'POST' })
}

export function roleHomePath(role: UserRole): string {
  return `/${role}`
}

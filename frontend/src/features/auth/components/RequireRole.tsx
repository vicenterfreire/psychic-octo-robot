import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { roleHomePath, type UserRole } from '../auth-api'
import { useSession } from '../hooks/use-session'

interface RequireRoleProps {
  role: UserRole
  children: ReactNode
}

/** Redirect cross-role navigation while leaving authoritative authorization to the API. */
export function RequireRole({ role, children }: RequireRoleProps) {
  const session = useSession()

  if (!session.data) {
    return null
  }

  if (session.data.role !== role) {
    return <Navigate to={roleHomePath(session.data.role)} replace />
  }

  return children
}

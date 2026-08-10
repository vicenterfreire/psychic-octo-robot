import { Navigate } from 'react-router-dom'
import { roleHomePath } from './auth-api'
import { useSession } from './use-session'

export function SessionRedirect() {
  const session = useSession()
  return session.data ? <Navigate to={roleHomePath(session.data.role)} replace /> : null
}

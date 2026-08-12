import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useSession } from '../hooks/use-session'

/** Restore authenticated navigation state without acting as a backend security boundary. */
export function RequireSession() {
  const session = useSession()
  const location = useLocation()

  if (session.isPending) {
    return <main className="centered-page">Restoring your session...</main>
  }

  if (session.isError) {
    return <main className="centered-page">The session service is unavailable.</main>
  }

  if (!session.data) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}

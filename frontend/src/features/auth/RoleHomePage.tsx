import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { logout, sessionQueryKey, type UserRole } from './auth-api'
import { useSession } from './use-session'

const roleContent: Record<UserRole, { eyebrow: string; title: string; next: string }> = {
  organizer: {
    eyebrow: 'Organizer workspace',
    title: 'Build an event people will remember.',
    next: 'Ticketmaster search and local event management arrive in the next increments.',
  },
  customer: {
    eyebrow: 'Customer workspace',
    title: 'Find your next live moment.',
    next: 'Published event discovery, reservations, and tickets are coming next.',
  },
  gate: {
    eyebrow: 'Gate workspace',
    title: 'Keep every entrance clear and trusted.',
    next: 'Manual and camera ticket validation will build on this protected route.',
  },
}

interface RoleHomePageProps {
  role: UserRole
}

export function RoleHomePage({ role }: RoleHomePageProps) {
  const session = useSession()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const content = roleContent[role]
  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(sessionQueryKey, null)
      navigate('/login', { replace: true })
    },
  })

  return (
    <div className="page-shell">
      <header className="site-header">
        <Link className="brand" to="/" aria-label="Gather home">
          <span className="brand__mark" aria-hidden="true" />
          Gather
        </Link>
        <span className="account-chip">{session.data?.email}</span>
      </header>

      <main className="role-workspace">
        <p className="eyebrow">{content.eyebrow}</p>
        <h1>{content.title}</h1>
        <section className="role-card">
          <div>
            <p className="role-card__label">Authenticated foundation</p>
            <h2>Your persistent session is active.</h2>
            <p>{content.next}</p>
          </div>
          <button
            className="secondary-button"
            type="button"
            disabled={logoutMutation.isPending}
            onClick={() => logoutMutation.mutate()}
          >
            {logoutMutation.isPending ? 'Signing out...' : 'Sign out'}
          </button>
        </section>
        {logoutMutation.isError && <p className="form-error">Unable to sign out. Try again.</p>}
      </main>
    </div>
  )
}

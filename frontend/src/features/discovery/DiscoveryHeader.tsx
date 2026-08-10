import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { logout, roleHomePath, sessionQueryKey } from '../auth/auth-api'
import { useSession } from '../auth/use-session'

interface DiscoveryHeaderProps {
  authenticated: boolean
}

function Brand() {
  return (
    <Link className="brand" to="/" aria-label="Gather home">
      <span className="brand__mark" aria-hidden="true" />
      Gather
    </Link>
  )
}

function PublicDiscoveryHeader() {
  return (
    <header className="site-header">
      <Brand />
      <Link className="header-link" to="/login">
        Sign in
      </Link>
    </header>
  )
}

function AuthenticatedDiscoveryHeader() {
  const session = useSession()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(sessionQueryKey, null)
      navigate('/login', { replace: true })
    },
  })

  return (
    <header className="site-header">
      <Brand />
      <div className="workspace-account">
        {session.data && (
          <Link className="account-chip" to={roleHomePath(session.data.role)}>
            {session.data.email}
          </Link>
        )}
        <button
          className="header-action"
          type="button"
          disabled={logoutMutation.isPending}
          onClick={() => logoutMutation.mutate()}
        >
          {logoutMutation.isPending ? 'Signing out...' : 'Sign out'}
        </button>
      </div>
    </header>
  )
}

export function DiscoveryHeader({ authenticated }: DiscoveryHeaderProps) {
  return authenticated ? <AuthenticatedDiscoveryHeader /> : <PublicDiscoveryHeader />
}

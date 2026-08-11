import { useMutation, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { ApiError } from '../../lib/api-client'
import {
  login,
  roleHomePath,
  sessionQueryKey,
  type CurrentUser,
  type LoginCredentials,
} from './auth-api'
import { useSession } from './hooks/use-session'

const demoAccounts: Array<LoginCredentials & { label: string }> = [
  { label: 'Organizer', email: 'organizer@example.com', password: 'Organizer123!' },
  { label: 'Customer', email: 'customer.one@example.com', password: 'Customer123!' },
  { label: 'Gate', email: 'gate@example.com', password: 'Gate123!' },
]

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const session = useSession()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (user: CurrentUser) => {
      queryClient.setQueryData(sessionQueryKey, user)
      navigate(roleHomePath(user.role), { replace: true })
    },
  })

  if (session.data) {
    return <Navigate to={roleHomePath(session.data.role)} replace />
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    loginMutation.mutate({ email, password })
  }

  function fillDemoAccount(account: LoginCredentials) {
    setEmail(account.email)
    setPassword(account.password)
    loginMutation.reset()
  }

  const errorMessage =
    loginMutation.error instanceof ApiError
      ? loginMutation.error.message
      : loginMutation.isError
        ? 'Unable to reach the authentication service.'
        : null

  return (
    <div className="auth-shell">
      <header className="site-header">
        <Link className="brand" to="/" aria-label="Gather home">
          <span className="brand__mark" aria-hidden="true" />
          Gather
        </Link>
        <span className="project-label">Elite Dev Challenge 2026</span>
      </header>

      <main className="auth-layout">
        <section className="auth-intro">
          <p className="eyebrow">Welcome back</p>
          <h1>Your next event starts here.</h1>
          <p>Sign in as an organizer, customer, or gate operator. Your session lasts seven days.</p>
        </section>

        <section className="auth-card" aria-labelledby="login-heading">
          <p className="auth-card__label">Account access</p>
          <h2 id="login-heading">Sign in</h2>

          <form onSubmit={submit}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />

            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />

            {errorMessage && <p className="form-error">{errorMessage}</p>}

            <button className="primary-button" type="submit" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="demo-accounts">
            <p>Use a seeded account</p>
            <div>
              {demoAccounts.map((account) => (
                <button key={account.label} type="button" onClick={() => fillDemoAccount(account)}>
                  {account.label}
                </button>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

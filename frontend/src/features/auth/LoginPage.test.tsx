import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { LoginPage } from './LoginPage'
import { RequireRole } from './RequireRole'
import { RequireSession } from './RequireSession'

function apiResponse(status: number, payload?: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response
}

function createQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('authentication flow', () => {
  it('signs in with a seeded account and enters its role workspace', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(apiResponse(401, { detail: 'Authentication is required.' }))
      .mockResolvedValueOnce(
        apiResponse(200, {
          id: '11111111-1111-4111-8111-111111111111',
          email: 'organizer@example.com',
          role: 'organizer',
        }),
      )
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()

    render(
      <QueryClientProvider client={createQueryClient()}>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/organizer" element={<p>Organizer workspace loaded</p>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await screen.findByRole('heading', { name: 'Sign in' })
    await user.click(screen.getByRole('button', { name: 'Organizer' }))
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Organizer workspace loaded')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://localhost:8000/api/auth/login',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify({
          email: 'organizer@example.com',
          password: 'Organizer123!',
        }),
      }),
    )
  })

  it('redirects an authenticated user away from another role workspace', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        apiResponse(200, {
          id: '33333333-3333-4333-8333-333333333333',
          email: 'gate@example.com',
          role: 'gate',
        }),
      ),
    )

    render(
      <QueryClientProvider client={createQueryClient()}>
        <MemoryRouter initialEntries={['/organizer']}>
          <Routes>
            <Route element={<RequireSession />}>
              <Route
                path="/organizer"
                element={
                  <RequireRole role="organizer">
                    <p>Organizer-only content</p>
                  </RequireRole>
                }
              />
              <Route path="/gate" element={<p>Gate workspace loaded</p>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect(await screen.findByText('Gate workspace loaded')).toBeInTheDocument()
    expect(screen.queryByText('Organizer-only content')).not.toBeInTheDocument()
  })
})

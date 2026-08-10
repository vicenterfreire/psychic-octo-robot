import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { OrganizerCatalogPage } from './OrganizerCatalogPage'

function apiResponse(status: number, payload?: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <OrganizerCatalogPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function organizerSession(): Response {
  return apiResponse(200, {
    id: '11111111-1111-4111-8111-111111111111',
    email: 'organizer@example.com',
    role: 'organizer',
  })
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('OrganizerCatalogPage', () => {
  it('searches the backend and selects a normalized Ticketmaster event', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(organizerSession())
      .mockResolvedValueOnce(
        apiResponse(200, {
          items: [
            {
              provider: 'ticketmaster',
              provider_event_id: 'event-123',
              name: 'Aurora World Tour',
              description: 'A live music event.',
              image_url: 'https://images.test/event.jpg',
              source_url: 'https://www.ticketmaster.com/event-123',
            },
          ],
        }),
      )
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderPage()

    await screen.findByText('organizer@example.com')
    await user.type(screen.getByRole('searchbox', { name: 'Event or artist' }), 'Aurora')
    await user.click(screen.getByRole('button', { name: 'Search catalog' }))

    expect(await screen.findByRole('heading', { name: 'Aurora World Tour' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Use this event' }))
    expect(screen.getByRole('button', { name: 'Selected' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('Aurora World Tour', { selector: 'strong' })).toBeInTheDocument()

    const searchUrl = String(fetchMock.mock.calls[1][0])
    expect(searchUrl).toBe('http://localhost:8000/api/catalog/events?q=Aurora')
    expect(searchUrl).not.toContain('apikey')
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      searchUrl,
      expect.objectContaining({ credentials: 'include' }),
    )
  })

  it('shows an actionable empty state', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce(organizerSession())
        .mockResolvedValueOnce(
          apiResponse(200, {
            items: [],
          }),
        ),
    )
    const user = userEvent.setup()
    renderPage()

    await screen.findByText('organizer@example.com')
    await user.type(screen.getByRole('searchbox', { name: 'Event or artist' }), 'No matches')
    await user.click(screen.getByRole('button', { name: 'Search catalog' }))

    expect(await screen.findByText(/No Ticketmaster events matched/)).toBeInTheDocument()
  })

  it('shows the stable backend error without provider details', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce(organizerSession())
        .mockResolvedValueOnce(
          apiResponse(503, { detail: 'Catalog provider quota is temporarily unavailable.' }),
        ),
    )
    const user = userEvent.setup()
    renderPage()

    await screen.findByText('organizer@example.com')
    await user.type(screen.getByRole('searchbox', { name: 'Event or artist' }), 'Aurora')
    await user.click(screen.getByRole('button', { name: 'Search catalog' }))

    expect(await screen.findByText(/quota is temporarily unavailable/)).toBeInTheDocument()
  })
})

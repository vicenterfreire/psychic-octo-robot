import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
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

function managedEvent(status: 'draft' | 'published' = 'draft') {
  return {
    id: '77777777-7777-4777-8777-777777777777',
    organizer_id: '11111111-1111-4111-8111-111111111111',
    name: 'Aurora Local Night',
    description: 'Local event copy.',
    venue_name: 'Gather Hall',
    address: '100 Avenida das Artes',
    city: 'Sao Paulo',
    country_code: 'BR',
    start_at: '2032-09-22T01:00:00Z',
    capacity: 100,
    price_minor: 15000,
    currency: 'BRL',
    status,
    source: {
      provider: 'ticketmaster',
      provider_event_id: 'event-123',
      name: 'Aurora World Tour',
      description: 'Provider copy.',
      image_url: null,
      source_url: 'https://www.ticketmaster.com/event-123',
    },
    created_at: '2026-08-10T12:00:00Z',
    updated_at: '2026-08-10T12:00:00Z',
  }
}

function catalogResult(): Response {
  return apiResponse(200, {
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
      .mockResolvedValueOnce(apiResponse(200, { items: [] }))
      .mockResolvedValueOnce(catalogResult())
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

    const searchUrl = String(fetchMock.mock.calls[2][0])
    expect(searchUrl).toBe('http://localhost:8000/api/catalog/events?q=Aurora')
    expect(searchUrl).not.toContain('apikey')
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
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
        .mockResolvedValueOnce(apiResponse(200, { items: [] }))
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
        .mockResolvedValueOnce(apiResponse(200, { items: [] }))
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

  it('creates a local draft from the selected trusted catalog identifier', async () => {
    const draft = managedEvent()
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(organizerSession())
      .mockResolvedValueOnce(apiResponse(200, { items: [] }))
      .mockResolvedValueOnce(catalogResult())
      .mockResolvedValueOnce(apiResponse(201, draft))
      .mockResolvedValueOnce(apiResponse(200, { items: [draft] }))
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderPage()

    await screen.findByText('organizer@example.com')
    await user.type(screen.getByRole('searchbox', { name: 'Event or artist' }), 'Aurora')
    await user.click(screen.getByRole('button', { name: 'Search catalog' }))
    await user.click(await screen.findByRole('button', { name: 'Use this event' }))

    await user.type(screen.getByLabelText('Venue'), 'Gather Hall')
    await user.type(screen.getByLabelText('Address'), '100 Avenida das Artes')
    await user.type(screen.getByLabelText('City'), 'Sao Paulo')
    fireEvent.change(screen.getByLabelText('Starts at'), { target: { value: '2032-09-21T22:00' } })
    await user.clear(screen.getByLabelText('Price (BRL)'))
    await user.type(screen.getByLabelText('Price (BRL)'), '150.00')
    await user.click(screen.getByRole('button', { name: 'Create draft' }))

    expect(await screen.findByText('draft')).toBeInTheDocument()
    const createCall = fetchMock.mock.calls[3]
    expect(String(createCall[0])).toBe('http://localhost:8000/api/events')
    const createBody = JSON.parse(String((createCall[1] as RequestInit).body))
    expect(createBody).toEqual(
      expect.objectContaining({
        provider_event_id: 'event-123',
        name: 'Aurora World Tour',
        venue_name: 'Gather Hall',
        capacity: 100,
        price_minor: 15000,
        currency: 'BRL',
      }),
    )
    expect(createBody).not.toHaveProperty('source_url')
  })

  it('publishes an owned draft only after an explicit action', async () => {
    const draft = managedEvent()
    const published = managedEvent('published')
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(organizerSession())
      .mockResolvedValueOnce(apiResponse(200, { items: [draft] }))
      .mockResolvedValueOnce(apiResponse(200, published))
      .mockResolvedValueOnce(apiResponse(200, { items: [published] }))
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderPage()

    expect(await screen.findByText('draft')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Publish' }))

    expect(await screen.findByText('published')).toBeInTheDocument()
    expect(String(fetchMock.mock.calls[2][0])).toBe(
      'http://localhost:8000/api/events/77777777-7777-4777-8777-777777777777/publish',
    )
    expect(fetchMock.mock.calls[2][1]).toEqual(expect.objectContaining({ method: 'POST' }))
  })
})

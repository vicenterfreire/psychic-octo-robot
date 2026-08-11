import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { EventDetailPage } from './EventDetailPage'
import { EventDiscoveryPage } from './EventDiscoveryPage'

function apiResponse(status: number, payload: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response
}

function publishedEvent() {
  return {
    id: '55555555-5555-4555-8555-555555555555',
    name: 'Aurora Live 2032',
    description: 'A customer-visible local event.',
    venue_name: 'Discovery Arena',
    address: '100 Search Avenue',
    city: 'Curitiba',
    country_code: 'BR',
    start_at: '2032-09-22T01:00:00Z',
    capacity: 10,
    available_quantity: 5,
    price_minor: 12345,
    currency: 'BRL',
    image_url: 'https://images.test/aurora.jpg',
  }
}

function renderWithQueryClient(ui: ReactNode, initialPath = '/') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('published event discovery', () => {
  it('shows event date, location, price, and current availability', async () => {
    const fetchMock = vi.fn().mockResolvedValue(apiResponse(200, { items: [publishedEvent()] }))
    vi.stubGlobal('fetch', fetchMock)
    renderWithQueryClient(<EventDiscoveryPage />)

    expect(await screen.findByRole('heading', { name: 'Aurora Live 2032' })).toBeInTheDocument()
    expect(screen.getByText(/Discovery Arena · Curitiba, BR/)).toBeInTheDocument()
    expect(screen.getByText(/123\.45/)).toBeInTheDocument()
    expect(screen.getByText('5 tickets available')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'View event' })).toHaveAttribute(
      'href',
      '/events/55555555-5555-4555-8555-555555555555',
    )
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/events',
      expect.objectContaining({ credentials: 'include' }),
    )
  })

  it('submits a basic text search and presents an actionable empty state', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(apiResponse(200, { items: [publishedEvent()] }))
      .mockResolvedValueOnce(apiResponse(200, { items: [] }))
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderWithQueryClient(<EventDiscoveryPage />)

    await screen.findByRole('heading', { name: 'Aurora Live 2032' })
    await user.type(
      screen.getByRole('searchbox', { name: 'Search published events' }),
      '  Porto Alegre  ',
    )
    await user.click(screen.getByRole('button', { name: 'Search' }))

    expect(await screen.findByText(/No published events match “Porto Alegre”/)).toBeInTheDocument()
    expect(String(fetchMock.mock.calls[1][0])).toBe(
      'http://localhost:8000/api/events?q=Porto+Alegre',
    )
  })

  it('shows the complete public event detail needed before reservation', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(apiResponse(200, publishedEvent())))
    renderWithQueryClient(
      <Routes>
        <Route path="/events/:eventId" element={<EventDetailPage />} />
      </Routes>,
      '/events/55555555-5555-4555-8555-555555555555',
    )

    expect(await screen.findByRole('heading', { name: 'Aurora Live 2032' })).toBeInTheDocument()
    expect(screen.getByText('100 Search Avenue, Curitiba, BR')).toBeInTheDocument()
    expect(screen.getByText('5 tickets available')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Sign in as a customer' })).toHaveAttribute(
      'href',
      '/login',
    )
  })

  it('creates a customer hold with the selected quantity', async () => {
    const reservation = {
      id: '66666666-6666-4666-8666-666666666666',
      event_id: publishedEvent().id,
      quantity: 2,
      status: 'pending',
      created_at: '2032-09-21T15:00:00Z',
      expires_at: '2032-09-21T15:10:00Z',
      server_time: '2032-09-21T15:00:00Z',
    }
    const fetchMock = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) {
        return apiResponse(200, {
          id: '22222222-2222-4222-8222-222222222221',
          email: 'customer.one@example.com',
          role: 'customer',
        })
      }
      if (url.endsWith('/reservations') && init?.method === 'POST') {
        return apiResponse(201, reservation)
      }
      return apiResponse(200, publishedEvent())
    })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderWithQueryClient(
      <Routes>
        <Route path="/customer/events/:eventId" element={<EventDetailPage authenticated />} />
        <Route
          path="/customer/reservations/:reservationId"
          element={<div>Reservation created</div>}
        />
      </Routes>,
      `/customer/events/${publishedEvent().id}`,
    )

    await screen.findByRole('heading', { name: 'Aurora Live 2032' })
    const quantity = screen.getByRole('spinbutton', { name: 'Ticket quantity' })
    await user.clear(quantity)
    await user.type(quantity, '2')
    await user.click(screen.getByRole('button', { name: 'Hold 2 tickets' }))

    expect(await screen.findByText('Reservation created')).toBeInTheDocument()
    const reservationCall = fetchMock.mock.calls.find(
      ([url, init]) => String(url).endsWith('/reservations') && init?.method === 'POST',
    )
    expect(reservationCall).toBeDefined()
    expect(JSON.parse(String(reservationCall?.[1]?.body))).toEqual({
      event_id: publishedEvent().id,
      quantity: 2,
    })
  })
})

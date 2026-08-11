import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ReservationHoldPage } from './ReservationHoldPage'

function apiResponse(status: number, payload: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('reservation hold recovery', () => {
  it('restores a server-expired hold with an actionable retry path', async () => {
    const eventId = '55555555-5555-4555-8555-555555555555'
    const reservationId = '66666666-6666-4666-8666-666666666666'
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: string | URL | Request) => {
        const url = String(input)
        if (url.endsWith('/auth/me')) {
          return apiResponse(200, {
            id: '22222222-2222-4222-8222-222222222221',
            email: 'customer.one@example.com',
            role: 'customer',
          })
        }
        if (url.includes('/events/')) {
          return apiResponse(200, {
            id: eventId,
            name: 'Aurora Live 2032',
          })
        }
        return apiResponse(200, {
          id: reservationId,
          event_id: eventId,
          quantity: 2,
          status: 'expired',
          created_at: '2032-09-21T15:00:00Z',
          expires_at: '2032-09-21T15:10:00Z',
          server_time: '2032-09-21T15:11:00Z',
          ticket_count: 0,
        })
      }),
    )
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[`/customer/reservations/${reservationId}`]}>
          <Routes>
            <Route path="/customer/reservations/:reservationId" element={<ReservationHoldPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect(await screen.findByRole('heading', { name: 'Your hold expired.' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Choose tickets again' })).toHaveAttribute(
      'href',
      `/customer/events/${eventId}`,
    )
  })

  it('submits a deterministic approval and presents the issued quantity', async () => {
    const eventId = '55555555-5555-4555-8555-555555555555'
    const reservationId = '66666666-6666-4666-8666-666666666666'
    const pendingReservation = {
      id: reservationId,
      event_id: eventId,
      quantity: 2,
      status: 'pending',
      created_at: '2032-09-21T15:00:00Z',
      expires_at: '2032-09-21T15:10:00Z',
      server_time: '2032-09-21T15:00:00Z',
      ticket_count: 0,
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
      if (url.includes('/events/')) {
        return apiResponse(200, { id: eventId, name: 'Aurora Live 2032' })
      }
      if (url.endsWith('/payment') && init?.method === 'POST') {
        return apiResponse(200, {
          ...pendingReservation,
          status: 'approved',
          ticket_count: 2,
        })
      }
      return apiResponse(200, pendingReservation)
    })
    vi.stubGlobal('fetch', fetchMock)
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const user = userEvent.setup()
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[`/customer/reservations/${reservationId}`]}>
          <Routes>
            <Route path="/customer/reservations/:reservationId" element={<ReservationHoldPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await user.click(await screen.findByRole('button', { name: 'Simulate approval' }))

    expect(
      await screen.findByRole('heading', { name: 'Your tickets are issued.' }),
    ).toBeInTheDocument()
    expect(screen.getByText(/2 tickets were created for Aurora Live 2032/)).toBeInTheDocument()
    const paymentCall = fetchMock.mock.calls.find(
      ([url, init]) => String(url).endsWith('/payment') && init?.method === 'POST',
    )
    expect(JSON.parse(String(paymentCall?.[1]?.body))).toEqual({ outcome: 'approved' })
  })
})

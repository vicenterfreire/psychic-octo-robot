import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { CustomerTicketsPage } from './CustomerTicketsPage'
import { SharedTicketPage } from './SharedTicketPage'

const token = `v1.${'7'.repeat(32)}.${'a'.repeat(43)}`

function apiResponse(status: number, payload: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response
}

function event() {
  return {
    id: '55555555-5555-4555-8555-555555555555',
    name: 'Aurora Live 2032',
    venue_name: 'Gather Hall',
    address: '100 Test Avenue',
    city: 'Sao Paulo',
    country_code: 'BR',
    start_at: '2032-09-21T22:00:00-03:00',
    image_url: null,
  }
}

function renderWithQueryClient(ui: ReactNode, path: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('ticket presentation and sharing', () => {
  it('renders the customer ticket QR and generated bearer link', async () => {
    const shareUrl = `http://localhost:5173/tickets/share/${token}`
    const fetchMock = vi.fn(async (input: string | URL | Request) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) {
        return apiResponse(200, {
          id: '22222222-2222-4222-8222-222222222221',
          email: 'customer.one@example.com',
          role: 'customer',
        })
      }
      return apiResponse(200, {
        items: [
          {
            id: '77777777-7777-4777-8777-777777777771',
            ticket_number: 1,
            issued_at: '2032-09-01T15:00:00Z',
            is_used: false,
            is_revoked: false,
            token,
            share_url: shareUrl,
            event: event(),
          },
        ],
      })
    })
    vi.stubGlobal('fetch', fetchMock)
    renderWithQueryClient(<CustomerTicketsPage />, '/customer/tickets')

    expect(await screen.findByRole('heading', { name: 'Aurora Live 2032' })).toBeInTheDocument()
    expect(screen.getByText('Ready for entry')).toBeInTheDocument()
    expect(screen.getByLabelText('QR for Aurora Live 2032')).toContainElement(
      screen.getByTitle('QR for Aurora Live 2032'),
    )
    expect(screen.getByRole('link', { name: 'Open shared view' })).toHaveAttribute('href', shareUrl)
    expect(screen.queryByText(token)).not.toBeInTheDocument()
  })

  it('loads a bearer ticket without an authenticated Customer session', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      apiResponse(200, {
        ticket_number: 1,
        issued_at: '2032-09-01T15:00:00Z',
        is_used: false,
        is_revoked: false,
        event: event(),
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    renderWithQueryClient(
      <Routes>
        <Route path="/tickets/share/:token" element={<SharedTicketPage />} />
      </Routes>,
      `/tickets/share/${token}`,
    )

    expect(await screen.findByRole('heading', { name: 'Aurora Live 2032' })).toBeInTheDocument()
    expect(screen.getByLabelText('Shared QR for Aurora Live 2032')).toBeInTheDocument()
    expect(screen.getByText(/Anyone with this link/)).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(String(fetchMock.mock.calls[0][0])).toContain(`/api/tickets/shared/${token}`)
  })
})

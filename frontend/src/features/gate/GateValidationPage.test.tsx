import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { GateValidationPage } from './GateValidationPage'
import type { GateValidationOutcome } from './gate-api'

const eventId = '55555555-5555-4555-8555-555555555555'
const token = `v1.${'7'.repeat(32)}.${'a'.repeat(43)}`

function apiResponse(status: number, payload: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response
}

function renderGatePage(outcome: GateValidationOutcome) {
  const fetchMock = vi.fn(async (input: string | URL | Request) => {
    const url = String(input)
    if (url.endsWith('/auth/me')) {
      return apiResponse(200, {
        id: '33333333-3333-4333-8333-333333333333',
        email: 'gate@example.com',
        role: 'gate',
      })
    }
    if (url.endsWith('/gate/events')) {
      return apiResponse(200, {
        items: [
          {
            id: eventId,
            name: 'Aurora Live 2030',
            venue_name: 'Gather Hall',
            city: 'Sao Paulo',
            country_code: 'BR',
            start_at: '2030-09-21T22:00:00-03:00',
          },
        ],
      })
    }
    if (url.endsWith('/gate/validations')) {
      return apiResponse(200, {
        outcome,
        ticket_number: outcome === 'valid' || outcome === 'already_used' ? 1 : null,
        used_at: outcome === 'valid' || outcome === 'already_used' ? '2030-09-21T21:45:00Z' : null,
      })
    }
    throw new Error(`Unexpected request: ${url}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <GateValidationPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('manual gate validation', () => {
  it.each([
    ['valid', 'Entry approved'],
    ['invalid', 'Ticket invalid'],
    ['already_used', 'Already used'],
    ['wrong_event', 'Wrong event'],
  ] as const)('presents the %s outcome clearly', async (outcome, title) => {
    const fetchMock = renderGatePage(outcome)

    expect(
      await screen.findByRole('option', { name: 'Aurora Live 2030 — Gather Hall' }),
    ).toBeVisible()
    fireEvent.change(screen.getByLabelText('Ticket code'), { target: { value: token } })
    fireEvent.click(screen.getByRole('button', { name: 'Validate ticket' }))

    expect(await screen.findByRole('heading', { name: title })).toBeVisible()
    expect(screen.getByLabelText('Ticket code')).toHaveValue('')
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/gate/validations'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ event_id: eventId, token }),
      }),
    )
  })
})

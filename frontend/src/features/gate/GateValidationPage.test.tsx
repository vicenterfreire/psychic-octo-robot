import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { GateValidationPage } from './GateValidationPage'
import type { GateValidationOutcome } from './gate-api'

type ScanCallback = (
  result: { getText: () => string } | undefined,
  error: unknown,
  controls: { stop: () => void },
) => void

const zxingMocks = vi.hoisted(() => ({
  decodeFromConstraints: vi.fn(),
  scanCallback: undefined as ScanCallback | undefined,
  stop: vi.fn(),
}))

vi.mock('@zxing/browser', () => ({
  BrowserQRCodeReader: class {
    decodeFromConstraints = zxingMocks.decodeFromConstraints
  },
}))

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

beforeEach(() => {
  Object.defineProperty(window, 'isSecureContext', {
    configurable: true,
    value: true,
  })
  Object.defineProperty(window.navigator, 'mediaDevices', {
    configurable: true,
    value: { getUserMedia: vi.fn() },
  })
  zxingMocks.decodeFromConstraints.mockImplementation(
    async (_constraints: unknown, _video: unknown, callback: ScanCallback) => {
      zxingMocks.scanCallback = callback
      return { stop: zxingMocks.stop }
    },
  )
})

afterEach(() => {
  cleanup()
  zxingMocks.scanCallback = undefined
  vi.clearAllMocks()
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

describe('camera gate validation', () => {
  it('keeps the camera off until the Gate user explicitly starts it', async () => {
    renderGatePage('valid')

    expect(
      await screen.findByRole('option', { name: 'Aurora Live 2030 — Gather Hall' }),
    ).toBeVisible()
    expect(screen.getByLabelText('Ticket code')).toBeEnabled()
    expect(
      screen.getByText('Camera is off. Start it only when you are ready to scan.'),
    ).toBeVisible()
    expect(zxingMocks.decodeFromConstraints).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Start camera' }))

    await waitFor(() => expect(zxingMocks.decodeFromConstraints).toHaveBeenCalledTimes(1))
    expect(screen.getByText('Camera active. Hold the QR code inside the frame.')).toBeVisible()
  })

  it.each([
    ['valid', 'Entry approved'],
    ['invalid', 'Ticket invalid'],
    ['already_used', 'Already used'],
    ['wrong_event', 'Wrong event'],
  ] as const)('submits a scanned token to the same %s outcome flow', async (outcome, title) => {
    const fetchMock = renderGatePage(outcome)

    expect(
      await screen.findByRole('option', { name: 'Aurora Live 2030 — Gather Hall' }),
    ).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Start camera' }))
    await waitFor(() => expect(zxingMocks.scanCallback).toBeDefined())

    await act(async () => {
      zxingMocks.scanCallback?.({ getText: () => token }, undefined, { stop: zxingMocks.stop })
      zxingMocks.scanCallback?.({ getText: () => token }, undefined, { stop: zxingMocks.stop })
    })

    expect(await screen.findByRole('heading', { name: title })).toBeVisible()
    expect(zxingMocks.stop).toHaveBeenCalled()
    expect(
      fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/gate/validations')),
    ).toHaveLength(1)
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/gate/validations'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ event_id: eventId, token }),
      }),
    )
  })

  it.each([
    [
      'NotAllowedError',
      'Camera access was denied. Allow it in browser settings or use manual entry below.',
    ],
    ['NotFoundError', 'No usable camera was found. Connect a camera or use manual entry below.'],
  ])('keeps manual entry available after a %s camera failure', async (errorName, message) => {
    zxingMocks.decodeFromConstraints.mockRejectedValueOnce(
      Object.assign(new Error('Camera unavailable'), { name: errorName }),
    )
    renderGatePage('valid')

    expect(
      await screen.findByRole('option', { name: 'Aurora Live 2030 — Gather Hall' }),
    ).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Start camera' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(message)
    expect(screen.getByLabelText('Ticket code')).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Validate ticket' })).toBeVisible()
  })

  it('explains unsupported camera access without hiding manual entry', async () => {
    Object.defineProperty(window.navigator, 'mediaDevices', {
      configurable: true,
      value: undefined,
    })
    renderGatePage('valid')

    expect(
      await screen.findByRole('option', { name: 'Aurora Live 2030 — Gather Hall' }),
    ).toBeVisible()
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'This browser cannot access a camera.',
    )
    expect(screen.getByRole('button', { name: 'Start camera' })).toBeDisabled()
    expect(zxingMocks.decodeFromConstraints).not.toHaveBeenCalled()
    expect(screen.getByLabelText('Ticket code')).toBeEnabled()
  })

  it('explains that a LAN HTTP origin cannot request camera permission', async () => {
    Object.defineProperty(window, 'isSecureContext', {
      configurable: true,
      value: false,
    })
    renderGatePage('valid')

    expect(
      await screen.findByRole('option', { name: 'Aurora Live 2030 — Gather Hall' }),
    ).toBeVisible()
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Camera access requires HTTPS when this page is opened from another device.',
    )
    expect(screen.getByRole('button', { name: 'Start camera' })).toBeDisabled()
    expect(zxingMocks.decodeFromConstraints).not.toHaveBeenCalled()
    expect(screen.getByLabelText('Ticket code')).toBeEnabled()
  })
})

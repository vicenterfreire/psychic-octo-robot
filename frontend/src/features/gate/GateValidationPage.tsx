import { useMutation, useQuery } from '@tanstack/react-query'
import { type FormEvent, useRef, useState } from 'react'
import { formatEventDate } from '../../lib/event-display'
import { SiteHeader } from '../navigation/components/SiteHeader'
import { GateCameraScanner } from './components/GateCameraScanner'
import {
  gateEventsQueryKey,
  getGateEvents,
  validateGateTicket,
  type GateValidationOutcome,
  type GateValidationResult,
} from './gate-api'

const outcomePresentation: Record<
  GateValidationOutcome,
  { eyebrow: string; title: string; detail: string }
> = {
  valid: {
    eyebrow: 'Admission accepted',
    title: 'Entry approved',
    detail: 'The ticket is authentic and has now been marked as used.',
  },
  invalid: {
    eyebrow: 'Admission denied',
    title: 'Ticket invalid',
    detail: 'The code is malformed, unknown, revoked, or has an invalid signature.',
  },
  already_used: {
    eyebrow: 'Admission denied',
    title: 'Already used',
    detail: 'This authentic ticket was accepted previously and cannot be used again.',
  },
  wrong_event: {
    eyebrow: 'Admission denied',
    title: 'Wrong event',
    detail: 'This authentic ticket belongs to a different event than the one selected.',
  },
}

function ValidationFeedback({ result }: { result: GateValidationResult }) {
  const presentation = outcomePresentation[result.outcome]
  return (
    <section
      className={`gate-result gate-result--${result.outcome.replace('_', '-')}`}
      role="status"
      aria-live="assertive"
    >
      <p className="gate-result__eyebrow">{presentation.eyebrow}</p>
      <h2>{presentation.title}</h2>
      <p>{presentation.detail}</p>
      {result.ticket_number !== null && <strong>Ticket #{result.ticket_number}</strong>}
    </section>
  )
}

export function GateValidationPage() {
  const [eventId, setEventId] = useState('')
  const [token, setToken] = useState('')
  const validationLockedRef = useRef(false)
  const eventsQuery = useQuery({
    queryKey: gateEventsQueryKey,
    queryFn: getGateEvents,
  })
  const validationMutation = useMutation({
    mutationFn: validateGateTicket,
    onSuccess: () => setToken(''),
    onSettled: () => {
      validationLockedRef.current = false
    },
  })
  const selectedEventId = eventId || eventsQuery.data?.[0]?.id || ''
  const selectedEvent = eventsQuery.data?.find((event) => event.id === selectedEventId)

  function changeEvent(nextEventId: string) {
    setEventId(nextEventId)
    validationMutation.reset()
  }

  function changeToken(nextToken: string) {
    setToken(nextToken)
    validationMutation.reset()
  }

  function submitValidation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    requestValidation(token)
  }

  function requestValidation(nextToken: string) {
    const normalizedToken = nextToken.trim()
    if (!selectedEventId || !normalizedToken || validationLockedRef.current) {
      return
    }

    validationLockedRef.current = true
    validationMutation.mutate({ event_id: selectedEventId, token: normalizedToken })
  }

  function scanToken(scannedToken: string) {
    setToken(scannedToken.trim())
    validationMutation.reset()
    requestValidation(scannedToken)
  }

  return (
    <div className="page-shell gate-shell">
      <SiteHeader authenticated />
      <main className="gate-workspace">
        <section className="gate-heading">
          <div>
            <p className="eyebrow">Gate validation</p>
            <h1>Fast checks. Clear decisions.</h1>
          </div>
          <p>
            Select the event, scan or enter the ticket code, and trust only the result returned by
            the server.
          </p>
        </section>

        {eventsQuery.isPending && <section className="empty-panel">Loading gate events...</section>}

        {eventsQuery.isError && (
          <section className="empty-panel">
            <h2>Events unavailable.</h2>
            <p>Check the connection and try loading the event list again.</p>
            <button
              className="secondary-button"
              type="button"
              onClick={() => eventsQuery.refetch()}
            >
              Try again
            </button>
          </section>
        )}

        {eventsQuery.data?.length === 0 && (
          <section className="empty-panel">
            <h2>No published events.</h2>
            <p>An Organizer must publish an event before the Gate can validate its tickets.</p>
          </section>
        )}

        {eventsQuery.data && eventsQuery.data.length > 0 && (
          <div className="gate-layout">
            <form className="gate-form" onSubmit={submitValidation}>
              <div>
                <label htmlFor="gate-event">Event</label>
                <select
                  id="gate-event"
                  value={selectedEventId}
                  disabled={validationMutation.isPending}
                  onChange={(event) => changeEvent(event.target.value)}
                >
                  {eventsQuery.data.map((event) => (
                    <option key={event.id} value={event.id}>
                      {event.name} — {event.venue_name}
                    </option>
                  ))}
                </select>
              </div>

              {selectedEvent && (
                <div className="gate-event-context">
                  <strong>{formatEventDate(selectedEvent.start_at)}</strong>
                  <span>
                    {selectedEvent.venue_name} · {selectedEvent.city}, {selectedEvent.country_code}
                  </span>
                </div>
              )}

              <GateCameraScanner
                key={selectedEventId}
                disabled={validationMutation.isPending}
                onScan={scanToken}
              />

              <div>
                <label htmlFor="ticket-code">Ticket code</label>
                <textarea
                  id="ticket-code"
                  value={token}
                  rows={4}
                  autoComplete="off"
                  spellCheck={false}
                  placeholder="v1.ticket-identifier.signature"
                  required
                  disabled={validationMutation.isPending}
                  onChange={(event) => changeToken(event.target.value)}
                />
                <small>
                  Manual entry remains available even when camera access is unavailable.
                </small>
              </div>

              <button
                className="primary-button gate-submit"
                type="submit"
                disabled={!token.trim() || validationMutation.isPending}
              >
                {validationMutation.isPending ? 'Validating...' : 'Validate ticket'}
              </button>

              {validationMutation.isError && (
                <p className="form-error" role="alert">
                  No authoritative result was received. Do not admit yet; retry the same code.
                </p>
              )}
            </form>

            <div className="gate-feedback" aria-label="Latest validation result">
              {validationMutation.data ? (
                <ValidationFeedback result={validationMutation.data} />
              ) : (
                <section className="gate-result gate-result--waiting">
                  <p className="gate-result__eyebrow">Ready</p>
                  <h2>Waiting for a ticket</h2>
                  <p>The latest authoritative result will appear here.</p>
                </section>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../../lib/api-client'
import { SiteHeader } from '../navigation/components/SiteHeader'
import { getPublishedEvent, publishedEventQueryKey } from '../discovery/discovery-api'
import { ReservationCountdown } from './components/ReservationCountdown'
import {
  getReservation,
  type PaymentOutcome,
  processPayment,
  reservationQueryKey,
} from './reservations-api'

export function ReservationHoldPage() {
  const { reservationId = '' } = useParams()
  const queryClient = useQueryClient()
  const reservationQuery = useQuery({
    queryKey: reservationQueryKey(reservationId),
    queryFn: () => getReservation(reservationId),
    enabled: Boolean(reservationId),
    refetchOnWindowFocus: true,
  })
  const eventId = reservationQuery.data?.event_id ?? ''
  const eventQuery = useQuery({
    queryKey: publishedEventQueryKey(eventId),
    queryFn: () => getPublishedEvent(eventId),
    enabled: Boolean(eventId),
  })
  const refetchReservation = reservationQuery.refetch
  const refreshAfterCountdown = useCallback(() => {
    void refetchReservation()
  }, [refetchReservation])
  const paymentMutation = useMutation({
    mutationFn: (outcome: PaymentOutcome) => processPayment(reservationId, outcome),
    onSuccess: (reservation) => {
      queryClient.setQueryData(reservationQueryKey(reservationId), reservation)
      void queryClient.invalidateQueries({ queryKey: ['events', 'published'] })
    },
  })

  if (reservationQuery.isPending) {
    return <main className="centered-page">Restoring your reservation...</main>
  }

  if (reservationQuery.isError) {
    return (
      <main className="centered-page">
        <p className="eyebrow">Reservation unavailable</p>
        <h1>We could not restore this reservation.</h1>
        <Link className="text-link" to="/customer">
          Browse published events
        </Link>
      </main>
    )
  }

  const reservation = reservationQuery.data
  const eventName = eventQuery.data?.name ?? 'your selected event'
  const eventPath = `/customer/events/${reservation.event_id}`

  return (
    <div className="page-shell">
      <SiteHeader authenticated />
      <main className="reservation-page">
        <section className="reservation-panel">
          {reservation.status === 'pending' ? (
            <>
              <p className="eyebrow">Tickets temporarily held</p>
              <h1>{eventName}</h1>
              <p>
                {reservation.quantity} {reservation.quantity === 1 ? 'ticket is' : 'tickets are'}
                {' held while you complete checkout.'}
              </p>
              <div className="reservation-deadline">
                <span>Time remaining</span>
                <ReservationCountdown
                  key={reservation.server_time}
                  expiresAt={reservation.expires_at}
                  serverTime={reservation.server_time}
                  onElapsed={refreshAfterCountdown}
                />
              </div>
              <p className="reservation-note">
                PostgreSQL decides whether this hold is still valid. This countdown is a display of
                the server deadline.
              </p>
              <div className="payment-simulator">
                <strong>Payment simulator</strong>
                <p>No real charge occurs. Choose a deterministic result for this demonstration.</p>
                <div className="payment-simulator__actions">
                  <button
                    className="primary-button"
                    type="button"
                    disabled={paymentMutation.isPending}
                    onClick={() => paymentMutation.mutate('approved')}
                  >
                    {paymentMutation.isPending ? 'Processing...' : 'Simulate approval'}
                  </button>
                  <button
                    className="secondary-button"
                    type="button"
                    disabled={paymentMutation.isPending}
                    onClick={() => paymentMutation.mutate('declined')}
                  >
                    Simulate decline
                  </button>
                </div>
                {paymentMutation.isError && (
                  <p className="form-error" role="alert">
                    {paymentMutation.error instanceof ApiError
                      ? paymentMutation.error.message
                      : 'We could not process this simulation. Please try again.'}
                  </p>
                )}
              </div>
            </>
          ) : reservation.status === 'approved' ? (
            <>
              <p className="eyebrow">Payment approved</p>
              <h1>Your tickets are issued.</h1>
              <p>
                {reservation.ticket_count}{' '}
                {reservation.ticket_count === 1 ? 'ticket was' : 'tickets were'} created for{' '}
                {eventName}.
              </p>
              <p className="reservation-note">
                Open My Tickets to present, share, or scan the issued QR credentials.
              </p>
              <Link className="primary-button" to="/customer/tickets">
                Open my tickets
              </Link>
            </>
          ) : reservation.status === 'declined' ? (
            <>
              <p className="eyebrow">Payment declined</p>
              <h1>The hold was released.</h1>
              <p>
                No charge occurred. Create a new hold to retry because this inventory is available
                again.
              </p>
              <Link className="primary-button" to={eventPath}>
                Try again
              </Link>
            </>
          ) : reservation.status === 'expired' ? (
            <>
              <p className="eyebrow">Reservation expired</p>
              <h1>Your hold expired.</h1>
              <p>The tickets were released so another customer can reserve them.</p>
              <Link className="primary-button" to={eventPath}>
                Choose tickets again
              </Link>
            </>
          ) : (
            <>
              <p className="eyebrow">Reservation {reservation.status}</p>
              <h1>This reservation is {reservation.status}.</h1>
              <Link className="text-link" to={eventPath}>
                View event
              </Link>
            </>
          )}
        </section>
      </main>
    </div>
  )
}

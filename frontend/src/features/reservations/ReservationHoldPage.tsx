import { useQuery } from '@tanstack/react-query'
import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { DiscoveryHeader } from '../discovery/DiscoveryHeader'
import { getPublishedEvent, publishedEventQueryKey } from '../discovery/discovery-api'
import { ReservationCountdown } from './ReservationCountdown'
import { getReservation, reservationQueryKey } from './reservations-api'

export function ReservationHoldPage() {
  const { reservationId = '' } = useParams()
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
      <DiscoveryHeader authenticated />
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
              <p className="reservation-note">Payment simulation will be added next.</p>
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

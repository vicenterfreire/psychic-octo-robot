import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../../lib/api-client'
import { SiteHeader } from '../navigation/components/SiteHeader'
import { ReservationForm } from '../reservations/components/ReservationForm'
import { getPublishedEvent, publishedEventQueryKey } from './discovery-api'
import { availabilityLabel, formatEventDate, formatEventPrice } from '../../lib/event-display'
import reservationStyles from '../reservations/reservations.module.css'
import styles from './discovery.module.css'

interface EventDetailPageProps {
  authenticated?: boolean
}

export function EventDetailPage({ authenticated = false }: EventDetailPageProps) {
  const { eventId = '' } = useParams()
  const eventQuery = useQuery({
    queryKey: publishedEventQueryKey(eventId),
    queryFn: () => getPublishedEvent(eventId),
    enabled: Boolean(eventId),
  })
  const listPath = authenticated ? '/customer' : '/events'

  if (eventQuery.isPending) {
    return <main className="centered-page">Loading event...</main>
  }

  if (eventQuery.isError) {
    const notFound = eventQuery.error instanceof ApiError && eventQuery.error.status === 404
    return (
      <main className="centered-page">
        <p className="eyebrow">{notFound ? 'Event not found' : 'Events unavailable'}</p>
        <h1>{notFound ? 'This event is not available.' : 'We could not load this event.'}</h1>
        <Link className="text-link" to={listPath}>
          Back to published events
        </Link>
      </main>
    )
  }

  const event = eventQuery.data
  return (
    <div className="page-shell">
      <SiteHeader authenticated={authenticated} />
      <main className={styles['event-detail']}>
        <Link className={styles['event-detail__back']} to={listPath}>
          ← All published events
        </Link>
        <div className={styles['event-detail__layout']}>
          <div className={styles['event-detail__image']}>
            {event.image_url ? (
              <img src={event.image_url} alt="" />
            ) : (
              <span aria-hidden="true">G</span>
            )}
          </div>
          <article className={styles['event-detail__content']}>
            <p className="eyebrow">{formatEventDate(event.start_at)}</p>
            <h1>{event.name}</h1>
            <p className={styles['event-detail__description']}>
              {event.description ?? 'No additional event description is available.'}
            </p>

            <dl className={styles['event-facts']}>
              <div>
                <dt>Venue</dt>
                <dd>{event.venue_name}</dd>
              </div>
              <div>
                <dt>Address</dt>
                <dd>
                  {event.address}, {event.city}, {event.country_code}
                </dd>
              </div>
              <div>
                <dt>Price</dt>
                <dd>{formatEventPrice(event.price_minor, event.currency)}</dd>
              </div>
              <div>
                <dt>Availability</dt>
                <dd>{availabilityLabel(event.available_quantity)}</dd>
              </div>
            </dl>

            <div className={reservationStyles['reservation-entry']}>
              {event.available_quantity === 0 ? (
                <p>This event is currently sold out.</p>
              ) : authenticated ? (
                <ReservationForm eventId={event.id} availableQuantity={event.available_quantity} />
              ) : (
                <>
                  <strong>Want to reserve a ticket?</strong>
                  <Link className="primary-button" to="/login">
                    Sign in as a customer
                  </Link>
                </>
              )}
            </div>
          </article>
        </div>
      </main>
    </div>
  )
}

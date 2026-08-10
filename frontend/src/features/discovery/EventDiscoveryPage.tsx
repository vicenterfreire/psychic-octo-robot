import { useQuery } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'
import { DiscoveryHeader } from './DiscoveryHeader'
import { getPublishedEvents, publishedEventsQueryKey, type PublishedEvent } from './discovery-api'
import { availabilityLabel, formatEventDate, formatEventPrice } from './event-display'

interface EventDiscoveryPageProps {
  authenticated?: boolean
}

interface EventCardProps {
  event: PublishedEvent
  detailPath: string
}

function EventCard({ event, detailPath }: EventCardProps) {
  return (
    <article className="discovery-card">
      <div className="discovery-card__image">
        {event.image_url ? <img src={event.image_url} alt="" /> : <span aria-hidden="true">G</span>}
      </div>
      <div className="discovery-card__content">
        <p className="discovery-card__date">{formatEventDate(event.start_at)}</p>
        <h2>{event.name}</h2>
        <p className="discovery-card__location">
          {event.venue_name} · {event.city}, {event.country_code}
        </p>
        <p className="discovery-card__description">
          {event.description ?? 'Event details will be available at the venue.'}
        </p>
        <div className="discovery-card__footer">
          <div>
            <strong>{formatEventPrice(event)}</strong>
            <span className={event.available_quantity === 0 ? 'availability--empty' : ''}>
              {availabilityLabel(event.available_quantity)}
            </span>
          </div>
          <Link className="secondary-button" to={detailPath}>
            View event
          </Link>
        </div>
      </div>
    </article>
  )
}

export function EventDiscoveryPage({ authenticated = false }: EventDiscoveryPageProps) {
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const eventsQuery = useQuery({
    queryKey: publishedEventsQueryKey(searchQuery),
    queryFn: () => getPublishedEvents(searchQuery),
  })
  const detailBasePath = authenticated ? '/customer/events' : '/events'

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSearchQuery(searchInput.trim())
  }

  function clearSearch() {
    setSearchInput('')
    setSearchQuery('')
  }

  const events = eventsQuery.data ?? []

  return (
    <div className="page-shell">
      <DiscoveryHeader authenticated={authenticated} />
      <main className="discovery-workspace">
        <section className="discovery-intro">
          <p className="eyebrow">Published events</p>
          <h1>Find a reason to show up.</h1>
          <p>
            Search by event, venue, or city. Availability already accounts for completed sales and
            active reservation holds.
          </p>
        </section>

        <form className="discovery-search" role="search" onSubmit={submitSearch}>
          <label htmlFor="event-search">Search published events</label>
          <div>
            <input
              id="event-search"
              type="search"
              maxLength={100}
              placeholder="Event, venue, or city"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
            />
            <button className="primary-button" type="submit" disabled={eventsQuery.isFetching}>
              {eventsQuery.isFetching ? 'Searching...' : 'Search'}
            </button>
            {searchQuery && (
              <button className="secondary-button" type="button" onClick={clearSearch}>
                Clear
              </button>
            )}
          </div>
        </form>

        <div className="discovery-feedback" aria-live="polite">
          {eventsQuery.isPending && <p>Loading published events...</p>}
          {eventsQuery.isError && (
            <p className="form-error">Unable to load events. Please try again.</p>
          )}
          {eventsQuery.isSuccess && events.length === 0 && (
            <p>
              {searchQuery
                ? `No published events match “${searchQuery}”. Try a broader term.`
                : 'No upcoming published events are available yet.'}
            </p>
          )}
        </div>

        {events.length > 0 && (
          <section className="discovery-grid" aria-label="Published event results">
            {events.map((event) => (
              <EventCard
                event={event}
                detailPath={`${detailBasePath}/${event.id}`}
                key={event.id}
              />
            ))}
          </section>
        )}
      </main>
    </div>
  )
}

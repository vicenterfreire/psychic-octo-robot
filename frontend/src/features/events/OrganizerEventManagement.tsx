import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { CatalogEvent } from '../catalog/catalog-api'
import { EventDetailsForm } from './EventDetailsForm'
import {
  createEvent,
  eventErrorMessage,
  getOrganizerEvents,
  organizerEventsQueryKey,
  type EventDetailsInput,
  type OrganizerEvent,
  publishEvent,
  updateEvent,
} from './events-api'

interface OrganizerEventCreatorProps {
  selectedEvent: CatalogEvent
  onCreated: () => void
}

export function OrganizerEventCreator({ selectedEvent, onCreated }: OrganizerEventCreatorProps) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: createEvent,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: organizerEventsQueryKey })
      onCreated()
    },
  })

  const initialEvent: OrganizerEvent = {
    id: '',
    organizer_id: '',
    name: selectedEvent.name,
    description: selectedEvent.description,
    venue_name: '',
    address: '',
    city: '',
    country_code: 'BR',
    start_at: '',
    capacity: 100,
    price_minor: 0,
    currency: 'BRL',
    status: 'draft',
    source: selectedEvent,
    created_at: '',
    updated_at: '',
  }

  return (
    <section className="event-editor" aria-labelledby="new-event-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Local event details</p>
          <h2 id="new-event-heading">Create from {selectedEvent.name}</h2>
        </div>
        <p>The Ticketmaster source is copied now; these local details remain yours to manage.</p>
      </div>
      <EventDetailsForm
        key={selectedEvent.provider_event_id}
        initialEvent={initialEvent}
        submitLabel="Create draft"
        isPending={mutation.isPending}
        error={mutation.error}
        onSubmit={(details) =>
          mutation.mutate({ ...details, provider_event_id: selectedEvent.provider_event_id })
        }
      />
    </section>
  )
}

interface OrganizerEventListProps {
  enabled: boolean
}

export function OrganizerEventList({ enabled }: OrganizerEventListProps) {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<string | null>(null)
  const eventsQuery = useQuery({
    queryKey: organizerEventsQueryKey,
    queryFn: getOrganizerEvents,
    enabled,
  })
  const updateMutation = useMutation({
    mutationFn: ({ eventId, details }: { eventId: string; details: EventDetailsInput }) =>
      updateEvent(eventId, details),
    onSuccess: async () => {
      setEditingId(null)
      await queryClient.invalidateQueries({ queryKey: organizerEventsQueryKey })
    },
  })
  const publishMutation = useMutation({
    mutationFn: publishEvent,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: organizerEventsQueryKey })
    },
  })

  const events = eventsQuery.data ?? []

  return (
    <section className="managed-events" aria-labelledby="managed-events-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Your events</p>
          <h2 id="managed-events-heading">Drafts and published events</h2>
        </div>
        <p>Publishing is explicit. A draft is never visible in customer discovery.</p>
      </div>

      {eventsQuery.isPending && enabled && <p>Loading your events...</p>}
      {eventsQuery.isError && <p className="form-error">{eventErrorMessage(eventsQuery.error)}</p>}
      {eventsQuery.isSuccess && events.length === 0 && (
        <p className="empty-panel">No local events yet. Search Ticketmaster to create the first.</p>
      )}

      <div className="managed-event-list">
        {events.map((event) => (
          <article className="managed-event" key={event.id}>
            <div className="managed-event__summary">
              <div>
                <span className={`event-status event-status--${event.status}`}>{event.status}</span>
                <h3>{event.name}</h3>
                <p>
                  {new Intl.DateTimeFormat('en', {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  }).format(new Date(event.start_at))}{' '}
                  · {event.venue_name}, {event.city} · {event.capacity} tickets
                </p>
                <small>Source snapshot: {event.source.name}</small>
              </div>
              <div className="managed-event__actions">
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => setEditingId(event.id)}
                >
                  Edit
                </button>
                {event.status === 'draft' && (
                  <button
                    className="primary-button"
                    type="button"
                    disabled={publishMutation.isPending}
                    onClick={() => publishMutation.mutate(event.id)}
                  >
                    Publish
                  </button>
                )}
              </div>
            </div>
            {publishMutation.isError && publishMutation.variables === event.id && (
              <p className="form-error" role="alert">
                {eventErrorMessage(publishMutation.error)}
              </p>
            )}
            {editingId === event.id && (
              <EventDetailsForm
                initialEvent={event}
                submitLabel="Save changes"
                isPending={updateMutation.isPending}
                error={updateMutation.error}
                onCancel={() => setEditingId(null)}
                onSubmit={(details) => updateMutation.mutate({ eventId: event.id, details })}
              />
            )}
          </article>
        ))}
      </div>
    </section>
  )
}

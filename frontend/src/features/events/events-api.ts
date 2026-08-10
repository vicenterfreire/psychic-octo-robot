import { ApiError, apiRequest } from '../../lib/api-client'

export type EventStatus = 'draft' | 'published'

export interface CatalogSource {
  provider: 'ticketmaster'
  provider_event_id: string
  name: string
  description: string | null
  image_url: string | null
  source_url: string | null
}

export interface OrganizerEvent {
  id: string
  organizer_id: string
  name: string
  description: string | null
  venue_name: string
  address: string
  city: string
  country_code: string
  start_at: string
  capacity: number
  price_minor: number
  currency: string
  status: EventStatus
  source: CatalogSource
  created_at: string
  updated_at: string
}

export interface EventDetailsInput {
  name: string
  description: string | null
  venue_name: string
  address: string
  city: string
  country_code: string
  start_at: string
  capacity: number
  price_minor: number
  currency: string
}

export interface EventCreateInput extends EventDetailsInput {
  provider_event_id: string
}

interface OrganizerEventCollection {
  items: OrganizerEvent[]
}

export const organizerEventsQueryKey = ['events', 'organizer'] as const

export function eventErrorMessage(error: unknown): string | null {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message
  }
  return error ? 'Unable to save the event.' : null
}

export async function getOrganizerEvents(): Promise<OrganizerEvent[]> {
  const response = await apiRequest<OrganizerEventCollection>('/events/organizer')
  return response.items
}

export function createEvent(input: EventCreateInput): Promise<OrganizerEvent> {
  return apiRequest<OrganizerEvent>('/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function updateEvent(eventId: string, input: EventDetailsInput): Promise<OrganizerEvent> {
  return apiRequest<OrganizerEvent>(`/events/${eventId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function publishEvent(eventId: string): Promise<OrganizerEvent> {
  return apiRequest<OrganizerEvent>(`/events/${eventId}/publish`, { method: 'POST' })
}

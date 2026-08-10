import { apiRequest } from '../../lib/api-client'

export interface PublishedEvent {
  id: string
  name: string
  description: string | null
  venue_name: string
  address: string
  city: string
  country_code: string
  start_at: string
  capacity: number
  available_quantity: number
  price_minor: number
  currency: string
  image_url: string | null
}

interface PublishedEventCollection {
  items: PublishedEvent[]
}

export function publishedEventsQueryKey(searchQuery: string) {
  return ['events', 'published', searchQuery] as const
}

export function publishedEventQueryKey(eventId: string) {
  return ['events', 'published', 'detail', eventId] as const
}

export async function getPublishedEvents(searchQuery: string): Promise<PublishedEvent[]> {
  const parameters = new URLSearchParams()
  if (searchQuery) {
    parameters.set('q', searchQuery)
  }
  const query = parameters.size ? `?${parameters.toString()}` : ''
  const response = await apiRequest<PublishedEventCollection>(`/events${query}`)
  return response.items
}

export function getPublishedEvent(eventId: string): Promise<PublishedEvent> {
  return apiRequest<PublishedEvent>(`/events/${eventId}`)
}

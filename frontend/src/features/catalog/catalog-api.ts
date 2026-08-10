import { apiRequest } from '../../lib/api-client'

export interface CatalogEvent {
  provider: 'ticketmaster'
  provider_event_id: string
  name: string
  description: string | null
  image_url: string | null
  source_url: string | null
}

interface CatalogSearchResponse {
  items: CatalogEvent[]
}

export function searchCatalogEvents(query: string): Promise<CatalogSearchResponse> {
  const searchParameters = new URLSearchParams({ q: query })
  return apiRequest<CatalogSearchResponse>(`/catalog/events?${searchParameters.toString()}`)
}

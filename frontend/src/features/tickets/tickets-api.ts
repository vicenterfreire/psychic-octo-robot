import { apiRequest } from '../../lib/api-client'

export interface TicketEvent {
  id: string
  name: string
  venue_name: string
  address: string
  city: string
  country_code: string
  start_at: string
  image_url: string | null
}

export interface CustomerTicket {
  id: string
  ticket_number: number
  issued_at: string
  is_used: boolean
  is_revoked: boolean
  token: string
  share_url: string
  event: TicketEvent
}

export interface SharedTicket {
  ticket_number: number
  issued_at: string
  is_used: boolean
  is_revoked: boolean
  event: TicketEvent
}

interface CustomerTicketCollection {
  items: CustomerTicket[]
}

export const customerTicketsQueryKey = ['tickets', 'customer'] as const

export function sharedTicketQueryKey(token: string) {
  return ['tickets', 'shared', token] as const
}

export async function getCustomerTickets(): Promise<CustomerTicket[]> {
  const response = await apiRequest<CustomerTicketCollection>('/tickets')
  return response.items
}

export function getSharedTicket(token: string): Promise<SharedTicket> {
  return apiRequest<SharedTicket>(`/tickets/shared/${encodeURIComponent(token)}`)
}

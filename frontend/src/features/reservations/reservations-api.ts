import { apiRequest } from '../../lib/api-client'

export type ReservationStatus = 'pending' | 'approved' | 'declined' | 'expired'

export interface Reservation {
  id: string
  event_id: string
  quantity: number
  status: ReservationStatus
  created_at: string
  expires_at: string
  server_time: string
}

export interface ReservationCreate {
  event_id: string
  quantity: number
}

export function reservationQueryKey(reservationId: string) {
  return ['reservations', 'detail', reservationId] as const
}

export function createReservation(command: ReservationCreate): Promise<Reservation> {
  return apiRequest<Reservation>('/reservations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(command),
  })
}

export function getReservation(reservationId: string): Promise<Reservation> {
  return apiRequest<Reservation>(`/reservations/${reservationId}`)
}

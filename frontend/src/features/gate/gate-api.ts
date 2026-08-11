import { apiRequest } from '../../lib/api-client'

export interface GateEvent {
  id: string
  name: string
  venue_name: string
  city: string
  country_code: string
  start_at: string
}

interface GateEventCollection {
  items: GateEvent[]
}

export type GateValidationOutcome = 'valid' | 'invalid' | 'already_used' | 'wrong_event'

export interface GateValidationResult {
  outcome: GateValidationOutcome
  ticket_number: number | null
  used_at: string | null
}

interface GateValidationCommand {
  event_id: string
  token: string
}

export const gateEventsQueryKey = ['gate', 'events'] as const

export async function getGateEvents(): Promise<GateEvent[]> {
  const response = await apiRequest<GateEventCollection>('/gate/events')
  return response.items
}

export function validateGateTicket(command: GateValidationCommand): Promise<GateValidationResult> {
  return apiRequest<GateValidationResult>('/gate/validations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(command),
  })
}

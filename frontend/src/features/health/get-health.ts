import { apiRequest } from '../../lib/api-client'

export interface HealthResponse {
  status: 'ok'
  service: string
}

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>('/health')
}

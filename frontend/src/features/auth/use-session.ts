import { useQuery } from '@tanstack/react-query'
import { getCurrentUser, sessionQueryKey } from './auth-api'

export function useSession() {
  return useQuery({
    queryKey: sessionQueryKey,
    queryFn: getCurrentUser,
    retry: false,
    staleTime: 60_000,
  })
}

import { useQuery } from '@tanstack/react-query'
import { getHealth } from '../get-health'

export function ApiStatus() {
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    retry: false,
  })

  if (healthQuery.isPending) {
    return <p className="status status--pending">Checking API connection...</p>
  }

  if (healthQuery.isError) {
    return <p className="status status--error">API unavailable. Start the FastAPI service.</p>
  }

  return (
    <p className="status status--connected">
      <span aria-hidden="true" /> API connected to {healthQuery.data.service}
    </p>
  )
}

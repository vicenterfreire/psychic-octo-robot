import { useQuery } from '@tanstack/react-query'
import { getHealth } from '../get-health'
import styles from '../health.module.css'

export function ApiStatus() {
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    retry: false,
  })

  if (healthQuery.isPending) {
    return <p className={styles.status}>Checking API connection...</p>
  }

  if (healthQuery.isError) {
    return (
      <p className={`${styles.status} ${styles.error}`}>
        API unavailable. Start the FastAPI service.
      </p>
    )
  }

  return (
    <p className={`${styles.status} ${styles.connected}`}>
      <span aria-hidden="true" /> API connected to {healthQuery.data.service}
    </p>
  )
}

import { useEffect, useState } from 'react'
import { formatReservationCountdown, reservationRemainingMilliseconds } from '../reservation-time'
import styles from '../reservations.module.css'

interface ReservationCountdownProps {
  expiresAt: string
  serverTime: string
  onElapsed: () => void
}

export function ReservationCountdown({
  expiresAt,
  serverTime,
  onElapsed,
}: ReservationCountdownProps) {
  const [clientReceivedAt] = useState(() => Date.now())
  const [clientNow, setClientNow] = useState(clientReceivedAt)
  const remaining = reservationRemainingMilliseconds(
    expiresAt,
    serverTime,
    clientReceivedAt,
    clientNow,
  )

  useEffect(() => {
    if (remaining === 0) {
      onElapsed()
      return
    }
    const interval = window.setInterval(() => setClientNow(Date.now()), 250)
    return () => window.clearInterval(interval)
  }, [onElapsed, remaining])

  return (
    <time className={styles['reservation-countdown']} dateTime={expiresAt}>
      {formatReservationCountdown(remaining)}
    </time>
  )
}

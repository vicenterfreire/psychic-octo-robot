export function reservationRemainingMilliseconds(
  expiresAt: string,
  serverTime: string,
  clientReceivedAt: number,
  clientNow: number,
): number {
  const serverOffset = Date.parse(serverTime) - clientReceivedAt
  const estimatedServerNow = clientNow + serverOffset
  return Math.max(Date.parse(expiresAt) - estimatedServerNow, 0)
}

export function formatReservationCountdown(milliseconds: number): string {
  const totalSeconds = Math.ceil(milliseconds / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

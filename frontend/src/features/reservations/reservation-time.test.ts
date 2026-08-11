import { describe, expect, it } from 'vitest'
import { formatReservationCountdown, reservationRemainingMilliseconds } from './reservation-time'

describe('reservation deadline presentation', () => {
  it('uses the server offset instead of trusting a skewed browser clock', () => {
    const receivedAt = Date.parse('2032-09-21T15:05:00Z')
    const oneClientMinuteLater = Date.parse('2032-09-21T15:06:00Z')

    const remaining = reservationRemainingMilliseconds(
      '2032-09-21T15:10:00Z',
      '2032-09-21T15:00:00Z',
      receivedAt,
      oneClientMinuteLater,
    )

    expect(remaining).toBe(9 * 60 * 1000)
    expect(formatReservationCountdown(remaining)).toBe('09:00')
  })
})

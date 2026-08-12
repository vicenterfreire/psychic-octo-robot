import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../../../lib/api-client'
import { createReservation } from '../reservations-api'
import styles from '../reservations.module.css'

interface ReservationFormProps {
  eventId: string
  availableQuantity: number
}

export function ReservationForm({ eventId, availableQuantity }: ReservationFormProps) {
  const [quantity, setQuantity] = useState(1)
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const reservationMutation = useMutation({
    mutationFn: createReservation,
    onSuccess: (reservation) => {
      void queryClient.invalidateQueries({ queryKey: ['events', 'published'] })
      navigate(`/customer/reservations/${reservation.id}`)
    },
  })
  const validQuantity = quantity >= 1 && quantity <= availableQuantity

  return (
    <form
      className={styles['reservation-form']}
      onSubmit={(event) => {
        event.preventDefault()
        if (validQuantity) {
          reservationMutation.mutate({ event_id: eventId, quantity })
        }
      }}
    >
      <label>
        <span>Quantity</span>
        <input
          aria-label="Ticket quantity"
          type="number"
          min="1"
          max={availableQuantity}
          value={quantity}
          onChange={(event) => setQuantity(event.currentTarget.valueAsNumber)}
        />
      </label>
      <button
        className="primary-button"
        type="submit"
        disabled={!validQuantity || reservationMutation.isPending}
      >
        {reservationMutation.isPending
          ? 'Holding tickets...'
          : `Hold ${quantity} ${quantity === 1 ? 'ticket' : 'tickets'}`}
      </button>
      {reservationMutation.isError && (
        <p className="form-error" role="alert">
          {reservationMutation.error instanceof ApiError
            ? reservationMutation.error.message
            : 'We could not hold these tickets. Please try again.'}
        </p>
      )}
    </form>
  )
}

import { type FormEvent, useId, useState } from 'react'
import { eventErrorMessage, type EventDetailsInput, type OrganizerEvent } from '../events-api'
import styles from '../events.module.css'

interface EventDetailsFormProps {
  initialEvent?: OrganizerEvent
  submitLabel: string
  isPending: boolean
  error: unknown
  onCancel?: () => void
  onSubmit: (input: EventDetailsInput) => void
}

function priceToMinorUnits(value: string): number {
  const normalized = value.trim().replace(',', '.')
  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) {
    throw new Error('Price must use at most two decimal places.')
  }
  const [whole, decimal = ''] = normalized.split('.')
  return Number(whole) * 100 + Number(decimal.padEnd(2, '0'))
}

function localDateTimeValue(value: string): string {
  const date = new Date(value)
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

function readEventDetails(form: HTMLFormElement): EventDetailsInput {
  const data = new FormData(form)
  return {
    name: String(data.get('name')).trim(),
    description: String(data.get('description')).trim() || null,
    venue_name: String(data.get('venue_name')).trim(),
    address: String(data.get('address')).trim(),
    city: String(data.get('city')).trim(),
    country_code: String(data.get('country_code')).trim().toUpperCase(),
    start_at: new Date(String(data.get('start_at'))).toISOString(),
    capacity: Number(data.get('capacity')),
    price_minor: priceToMinorUnits(String(data.get('price'))),
    currency: 'BRL',
  }
}

/**
 * Normalize human-entered price and local date-time values into the event API contract.
 *
 * Browser validation improves feedback; backend validation remains authoritative.
 */
export function EventDetailsForm({
  initialEvent,
  submitLabel,
  isPending,
  error,
  onCancel,
  onSubmit,
}: EventDetailsFormProps) {
  const formId = useId()
  const [localError, setLocalError] = useState<string | null>(null)

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLocalError(null)
    try {
      onSubmit(readEventDetails(event.currentTarget))
    } catch (caughtError) {
      setLocalError(eventErrorMessage(caughtError))
    }
  }

  const externalError = eventErrorMessage(error)

  return (
    <form className={styles['event-form']} onSubmit={submit}>
      <div className={styles['event-form-wide']}>
        <label htmlFor={`${formId}-name`}>Event name</label>
        <input
          id={`${formId}-name`}
          name="name"
          defaultValue={initialEvent?.name}
          minLength={1}
          maxLength={255}
          required
        />
      </div>
      <div className={styles['event-form-wide']}>
        <label htmlFor={`${formId}-description`}>Description</label>
        <textarea
          id={`${formId}-description`}
          name="description"
          defaultValue={initialEvent?.description ?? ''}
          maxLength={5000}
          rows={3}
        />
      </div>
      <div>
        <label htmlFor={`${formId}-venue`}>Venue</label>
        <input
          id={`${formId}-venue`}
          name="venue_name"
          defaultValue={initialEvent?.venue_name}
          maxLength={255}
          required
        />
      </div>
      <div>
        <label htmlFor={`${formId}-address`}>Address</label>
        <input
          id={`${formId}-address`}
          name="address"
          defaultValue={initialEvent?.address}
          maxLength={500}
          required
        />
      </div>
      <div>
        <label htmlFor={`${formId}-city`}>City</label>
        <input
          id={`${formId}-city`}
          name="city"
          defaultValue={initialEvent?.city}
          maxLength={120}
          required
        />
      </div>
      <div>
        <label htmlFor={`${formId}-country`}>Country code</label>
        <input
          id={`${formId}-country`}
          name="country_code"
          defaultValue={initialEvent?.country_code ?? 'BR'}
          minLength={2}
          maxLength={2}
          required
        />
      </div>
      <div>
        <label htmlFor={`${formId}-start`}>Starts at</label>
        <input
          id={`${formId}-start`}
          name="start_at"
          type="datetime-local"
          defaultValue={
            initialEvent?.start_at ? localDateTimeValue(initialEvent.start_at) : undefined
          }
          required
        />
      </div>
      <div>
        <label htmlFor={`${formId}-capacity`}>Total capacity</label>
        <input
          id={`${formId}-capacity`}
          name="capacity"
          type="number"
          min={1}
          max={1_000_000}
          defaultValue={initialEvent?.capacity ?? 100}
          required
        />
      </div>
      <div>
        <label htmlFor={`${formId}-price`}>Price (BRL)</label>
        <input
          id={`${formId}-price`}
          name="price"
          type="text"
          inputMode="decimal"
          defaultValue={initialEvent ? (initialEvent.price_minor / 100).toFixed(2) : ''}
          placeholder="150.00"
          required
        />
      </div>

      <div className={`${styles['event-form-actions']} ${styles['event-form-wide']}`}>
        <button className="primary-button" type="submit" disabled={isPending}>
          {isPending ? 'Saving...' : submitLabel}
        </button>
        {onCancel && (
          <button className="secondary-button" type="button" onClick={onCancel}>
            Cancel
          </button>
        )}
        {(localError || externalError) && (
          <p className="form-error" role="alert">
            {localError ?? externalError}
          </p>
        )}
      </div>
    </form>
  )
}

import type { PublishedEvent } from './discovery-api'

export function formatEventDate(value: string): string {
  return new Intl.DateTimeFormat('en', {
    dateStyle: 'long',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function formatEventPrice(event: PublishedEvent): string {
  return new Intl.NumberFormat('en', {
    style: 'currency',
    currency: event.currency,
  }).format(event.price_minor / 100)
}

export function availabilityLabel(quantity: number): string {
  if (quantity === 0) {
    return 'Sold out'
  }
  return `${quantity} ${quantity === 1 ? 'ticket' : 'tickets'} available`
}

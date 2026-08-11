export function formatEventDate(value: string): string {
  return new Intl.DateTimeFormat('en', {
    dateStyle: 'long',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function formatEventPrice(priceMinor: number, currency: string): string {
  return new Intl.NumberFormat('en', {
    style: 'currency',
    currency,
  }).format(priceMinor / 100)
}

export function availabilityLabel(quantity: number): string {
  if (quantity === 0) {
    return 'Sold out'
  }
  return `${quantity} ${quantity === 1 ? 'ticket' : 'tickets'} available`
}

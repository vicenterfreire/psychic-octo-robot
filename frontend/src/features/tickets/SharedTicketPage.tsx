import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { formatEventDate } from '../../lib/event-display'
import { SiteHeader } from '../navigation/components/SiteHeader'
import { TicketQrCode } from './components/TicketQrCode'
import { getSharedTicket, sharedTicketQueryKey } from './tickets-api'
import styles from './tickets.module.css'

export function SharedTicketPage() {
  const { token = '' } = useParams()
  const ticketQuery = useQuery({
    queryKey: sharedTicketQueryKey(token),
    queryFn: () => getSharedTicket(token),
    enabled: Boolean(token),
    retry: false,
  })

  if (ticketQuery.isPending) {
    return <main className="centered-page">Verifying shared ticket...</main>
  }

  if (ticketQuery.isError) {
    return (
      <main className="centered-page">
        <p className="eyebrow">Ticket unavailable</p>
        <h1>This sharing link is invalid.</h1>
        <Link className="text-link" to="/events">
          Browse published events
        </Link>
      </main>
    )
  }

  const ticket = ticketQuery.data
  return (
    <div className="page-shell">
      <SiteHeader authenticated={false} />
      <main className={styles['shared-ticket-page']}>
        <article className={styles['shared-ticket']}>
          <div>
            <p className="eyebrow">Shared ticket #{ticket.ticket_number}</p>
            <h1>{ticket.event.name}</h1>
            <p>{formatEventDate(ticket.event.start_at)}</p>
            <p>
              {ticket.event.venue_name} · {ticket.event.address}, {ticket.event.city},{' '}
              {ticket.event.country_code}
            </p>
            <span
              className={`${styles['ticket-state']} ${
                ticket.is_used || ticket.is_revoked ? styles['ticket-state--used'] : ''
              }`}
            >
              {ticket.is_revoked
                ? 'Ticket revoked'
                : ticket.is_used
                  ? 'Already used'
                  : 'Ready for entry'}
            </span>
            <p className={styles['ticket-bearer-warning']}>
              This is a bearer ticket. Anyone with this link can present it at the gate.
            </p>
          </div>
          <TicketQrCode token={token} label={`Shared QR for ${ticket.event.name}`} />
        </article>
      </main>
    </div>
  )
}
